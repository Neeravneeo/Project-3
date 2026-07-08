from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
