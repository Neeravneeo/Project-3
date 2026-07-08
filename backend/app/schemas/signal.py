import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    strategy_id: uuid.UUID
    symbol: str
    direction: str
    confidence: Decimal
    technical_score: Decimal | None
    sentiment_score: Decimal | None
    regime_aligned: bool | None
    explanation: str | None
    raw_indicators: dict[str, Any] | None
    time_horizon: str | None
    is_active: bool
    created_at: datetime
