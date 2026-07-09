"""
Abstract BaseBroker — all broker implementations inherit from this.

Execution rule (CRITICAL):
  Order execution MUST stay in the asyncio event loop.
  NEVER route live order placement through Celery workers.
  The serialization overhead adds 10ms–1s of latency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    BUY  = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET     = "market"
    LIMIT      = "limit"
    STOP       = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING   = "pending"
    FILLED    = "filled"
    PARTIAL   = "partial"
    CANCELLED = "cancelled"
    FAILED    = "failed"


@dataclass
class OrderRequest:
    symbol:      str
    side:        OrderSide
    quantity:    float
    order_type:  OrderType  = OrderType.MARKET
    limit_price: float | None = None
    stop_price:  float | None = None
    strategy:    str | None   = None
    signal_id:   str | None   = None
    is_hedge:    bool          = False
    reason:      str           = ""


@dataclass
class OrderResult:
    broker_order_id: str
    symbol:          str
    side:            OrderSide
    order_type:      OrderType
    quantity:        float
    filled_price:    float | None
    filled_qty:      float
    status:          OrderStatus
    is_paper:        bool
    timestamp:       datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error:           str | None = None
    raw:             dict[str, Any] = field(default_factory=dict)

    @property
    def total_value(self) -> float:
        if self.filled_price and self.filled_qty:
            return self.filled_price * self.filled_qty
        return 0.0

    @property
    def is_success(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.PARTIAL)


class BaseBroker(ABC):
    """Abstract broker interface. Implement for paper, Alpaca, Zerodha etc."""

    is_paper: bool = True

    @abstractmethod
    async def place_order(self, request: OrderRequest) -> OrderResult:
        """Place an order. Returns result immediately (market) or when filled."""
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel a pending order. Returns True if cancelled successfully."""
        ...

    @abstractmethod
    async def get_order(self, broker_order_id: str) -> OrderResult | None:
        """Fetch current order status from broker."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[dict]:
        """Return all open positions from broker account."""
        ...

    @abstractmethod
    async def get_account(self) -> dict:
        """Return account balance, buying power, equity."""
        ...

    @abstractmethod
    async def is_market_open(self) -> bool:
        """Check if market is currently open for trading."""
        ...
