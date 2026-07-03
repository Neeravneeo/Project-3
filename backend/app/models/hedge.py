from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class HedgeEvent(Base):
    __tablename__ = "hedge_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    trigger_value = Column(Numeric(10, 4))
    trigger_threshold = Column(Numeric(10, 4))
    portfolio_beta_before = Column(Numeric(6, 4))
    portfolio_beta_after = Column(Numeric(6, 4))
    hedge_instrument = Column(String(20))
    hedge_quantity = Column(Numeric(18, 6))
    hedge_cost = Column(Numeric(18, 2))
    estimated_risk_reduction = Column(Numeric(5, 4))
    explanation = Column(String)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    status = Column(String(20), nullable=False, server_default='triggered')

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    portfolio = relationship("Portfolio", back_populates="hedge_events")
