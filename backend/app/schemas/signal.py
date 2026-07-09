import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class SignalResponse(BaseModel):
    """DB-persisted signal record (from `signals` table)."""
    model_config = ConfigDict(from_attributes=True)

    id:              uuid.UUID
    strategy_id:     uuid.UUID
    symbol:          str
    direction:       str
    confidence:      Decimal
    technical_score: Decimal | None = None
    sentiment_score: Decimal | None = None
    regime_aligned:  bool | None    = None
    explanation:     str | None     = None
    raw_indicators:  dict[str, Any] | None = None
    time_horizon:    str | None     = None
    is_active:       bool           = True
    created_at:      datetime


class StrategyContribution(BaseModel):
    """Per-strategy breakdown inside an aggregated signal."""
    strategy:        str
    direction:       str
    confidence:      float
    weight:          float
    weighted_vote:   float
    technical_score: float


class AggregatedSignalResponse(BaseModel):
    """Real-time aggregated signal from the strategy engine."""
    symbol:           str
    direction:        str           # 'buy' | 'sell' | 'hold'
    confidence:       float
    agreement_ratio:  float
    net_score:        float
    contributing:     list[StrategyContribution]
    explanation:      str
    timestamp:        str
