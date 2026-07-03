from sqlalchemy import Column, String, Boolean, DateTime, text, ForeignKey, Numeric, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint
from app.core.database import Base

class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    portfolio_value = Column(Numeric(18, 2))
    cash_balance = Column(Numeric(18, 2))
    portfolio_beta = Column(Numeric(6, 4))
    var_95 = Column(Numeric(18, 2))
    cvar_95 = Column(Numeric(18, 2))
    max_drawdown = Column(Numeric(6, 4))
    sharpe_ratio = Column(Numeric(6, 4))
    sortino_ratio = Column(Numeric(6, 4))
    calmar_ratio = Column(Numeric(6, 4))
    risk_score = Column(Integer)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint('portfolio_id', 'snapshot_date', name='uq_portfolio_snapshot_date'),)

    portfolio = relationship("Portfolio", back_populates="risk_snapshots")
