from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class HedgeStatusResponse(BaseModel):
    is_active: bool
    current_beta: float
    target_beta: float
    active_instrument: Optional[str] = None
    active_quantity: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class HedgeEventResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    trigger_type: str
    trigger_value: Optional[float] = None
    trigger_threshold: Optional[float] = None
    portfolio_beta_before: Optional[float] = None
    portfolio_beta_after: Optional[float] = None
    hedge_instrument: Optional[str] = None
    hedge_quantity: Optional[float] = None
    hedge_cost: Optional[float] = None
    estimated_risk_reduction: Optional[float] = None
    explanation: Optional[str] = None
    order_id: Optional[UUID] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
