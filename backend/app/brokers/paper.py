"""
Paper Broker — simulated order execution for safe testing.

Features:
- Realistic slippage model (0.05% default for market orders)
- Simulated fill at last price ± slippage
- In-memory position and balance tracking
- No real money, no broker API calls
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from app.brokers.base import (
    BaseBroker, OrderRequest, OrderResult,
    OrderSide, OrderStatus, OrderType,
)
from app.core.config import settings


class PaperBroker(BaseBroker):
    """
    Simulated broker for paper trading.
    Uses Redis quote cache for current prices.
    """

    is_paper = True

    # Slippage model: market orders fill at price * (1 ± slippage_pct)
    SLIPPAGE_PCT = 0.0005   # 0.05% — realistic for liquid US equities
    COMMISSION   = 0.0      # commission-free (like Alpaca)

    def __init__(self, redis: aioredis.Redis, initial_capital: float = 100_000.0) -> None:
        self._redis          = redis
        self._cash           = initial_capital
        self._initial_capital = initial_capital
        # positions: {symbol: {"qty": float, "avg_cost": float, "side": str}}
        self._positions: dict[str, dict] = {}
        # orders: {broker_order_id: OrderResult}
        self._orders: dict[str, OrderResult] = {}

    # ── Order Execution ───────────────────────────────────────────────────────

    async def place_order(self, request: OrderRequest) -> OrderResult:
        """Simulate market/limit order fill."""
        order_id = str(uuid.uuid4())

        current_price = await self._get_price(request.symbol)
        if current_price is None:
            return OrderResult(
                broker_order_id=order_id,
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                filled_price=None,
                filled_qty=0.0,
                status=OrderStatus.FAILED,
                is_paper=True,
                error=f"No price available for {request.symbol}",
            )

        # Apply slippage to market orders
        if request.order_type == OrderType.MARKET:
            slippage = self.SLIPPAGE_PCT
            if request.side == OrderSide.BUY:
                fill_price = current_price * (1 + slippage)
            else:
                fill_price = current_price * (1 - slippage)
        else:
            # Limit order: fill at limit price if market is within range
            fill_price = request.limit_price or current_price
            if request.side == OrderSide.BUY and current_price > fill_price:
                return self._pending_result(order_id, request)
            if request.side == OrderSide.SELL and current_price < fill_price:
                return self._pending_result(order_id, request)

        fill_price = round(fill_price, 6)
        total_cost = fill_price * request.quantity

        # ── Validate: enough cash / shares ────────────────────────────────────
        if request.side == OrderSide.BUY:
            if total_cost > self._cash:
                max_qty = int(self._cash / fill_price)
                if max_qty <= 0:
                    return OrderResult(
                        broker_order_id=order_id,
                        symbol=request.symbol,
                        side=request.side,
                        order_type=request.order_type,
                        quantity=request.quantity,
                        filled_price=None,
                        filled_qty=0.0,
                        status=OrderStatus.FAILED,
                        is_paper=True,
                        error=f"Insufficient cash. Have ${self._cash:.2f}, need ${total_cost:.2f}",
                    )
                # Partial fill with available cash
                request = OrderRequest(
                    **{**request.__dict__, "quantity": float(max_qty)}
                )
                total_cost = fill_price * max_qty

        elif request.side == OrderSide.SELL:
            pos = self._positions.get(request.symbol.upper(), {})
            held_qty = pos.get("qty", 0.0)
            if held_qty < request.quantity:
                if held_qty <= 0:
                    return OrderResult(
                        broker_order_id=order_id,
                        symbol=request.symbol,
                        side=request.side,
                        order_type=request.order_type,
                        quantity=request.quantity,
                        filled_price=None,
                        filled_qty=0.0,
                        status=OrderStatus.FAILED,
                        is_paper=True,
                        error=f"No position in {request.symbol}",
                    )
                request = OrderRequest(
                    **{**request.__dict__, "quantity": held_qty}
                )
                total_cost = fill_price * held_qty

        # ── Apply fill ────────────────────────────────────────────────────────
        self._apply_fill(request, fill_price)

        result = OrderResult(
            broker_order_id=order_id,
            symbol=request.symbol.upper(),
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            filled_price=fill_price,
            filled_qty=request.quantity,
            status=OrderStatus.FILLED,
            is_paper=True,
            raw={"fill_price": fill_price, "cash_after": self._cash},
        )
        self._orders[order_id] = result
        return result

    def _apply_fill(self, request: OrderRequest, fill_price: float) -> None:
        """Update internal cash and position state after fill."""
        sym = request.symbol.upper()
        qty = request.quantity

        if request.side == OrderSide.BUY:
            self._cash -= fill_price * qty
            if sym in self._positions:
                pos = self._positions[sym]
                new_qty = pos["qty"] + qty
                pos["avg_cost"] = (pos["avg_cost"] * pos["qty"] + fill_price * qty) / new_qty
                pos["qty"] = new_qty
            else:
                self._positions[sym] = {"qty": qty, "avg_cost": fill_price, "side": "long"}

        elif request.side == OrderSide.SELL:
            self._cash += fill_price * qty
            if sym in self._positions:
                self._positions[sym]["qty"] -= qty
                if self._positions[sym]["qty"] <= 0:
                    del self._positions[sym]

    # ── Queries ───────────────────────────────────────────────────────────────

    async def cancel_order(self, broker_order_id: str) -> bool:
        if broker_order_id in self._orders:
            order = self._orders[broker_order_id]
            if order.status == OrderStatus.PENDING:
                self._orders[broker_order_id] = OrderResult(
                    **{**order.__dict__, "status": OrderStatus.CANCELLED}
                )
                return True
        return False

    async def get_order(self, broker_order_id: str) -> OrderResult | None:
        return self._orders.get(broker_order_id)

    async def get_positions(self) -> list[dict]:
        return [
            {"symbol": sym, **pos}
            for sym, pos in self._positions.items()
        ]

    async def get_account(self) -> dict:
        total_equity = self._cash + sum(
            pos["qty"] * pos["avg_cost"]   # approximate with cost basis
            for pos in self._positions.values()
        )
        return {
            "cash":            round(self._cash, 2),
            "equity":          round(total_equity, 2),
            "initial_capital": self._initial_capital,
            "total_pnl":       round(total_equity - self._initial_capital, 2),
            "total_pnl_pct":   round((total_equity - self._initial_capital) / self._initial_capital * 100, 3),
            "broker":          "paper",
        }

    async def is_market_open(self) -> bool:
        """Paper trading is always 'open'."""
        return True

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_price(self, symbol: str) -> float | None:
        """Get latest price from Redis cache."""
        import json
        raw = await self._redis.get(f"price:{symbol.upper()}")
        if raw:
            data = json.loads(raw)
            return float(data["price"])
        return None

    def _pending_result(self, order_id: str, request: OrderRequest) -> OrderResult:
        result = OrderResult(
            broker_order_id=order_id,
            symbol=request.symbol.upper(),
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            filled_price=None,
            filled_qty=0.0,
            status=OrderStatus.PENDING,
            is_paper=True,
        )
        self._orders[order_id] = result
        return result
