from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, server_default='NASDAQ')
    side = Column(String(10), nullable=False, server_default='long')
    quantity = Column(Numeric(18, 6), nullable=False)
    avg_cost = Column(Numeric(18, 6), nullable=False)
    current_price = Column(Numeric(18, 6))
    unrealized_pnl = Column(Numeric(18, 2))
    realized_pnl = Column(Numeric(18, 2), nullable=False, server_default=text('0'))
    strategy = Column(String(100))
    is_hedge = Column(Boolean, nullable=False, server_default=text('false'))

    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    portfolio = relationship("Portfolio", back_populates="positions")
