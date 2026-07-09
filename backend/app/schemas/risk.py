from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiskMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portfolio_id:            UUID
    snapshot_date:           date | None = None
    portfolio_value:         Decimal | None = None
    cash_balance:            Decimal | None = None
    # Beta
    portfolio_beta:          Decimal | None = None
    # VaR / CVaR
    var_95:                  Decimal | None = None
    cvar_95:                 Decimal | None = None
    var_95_dollar:           Decimal | None = None
    cvar_95_dollar:          Decimal | None = None
    # Return metrics
    annualized_return:       Decimal | None = None
    annualized_volatility:   Decimal | None = None
    win_rate:                Decimal | None = None
    # Ratios
    sharpe_ratio:            Decimal | None = None
    sortino_ratio:           Decimal | None = None
    calmar_ratio:            Decimal | None = None
    max_drawdown:            Decimal | None = None
    # Composite score
    risk_score:              int | None = None
