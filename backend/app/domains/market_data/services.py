"""
Market Data Service — Hot/Cold Path Architecture

Hot path  → Redis  (latest tick, < 5ms read)
Cold path → TimescaleDB (historical OHLCV bars)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import redis.asyncio as aioredis
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.core.config import settings


# ─── Hot Path: Redis Cache ────────────────────────────────────────────────────

async def cache_quote(redis: aioredis.Redis, symbol: str, data: dict) -> None:
    """Write latest quote to Redis hot cache (TTL: 60s)."""
    await redis.setex(f"price:{symbol.upper()}", 60, json.dumps(data))


async def get_cached_quote(redis: aioredis.Redis, symbol: str) -> dict | None:
    """Read latest quote from Redis hot cache."""
    raw = await redis.get(f"price:{symbol.upper()}")
    return json.loads(raw) if raw else None


async def get_cached_quotes(redis: aioredis.Redis, symbols: list[str]) -> dict[str, dict]:
    """Read multiple quotes from Redis in a single pipeline call."""
    pipe = redis.pipeline()
    for sym in symbols:
        pipe.get(f"price:{sym.upper()}")
    results = await pipe.execute()
    return {
        sym: json.loads(raw) if raw else None
        for sym, raw in zip(symbols, results)
    }


# ─── Cold Path: TimescaleDB ───────────────────────────────────────────────────

async def get_ohlcv_bars(
    db: AsyncSession,
    symbol: str,
    timeframe: str = "1d",
    limit: int = 200,
) -> list[dict]:
    """Fetch OHLCV bars from TimescaleDB hypertable."""
    query = text("""
        SELECT time, open, high, low, close, volume
        FROM market_bars
        WHERE symbol = :symbol AND timeframe = :timeframe
        ORDER BY time DESC
        LIMIT :limit
    """)
    result = await db.execute(query, {"symbol": symbol.upper(), "timeframe": timeframe, "limit": limit})
    rows = result.fetchall()
    return [
        {
            "time": row.time.isoformat(),
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": int(row.volume),
        }
        for row in reversed(rows)  # return chronological order
    ]


async def upsert_ohlcv_bars(db: AsyncSession, symbol: str, timeframe: str, bars: list[dict]) -> int:
    """Insert OHLCV bars into TimescaleDB, ignore duplicates."""
    if not bars:
        return 0
    query = text("""
        INSERT INTO market_bars (time, symbol, timeframe, open, high, low, close, volume)
        VALUES (:time, :symbol, :timeframe, :open, :high, :low, :close, :volume)
        ON CONFLICT (time, symbol, timeframe) DO UPDATE SET
            open   = EXCLUDED.open,
            high   = EXCLUDED.high,
            low    = EXCLUDED.low,
            close  = EXCLUDED.close,
            volume = EXCLUDED.volume
    """)
    count = 0
    for bar in bars:
        await db.execute(query, {
            "time": bar["time"],
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            **{k: bar[k] for k in ("open", "high", "low", "close", "volume")},
        })
        count += 1
    await db.commit()
    return count


# ─── yfinance Data Provider (dev/backtesting) ─────────────────────────────────

def fetch_yfinance_bars(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> list[dict]:
    """
    Fetch OHLCV bars from yfinance.
    WARNING: yfinance is for development/backtesting only.
    Use Alpaca data feed in production.
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        return []
    df.index = pd.to_datetime(df.index, utc=True)
    return [
        {
            "time": idx.to_pydatetime(),
            "open": float(row.Open),
            "high": float(row.High),
            "low": float(row.Low),
            "close": float(row.Close),
            "volume": int(row.Volume),
        }
        for idx, row in df.iterrows()
    ]


def fetch_latest_quote_yfinance(symbol: str) -> dict | None:
    """Fetch current price from yfinance (dev fallback)."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.last_price
        prev_close = info.previous_close
        change = price - prev_close if prev_close else 0.0
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        return {
            "symbol": symbol.upper(),
            "price": round(float(price), 4),
            "change": round(float(change), 4),
            "change_pct": round(float(change_pct), 4),
            "volume": int(info.three_month_average_volume or 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "yfinance",
        }
    except Exception:
        return None


# ─── Bulk Refresh (called by Celery task) ────────────────────────────────────

async def refresh_quotes_to_cache(redis: aioredis.Redis, symbols: list[str]) -> dict[str, bool]:
    """
    Fetch latest prices for all symbols and store in Redis.
    Called by Celery beat every 60 seconds during market hours.
    Returns dict of symbol → success.
    """
    results: dict[str, bool] = {}

    async def _fetch_and_cache(sym: str) -> None:
        quote = await asyncio.to_thread(fetch_latest_quote_yfinance, sym)
        if quote:
            await cache_quote(redis, sym, quote)
            results[sym] = True
        else:
            results[sym] = False

    await asyncio.gather(*[_fetch_and_cache(sym) for sym in symbols])
    return results


async def bootstrap_historical_data(
    db: AsyncSession,
    redis: aioredis.Redis,
    symbols: list[str],
    period: str = "1y",
) -> dict[str, int]:
    """
    One-time bootstrap: fetch 1yr of daily bars for all symbols → TimescaleDB.
    Also primes the Redis quote cache.
    """
    counts: dict[str, int] = {}
    for symbol in symbols:
        bars = await asyncio.to_thread(fetch_yfinance_bars, symbol, period, "1d")
        n = await upsert_ohlcv_bars(db, symbol, "1d", bars)
        counts[symbol] = n
        # Also prime cache with latest bar
        if bars:
            latest = bars[-1]
            await cache_quote(redis, symbol, {
                "symbol": symbol.upper(),
                "price": latest["close"],
                "change": 0.0,
                "change_pct": 0.0,
                "volume": latest["volume"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "timescaledb_bootstrap",
            })
    return counts
