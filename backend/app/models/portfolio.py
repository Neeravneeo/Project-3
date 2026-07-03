from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, server_default='My Portfolio')
    broker = Column(String(50), nullable=False, server_default='paper')
    currency = Column(String(10), nullable=False, server_default='USD')
    initial_capital = Column(Numeric(18, 2), nullable=False, server_default=text('100000.00'))
    cash_balance = Column(Numeric(18, 2), nullable=False, server_default=text('100000.00'))
    is_active = Column(Boolean, nullable=False, server_default=text('true'))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="portfolio", cascade="all, delete-orphan")
    risk_snapshots = relationship("RiskSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    hedge_events = relationship("HedgeEvent", back_populates="portfolio", cascade="all, delete-orphan")
