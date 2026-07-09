"""
Celery Task: Market data refresh
Fetches latest quotes for all watched symbols → Redis hot cache
"""

import asyncio
import logging

import redis as sync_redis

from workers.celery_app import celery_app
from app.core.config import settings
from app.domains.market_data.services import fetch_latest_quote_yfinance, cache_quote

logger = logging.getLogger(__name__)

# Default watchlist — in production this comes from DB per user
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "SPY", "QQQ", "IWM",
    # Hedge instruments
    "SH", "SDS", "PSQ",
    # VIX proxy
    "VXX",
]


@celery_app.task(name="workers.tasks.data_refresh.refresh_all_quotes", bind=True, max_retries=3)
def refresh_all_quotes(self, symbols: list[str] | None = None):
    """
    Fetch latest quotes for all symbols → Redis.
    Called every 60 seconds by Celery beat.
    """
    symbols = symbols or DEFAULT_WATCHLIST
    r = sync_redis.from_url(settings.redis_url, decode_responses=True)

    success, failed = 0, 0
    for symbol in symbols:
        try:
            quote = fetch_latest_quote_yfinance(symbol)
            if quote:
                import json
                r.setex(f"price:{symbol.upper()}", 60, json.dumps(quote))
                success += 1
            else:
                failed += 1
        except Exception as exc:
            logger.warning("Failed to refresh %s: %s", symbol, exc)
            failed += 1

    logger.info("Quote refresh complete: %d OK, %d failed", success, failed)
    return {"success": success, "failed": failed, "total": len(symbols)}


@celery_app.task(name="workers.tasks.data_refresh.bootstrap_symbol", bind=True)
def bootstrap_symbol_history(self, symbol: str, period: str = "1y"):
    """
    One-time task: load 1 year of daily OHLCV for a symbol into TimescaleDB.
    Triggered when a user adds a symbol to their watchlist.
    """
    import asyncio
    from app.core.database import AsyncSessionLocal
    from app.domains.market_data.services import (
        fetch_yfinance_bars, upsert_ohlcv_bars
    )
    import redis.asyncio as aioredis

    async def _run():
        bars = fetch_yfinance_bars(symbol, period=period, interval="1d")
        async with AsyncSessionLocal() as db:
            count = await upsert_ohlcv_bars(db, symbol, "1d", bars)
        logger.info("Bootstrapped %s: %d bars inserted", symbol, count)
        return count

    return asyncio.run(_run())
