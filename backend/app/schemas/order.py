from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    side: str = Field(pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit|stop|stop_limit)$")
    quantity: Decimal = Field(gt=0)
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    strategy: str | None = None
    signal_id: UUID | None = None
    reason: str | None = None

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    portfolio_id: UUID
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    limit_price: Decimal | None
    stop_price: Decimal | None
    filled_price: Decimal | None
    filled_qty: Decimal | None
    status: str
    strategy: str | None
    signal_id: UUID | None
    is_paper: bool
    is_hedge: bool
    reason: str | None
    created_at: datetime
    updated_at: datetime
