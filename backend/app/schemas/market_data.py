from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    """Latest price snapshot for a symbol."""

    symbol: str
    price: Decimal
    change: Decimal | None = None
    change_pct: Decimal | None = None
    volume: int | None = None
    timestamp: datetime | None = None

class OHLCVBar(BaseModel):
    """Single OHLCV bar."""

    time: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str
