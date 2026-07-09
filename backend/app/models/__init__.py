"""SQLAlchemy ORM models — all 12 tables from the schema doc."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, TIMESTAMPTZ
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ─── Shared column helpers ────────────────────────────────────────────────────

def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )


def _now() -> Mapped[datetime]:
    return mapped_column(TIMESTAMPTZ, nullable=False, server_default=text("NOW()"))


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    """Authenticated user account."""

    __tablename__ = "users"

    id: Mapped[UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'trader'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    # Relationships
    settings: Mapped[UserSettings] = relationship("UserSettings", back_populates="user", uselist=False)
    portfolios: Mapped[list[Portfolio]] = relationship("Portfolio", back_populates="user")
    strategies: Mapped[list[Strategy]] = relationship("Strategy", back_populates="user")
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="user")
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user")


class UserSettings(Base):
    """Per-user risk thresholds and preferences."""

    __tablename__ = "user_settings"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # Broker
    alpaca_api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    alpaca_secret_key_encrypted: Mapped[str | None] = mapped_column(Text)
    alpaca_paper_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    # Risk thresholds
    max_drawdown_trigger: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, server_default=text("0.05"))
    max_position_beta: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default=text("0.90"))
    single_position_loss: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, server_default=text("0.03"))
    vix_caution_level: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("20.0"))
    vix_hedge_level: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("25.0"))
    vix_aggressive_level: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("30.0"))
    max_position_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, server_default=text("0.10"))
    # Notifications
    notify_trade_executed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    notify_hedge_activated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    notify_risk_threshold: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    notify_strategy_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    user: Mapped[User] = relationship("User", back_populates="settings")


# ─── Portfolio ────────────────────────────────────────────────────────────────

class Portfolio(Base):
    """Top-level portfolio container per user."""

    __tablename__ = "portfolios"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("'My Portfolio'"))
    broker: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'paper'"))
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'USD'"))
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text("100000.00"))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text("100000.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    user: Mapped[User] = relationship("User", back_populates="portfolios")
    positions: Mapped[list[Position]] = relationship("Position", back_populates="portfolio")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="portfolio")
    risk_snapshots: Mapped[list[RiskSnapshot]] = relationship("RiskSnapshot", back_populates="portfolio")
    hedge_events: Mapped[list[HedgeEvent]] = relationship("HedgeEvent", back_populates="portfolio")


# ─── Position ─────────────────────────────────────────────────────────────────

class Position(Base):
    """Currently open positions in a portfolio."""

    __tablename__ = "positions"

    id: Mapped[UUID] = _uuid_pk()
    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'NASDAQ'"))
    side: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'long'"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text("0"))
    strategy: Mapped[str | None] = mapped_column(String(100))
    is_hedge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    opened_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    portfolio: Mapped[Portfolio] = relationship("Portfolio", back_populates="positions")


# ─── Order ────────────────────────────────────────────────────────────────────

class Order(Base):
    """Full order history (paper + live)."""

    __tablename__ = "orders"

    id: Mapped[UUID] = _uuid_pk()
    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_order_id: Mapped[str | None] = mapped_column(String(255))
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'market'"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    filled_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    filled_qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"), index=True)
    strategy: Mapped[str | None] = mapped_column(String(100))
    signal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True
    )
    is_paper: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    is_hedge: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    portfolio: Mapped[Portfolio] = relationship("Portfolio", back_populates="orders")
    signal: Mapped[Signal | None] = relationship("Signal")


# ─── Strategy ────────────────────────────────────────────────────────────────

class Strategy(Base):
    """Strategy definitions and per-user configuration."""

    __tablename__ = "strategies"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    risk_per_trade: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    total_signals: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    avg_return: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    user: Mapped[User] = relationship("User", back_populates="strategies")
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="strategy")


# ─── Signal ───────────────────────────────────────────────────────────────────

class Signal(Base):
    """Generated trading signals from each strategy."""

    __tablename__ = "signals"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    technical_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    regime_aligned: Mapped[bool | None] = mapped_column(Boolean)
    explanation: Mapped[str | None] = mapped_column(Text)
    raw_indicators: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    time_horizon: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = _now()

    user: Mapped[User] = relationship("User", back_populates="signals")
    strategy: Mapped[Strategy] = relationship("Strategy", back_populates="signals")


# ─── Market Bars (hypertable — no ORM PK trick needed) ───────────────────────

class MarketBar(Base):
    """OHLCV price bar — maps to the TimescaleDB hypertable."""

    __tablename__ = "market_bars"

    # Hypertable primary key is (time, symbol) — no uuid
    time: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, primary_key=True)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'NASDAQ'"))
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'1d'"), primary_key=True)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    vwap: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    num_trades: Mapped[int | None] = mapped_column(Integer)


# ─── Risk Snapshot ────────────────────────────────────────────────────────────

class RiskSnapshot(Base):
    """Daily snapshot of portfolio risk metrics."""

    __tablename__ = "risk_snapshots"

    id: Mapped[UUID] = _uuid_pk()
    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    portfolio_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cash_balance: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    portfolio_beta: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    var_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cvar_95: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    sortino_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    calmar_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _now()

    portfolio: Mapped[Portfolio] = relationship("Portfolio", back_populates="risk_snapshots")


# ─── Hedge Event ──────────────────────────────────────────────────────────────

class HedgeEvent(Base):
    """Log of every hedge trigger and action."""

    __tablename__ = "hedge_events"

    id: Mapped[UUID] = _uuid_pk()
    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    trigger_threshold: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    portfolio_beta_before: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    portfolio_beta_after: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    hedge_instrument: Mapped[str | None] = mapped_column(String(20))
    hedge_quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    hedge_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    estimated_risk_reduction: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    explanation: Mapped[str | None] = mapped_column(Text)
    order_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'triggered'"))
    created_at: Mapped[datetime] = _now()

    portfolio: Mapped[Portfolio] = relationship("Portfolio", back_populates="hedge_events")


# ─── News Item ────────────────────────────────────────────────────────────────

class NewsItem(Base):
    """Cached news headlines with FinBERT sentiment scores."""

    __tablename__ = "news_items"

    id: Mapped[UUID] = _uuid_pk()
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text)
    symbols: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    sentiment_label: Mapped[str | None] = mapped_column(String(20))
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[datetime] = _now()


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """Immutable log of all significant system actions."""

    __tablename__ = "audit_log"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = _now()

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")
