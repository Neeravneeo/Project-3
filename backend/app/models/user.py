from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, server_default='trader')
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    is_verified = Column(Boolean, nullable=False, server_default=text('false'))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    alpaca_api_key_encrypted = Column(String)
    alpaca_secret_key_encrypted = Column(String)
    alpaca_paper_mode = Column(Boolean, nullable=False, server_default=text('true'))

    max_drawdown_trigger = Column(Numeric(5, 4), nullable=False, server_default=text('0.05'))
    max_position_beta = Column(Numeric(4, 2), nullable=False, server_default=text('0.90'))
    single_position_loss = Column(Numeric(5, 4), nullable=False, server_default=text('0.03'))
    vix_caution_level = Column(Numeric(5, 2), nullable=False, server_default=text('20.0'))
    vix_hedge_level = Column(Numeric(5, 2), nullable=False, server_default=text('25.0'))
    vix_aggressive_level = Column(Numeric(5, 2), nullable=False, server_default=text('30.0'))
    max_position_weight = Column(Numeric(5, 4), nullable=False, server_default=text('0.10'))

    notify_trade_executed = Column(Boolean, nullable=False, server_default=text('true'))
    notify_hedge_activated = Column(Boolean, nullable=False, server_default=text('true'))
    notify_risk_threshold = Column(Boolean, nullable=False, server_default=text('true'))
    notify_strategy_disabled = Column(Boolean, nullable=False, server_default=text('true'))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="settings")
