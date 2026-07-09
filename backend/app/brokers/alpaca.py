"""
Alpaca Broker — live & paper trading via alpaca-py (official 2025 SDK).

CRITICAL NOTES:
  1. Use alpaca-py NOT the deprecated alpaca-trade-api-python
  2. Order execution runs in asyncio event loop — NEVER via Celery
  3. Implement manual exponential-backoff WebSocket reconnection
  4. Paper mode: ALPACA_PAPER=true in .env (uses sandbox endpoints)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
)
from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

from app.brokers.base import (
    BaseBroker, OrderRequest, OrderResult,
    OrderSide, OrderStatus, OrderType,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlpacaBroker(BaseBroker):
    """
    Live + paper trading via Alpaca Markets.
    Defaults to paper trading (ALPACA_PAPER=true).
    """

    def __init__(self) -> None:
        self.is_paper = settings.alpaca_paper
        self._client = TradingClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.alpaca_paper,
        )
        self._data_client = StockHistoricalDataClient(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
        )

    # ── Order Execution (stays in asyncio loop — no Celery) ───────────────────

    async def place_order(self, request: OrderRequest) -> OrderResult:
        """Place order via Alpaca REST API."""
        try:
            alpaca_side = (
                AlpacaSide.BUY if request.side == OrderSide.BUY else AlpacaSide.SELL
            )

            # Build order request based on type
            if request.order_type == OrderType.MARKET:
                order_data = MarketOrderRequest(
                    symbol=request.symbol.upper(),
                    qty=request.quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                )
            elif request.order_type == OrderType.LIMIT and request.limit_price:
                order_data = LimitOrderRequest(
                    symbol=request.symbol.upper(),
                    qty=request.quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=request.limit_price,
                )
            else:
                order_data = MarketOrderRequest(
                    symbol=request.symbol.upper(),
                    qty=request.quantity,
                    side=alpaca_side,
                    time_in_force=TimeInForce.DAY,
                )

            # Execute in thread to avoid blocking asyncio event loop
            alpaca_order = await asyncio.to_thread(
                self._client.submit_order, order_data
            )

            filled_price = (
                float(alpaca_order.filled_avg_price)
                if alpaca_order.filled_avg_price else None
            )
            filled_qty = float(alpaca_order.filled_qty or 0)

            status_map = {
                "filled":            OrderStatus.FILLED,
                "partially_filled":  OrderStatus.PARTIAL,
                "pending_new":       OrderStatus.PENDING,
                "new":               OrderStatus.PENDING,
                "canceled":          OrderStatus.CANCELLED,
                "rejected":          OrderStatus.FAILED,
                "expired":           OrderStatus.CANCELLED,
            }
            status = status_map.get(str(alpaca_order.status), OrderStatus.PENDING)

            return OrderResult(
                broker_order_id=str(alpaca_order.id),
                symbol=request.symbol.upper(),
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                filled_price=filled_price,
                filled_qty=filled_qty,
                status=status,
                is_paper=self.is_paper,
                raw={"alpaca_status": str(alpaca_order.status)},
            )

        except Exception as exc:
            logger.error("Alpaca order failed: %s | request=%s", exc, request)
            return OrderResult(
                broker_order_id="",
                symbol=request.symbol.upper(),
                side=request.side,
                order_type=request.order_type,
                quantity=request.quantity,
                filled_price=None,
                filled_qty=0.0,
                status=OrderStatus.FAILED,
                is_paper=self.is_paper,
                error=str(exc),
            )

    async def cancel_order(self, broker_order_id: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.cancel_order_by_id, broker_order_id
            )
            return True
        except Exception as exc:
            logger.warning("Cancel order %s failed: %s", broker_order_id, exc)
            return False

    async def get_order(self, broker_order_id: str) -> OrderResult | None:
        try:
            alpaca_order = await asyncio.to_thread(
                self._client.get_order_by_id, broker_order_id
            )
            filled_price = (
                float(alpaca_order.filled_avg_price)
                if alpaca_order.filled_avg_price else None
            )
            return OrderResult(
                broker_order_id=str(alpaca_order.id),
                symbol=str(alpaca_order.symbol),
                side=OrderSide.BUY if str(alpaca_order.side) == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=float(alpaca_order.qty or 0),
                filled_price=filled_price,
                filled_qty=float(alpaca_order.filled_qty or 0),
                status=OrderStatus.FILLED if str(alpaca_order.status) == "filled" else OrderStatus.PENDING,
                is_paper=self.is_paper,
            )
        except Exception:
            return None

    async def get_positions(self) -> list[dict]:
        try:
            positions = await asyncio.to_thread(self._client.get_all_positions)
            return [
                {
                    "symbol":       p.symbol,
                    "qty":          float(p.qty),
                    "avg_cost":     float(p.avg_entry_price),
                    "current_price": float(p.current_price or 0),
                    "unrealized_pnl": float(p.unrealized_pl or 0),
                    "side":         str(p.side),
                }
                for p in positions
            ]
        except Exception as exc:
            logger.error("get_positions failed: %s", exc)
            return []

    async def get_account(self) -> dict:
        try:
            acct = await asyncio.to_thread(self._client.get_account)
            return {
                "cash":         float(acct.cash),
                "equity":       float(acct.equity),
                "buying_power": float(acct.buying_power),
                "portfolio_value": float(acct.portfolio_value),
                "broker":       "alpaca",
                "paper":        self.is_paper,
            }
        except Exception as exc:
            logger.error("get_account failed: %s", exc)
            return {}

    async def is_market_open(self) -> bool:
        try:
            clock = await asyncio.to_thread(self._client.get_clock)
            return bool(clock.is_open)
        except Exception:
            return False

    async def get_latest_quote(self, symbol: str) -> dict | None:
        """Fetch real-time quote from Alpaca data feed (IEX)."""
        try:
            req    = StockLatestQuoteRequest(symbol_or_symbols=symbol.upper())
            result = await asyncio.to_thread(self._data_client.get_stock_latest_quote, req)
            quote  = result[symbol.upper()]
            mid    = (float(quote.ask_price) + float(quote.bid_price)) / 2
            return {
                "symbol":    symbol.upper(),
                "price":     round(mid, 4),
                "bid":       float(quote.bid_price),
                "ask":       float(quote.ask_price),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source":    "alpaca",
            }
        except Exception as exc:
            logger.warning("get_latest_quote(%s) failed: %s", symbol, exc)
            return None
