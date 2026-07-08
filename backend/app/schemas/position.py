from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    symbol: str
    exchange: str
    side: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal
    strategy: str | None
    is_hedge: bool
    opened_at: datetime
