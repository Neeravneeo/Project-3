from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_order_id = Column(String(255))
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False, server_default='market')
    quantity = Column(Numeric(18, 6), nullable=False)
    limit_price = Column(Numeric(18, 6))
    stop_price = Column(Numeric(18, 6))
    filled_price = Column(Numeric(18, 6))
    filled_qty = Column(Numeric(18, 6))
    status = Column(String(20), nullable=False, server_default='pending', index=True)
    strategy = Column(String(100))
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"))
    is_paper = Column(Boolean, nullable=False, server_default=text('true'))
    is_hedge = Column(Boolean, nullable=False, server_default=text('false'))
    reason = Column(String)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    portfolio = relationship("Portfolio", back_populates="orders")
