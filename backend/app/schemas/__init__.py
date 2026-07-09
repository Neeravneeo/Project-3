"""Pydantic v2 schemas — request/response models for all API endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ─── Common ───────────────────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list wrapper."""

    items: list[T]
    total: int
    page: int
    limit: int
    has_next: bool


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    code: str | None = None


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# ─── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


# ─── Portfolio ────────────────────────────────────────────────────────────────

class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    broker: str
    currency: str
    initial_capital: Decimal
    cash_balance: Decimal
    is_active: bool
    created_at: datetime


class PortfolioSummary(BaseModel):
    """Enriched portfolio summary including computed fields."""

    id: UUID
    name: str
    currency: str
    total_value: Decimal
    cash_balance: Decimal
    daily_pnl: Decimal
    total_pnl: Decimal
    num_positions: int


# ─── Position ─────────────────────────────────────────────────────────────────

class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    symbol: str
    exchange: str
    side: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal
    strategy: str | None
    is_hedge: bool
    opened_at: datetime


# ─── Order ────────────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: str = Field(pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit|stop|stop_limit)$")
    quantity: Decimal = Field(gt=0)
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    strategy: str | None = None
    signal_id: UUID | None = None
    reason: str | None = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    limit_price: Decimal | None
    stop_price: Decimal | None
    filled_price: Decimal | None
    filled_qty: Decimal | None
    status: str
    strategy: str | None
    signal_id: UUID | None
    is_paper: bool
    is_hedge: bool
    reason: str | None
    created_at: datetime
    updated_at: datetime


# ─── Strategy ────────────────────────────────────────────────────────────────

class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_enabled: bool
    parameters: dict[str, Any]
    risk_per_trade: Decimal | None
    win_rate: Decimal | None
    total_signals: int
    avg_return: Decimal | None
    updated_at: datetime


class StrategyUpdate(BaseModel):
    is_enabled: bool | None = None
    parameters: dict[str, Any] | None = None
    risk_per_trade: Decimal | None = None


# ─── Signal ───────────────────────────────────────────────────────────────────

class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    strategy_id: UUID
    symbol: str
    direction: str
    confidence: Decimal
    technical_score: Decimal | None
    sentiment_score: Decimal | None
    regime_aligned: bool | None
    explanation: str | None
    raw_indicators: dict[str, Any] | None
    time_horizon: str | None
    is_active: bool
    created_at: datetime


# ─── Risk ─────────────────────────────────────────────────────────────────────

class RiskMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portfolio_id: UUID
    snapshot_date: date
    portfolio_value: Decimal | None
    cash_balance: Decimal | None
    portfolio_beta: Decimal | None
    var_95: Decimal | None
    cvar_95: Decimal | None
    max_drawdown: Decimal | None
    sharpe_ratio: Decimal | None
    sortino_ratio: Decimal | None
    calmar_ratio: Decimal | None
    risk_score: int | None


# ─── Hedge ────────────────────────────────────────────────────────────────────

class HedgeStatusResponse(BaseModel):
    """Current hedge engine state."""

    is_active: bool
    trigger_type: str | None
    hedge_instrument: str | None
    hedge_quantity: Decimal | None
    last_triggered_at: datetime | None


class HedgeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    trigger_type: str
    trigger_value: Decimal | None
    trigger_threshold: Decimal | None
    portfolio_beta_before: Decimal | None
    portfolio_beta_after: Decimal | None
    hedge_instrument: str | None
    hedge_quantity: Decimal | None
    hedge_cost: Decimal | None
    estimated_risk_reduction: Decimal | None
    explanation: str | None
    status: str
    created_at: datetime


# ─── Market Data ─────────────────────────────────────────────────────────────

class QuoteResponse(BaseModel):
    """Latest price snapshot for a symbol."""

    symbol: str
    price: Decimal
    change: Decimal | None = None
    change_pct: Decimal | None = None
    volume: int | None = None
    timestamp: datetime | None = None


class OHLCVBar(BaseModel):
    """Single OHLCV bar."""

    time: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str
