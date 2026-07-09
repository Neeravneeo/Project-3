from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HedgeStatusResponse(BaseModel):
    """Current hedge engine state."""

    is_active: bool
    trigger_type: str | None
    hedge_instrument: str | None
    hedge_quantity: Decimal | None
    last_triggered_at: datetime | None

class HedgeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    trigger_type: str
    trigger_value: Decimal | None
    trigger_threshold: Decimal | None
    portfolio_beta_before: Decimal | None
    portfolio_beta_after: Decimal | None
    hedge_instrument: str | None
    hedge_quantity: Decimal | None
    hedge_cost: Decimal | None
    estimated_risk_reduction: Decimal | None
    explanation: str | None
    status: str
    created_at: datetime
