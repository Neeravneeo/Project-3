from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False, index=True)
    confidence = Column(Numeric(5, 4), nullable=False)
    technical_score = Column(Numeric(5, 4))
    sentiment_score = Column(Numeric(5, 4))
    regime_aligned = Column(Boolean)
    explanation = Column(String)
    raw_indicators = Column(JSONB)
    time_horizon = Column(String(50))
    is_active = Column(Boolean, nullable=False, server_default=text('true'))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    strategy = relationship("Strategy", back_populates="signals")
