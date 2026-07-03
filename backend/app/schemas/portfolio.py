from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PortfolioResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    broker: str
    currency: str
    initial_capital: float
    cash_balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PortfolioSummary(BaseModel):
    id: UUID
    name: str
    total_value: float
    cash_balance: float
    daily_pnl: float
    daily_pnl_percent: float

    model_config = ConfigDict(from_attributes=True)
