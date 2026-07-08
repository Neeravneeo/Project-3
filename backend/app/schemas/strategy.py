from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_enabled: bool
    parameters: dict[str, Any]
    risk_per_trade: Decimal | None
    win_rate: Decimal | None
    total_signals: int
    avg_return: Decimal | None
    updated_at: datetime

class StrategyUpdate(BaseModel):
    is_enabled: bool | None = None
    parameters: dict[str, Any] | None = None
    risk_per_trade: Decimal | None = None
