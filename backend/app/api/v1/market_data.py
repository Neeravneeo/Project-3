"""Market Data API endpoints — quotes, OHLCV bars, watchlist, symbol search."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.core.redis_client import price_key, redis_get_json
from app.models import MarketBar
from app.schemas import OHLCVBar, QuoteResponse, TickerSearchResult

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Static symbol directory (Phase 1B — replace with DB/API lookup later) ───
_SYMBOLS: dict[str, dict[str, str]] = {
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ"},
    "MSFT": {"name": "Microsoft Corporation", "exchange": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.", "exchange": "NASDAQ"},
    "AMZN": {"name": "Amazon.com Inc.", "exchange": "NASDAQ"},
    "TSLA": {"name": "Tesla Inc.", "exchange": "NASDAQ"},
    "META": {"name": "Meta Platforms Inc.", "exchange": "NASDAQ"},
    "NVDA": {"name": "NVIDIA Corporation", "exchange": "NASDAQ"},
    "NFLX": {"name": "Netflix Inc.", "exchange": "NASDAQ"},
    "AMD": {"name": "Advanced Micro Devices", "exchange": "NASDAQ"},
    "INTC": {"name": "Intel Corporation", "exchange": "NASDAQ"},
    "SPY": {"name": "SPDR S&P 500 ETF", "exchange": "NYSE"},
    "QQQ": {"name": "Invesco QQQ ETF", "exchange": "NASDAQ"},
    "IWM": {"name": "iShares Russell 2000 ETF", "exchange": "NYSE"},
    "DIA": {"name": "SPDR Dow Jones ETF", "exchange": "NYSE"},
    "GLD": {"name": "SPDR Gold Shares", "exchange": "NYSE"},
    "SLV": {"name": "iShares Silver Trust", "exchange": "NYSE"},
    "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "exchange": "NASDAQ"},
    "SH": {"name": "ProShares Short S&P 500", "exchange": "NYSE"},
    "SDS": {"name": "ProShares UltraShort S&P 500", "exchange": "NYSE"},
    "PSQ": {"name": "ProShares Short QQQ", "exchange": "NASDAQ"},
    "JPM": {"name": "JPMorgan Chase & Co.", "exchange": "NYSE"},
    "BAC": {"name": "Bank of America Corp.", "exchange": "NYSE"},
    "GS": {"name": "Goldman Sachs Group Inc.", "exchange": "NYSE"},
    "V": {"name": "Visa Inc.", "exchange": "NYSE"},
    "MA": {"name": "Mastercard Inc.", "exchange": "NYSE"},
    "JNJ": {"name": "Johnson & Johnson", "exchange": "NYSE"},
    "PFE": {"name": "Pfizer Inc.", "exchange": "NYSE"},
    "XOM": {"name": "Exxon Mobil Corporation", "exchange": "NYSE"},
    "CVX": {"name": "Chevron Corporation", "exchange": "NYSE"},
    "BRK.B": {"name": "Berkshire Hathaway Inc.", "exchange": "NYSE"},
}


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    current_user: CurrentUser,
    request_obj: Annotated[object, Depends(lambda: None)],  # placeholder for request
) -> QuoteResponse:
    """Return the latest price for a symbol from Redis cache."""
    from fastapi import Request

    symbol = symbol.upper()
    if symbol not in _SYMBOLS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown symbol: {symbol}")

    # NOTE: In production routes use `request.app.state.redis` — injected via middleware
    # For now we read from the module-level client (Celery workers keep it warm)
    from app.core.redis_client import get_redis_client
    redis = await get_redis_client()
    data = await redis_get_json(redis, price_key(symbol))

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data cached for {symbol}. Market data worker may not be running.",
        )

    return QuoteResponse(
        symbol=symbol,
        price=Decimal(str(data.get("price", 0))),
        change=Decimal(str(data.get("change", 0))) if "change" in data else None,
        change_pct=Decimal(str(data.get("change_pct", 0))) if "change_pct" in data else None,
        volume=data.get("volume"),
        timestamp=datetime.fromisoformat(data["ts"]) if "ts" in data else None,
    )


@router.get("/bars/{symbol}", response_model=list[OHLCVBar])
async def get_bars(
    symbol: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    timeframe: str = Query(default="1d", pattern="^(1m|5m|15m|1h|1d)$"),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[OHLCVBar]:
    """Return OHLCV bars for a symbol from TimescaleDB."""
    symbol = symbol.upper()
    if symbol not in _SYMBOLS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown symbol: {symbol}")

    result = await db.execute(
        select(MarketBar)
        .where(MarketBar.symbol == symbol, MarketBar.timeframe == timeframe)
        .order_by(desc(MarketBar.time))
        .limit(limit)
    )
    bars = result.scalars().all()

    # Return in chronological order (oldest first)
    return [
        OHLCVBar(
            time=bar.time,
            symbol=bar.symbol,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in reversed(bars)
    ]


@router.get("/watchlist", response_model=list[QuoteResponse])
async def get_watchlist(current_user: CurrentUser) -> list[QuoteResponse]:
    """Return prices for the user's watchlist symbols from Redis cache."""
    # Default watchlist — will be per-user from user_settings.watchlist JSONB in Phase 1B
    watchlist = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "SPY", "QQQ"]

    from app.core.redis_client import get_redis_client
    redis = await get_redis_client()

    quotes: list[QuoteResponse] = []
    for symbol in watchlist:
        data = await redis_get_json(redis, price_key(symbol))
        if data:
            quotes.append(
                QuoteResponse(
                    symbol=symbol,
                    price=Decimal(str(data.get("price", 0))),
                    change=Decimal(str(data.get("change", 0))) if "change" in data else None,
                    change_pct=Decimal(str(data.get("change_pct", 0))) if "change_pct" in data else None,
                    volume=data.get("volume"),
                    timestamp=datetime.fromisoformat(data["ts"]) if "ts" in data else None,
                )
            )
    return quotes


@router.get("/search", response_model=list[TickerSearchResult])
async def search_symbols(
    current_user: CurrentUser,
    q: str = Query(min_length=1, max_length=20),
) -> list[TickerSearchResult]:
    """Search for ticker symbols by name or symbol prefix."""
    q_lower = q.lower()
    results = [
        TickerSearchResult(symbol=sym, name=info["name"], exchange=info["exchange"])
        for sym, info in _SYMBOLS.items()
        if q_lower in sym.lower() or q_lower in info["name"].lower()
    ]
    return results[:10]
