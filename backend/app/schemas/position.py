from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PositionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    symbol: str
    exchange: str
    side: str
    quantity: float
    avg_cost: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: float
    strategy: Optional[str] = None
    is_hedge: bool
    opened_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
