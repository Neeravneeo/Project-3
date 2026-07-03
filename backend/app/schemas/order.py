from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class OrderCreate(BaseModel):
    symbol: str
    side: str
    quantity: float
    order_type: str = "market"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    is_paper: bool = True

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    broker_order_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_price: Optional[float] = None
    filled_qty: Optional[float] = None
    status: str
    strategy: Optional[str] = None
    signal_id: Optional[UUID] = None
    is_paper: bool
    is_hedge: bool
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
