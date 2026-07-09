from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    broker: str
    currency: str
    initial_capital: Decimal
    cash_balance: Decimal
    is_active: bool
    created_at: datetime

class PortfolioSummary(BaseModel):
    """Enriched portfolio summary including computed fields."""

    id: UUID
    name: str
    currency: str
    total_value: Decimal
    cash_balance: Decimal
    daily_pnl: Decimal
    total_pnl: Decimal
    num_positions: int
