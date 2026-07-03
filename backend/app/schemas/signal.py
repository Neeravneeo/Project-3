from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional

class SignalResponse(BaseModel):
    id: UUID
    user_id: UUID
    strategy_id: UUID
    symbol: str
    direction: str
    confidence: float
    technical_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    regime_aligned: Optional[bool] = None
    explanation: Optional[str] = None
    raw_indicators: Optional[Dict[str, Any]] = None
    time_horizon: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
