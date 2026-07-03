from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Optional

class RiskMetricsResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    snapshot_date: date
    portfolio_value: Optional[float] = None
    cash_balance: Optional[float] = None
    portfolio_beta: Optional[float] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    risk_score: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
