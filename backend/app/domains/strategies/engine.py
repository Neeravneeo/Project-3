"""
Strategy Engine — orchestrates all active strategies for a given symbol.

This is the main entry point called by:
  - Celery beat task every 5 minutes
  - WebSocket price update handler (on significant price move)
  - Manual signal refresh via API

Flow:
  1. Fetch OHLCV bars from TimescaleDB (cold path)
  2. Run all enabled strategies in parallel
  3. Aggregate signals via weighted voting
  4. Store result in Redis (hot cache) + TimescaleDB
  5. Publish to WebSocket channel for real-time frontend update
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

import pandas as pd
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.domains.market_data.services import get_ohlcv_bars
from app.domains.strategies.base_strategy import SignalDirection, SignalResult
from app.domains.strategies.ema_crossover import EMACrossoverStrategy
from app.domains.strategies.mean_reversion import MeanReversionStrategy
from app.domains.strategies.rsi_momentum import RSIMomentumStrategy
from app.domains.strategies.signal_aggregator import aggregate_signals, AggregatedSignal

logger = logging.getLogger(__name__)

# ── Strategy registry — add new strategies here ───────────────────────────────
STRATEGY_REGISTRY = {
    "ema_crossover":  EMACrossoverStrategy,
    "rsi_momentum":   RSIMomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}


async def run_strategies_for_symbol(
    symbol: str,
    db: AsyncSession,
    redis: aioredis.Redis,
    enabled_strategies: dict[str, dict],  # {strategy_name: parameters}
    bars_limit: int = 200,
) -> AggregatedSignal:
    """
    Run all enabled strategies for one symbol and return aggregated signal.

    Args:
        symbol:             Ticker symbol (e.g. 'AAPL')
        db:                 Async DB session for fetching OHLCV bars
        redis:              Redis client for caching results
        enabled_strategies: Dict of {strategy_name: parameters_dict}
        bars_limit:         How many historical bars to load

    Returns:
        AggregatedSignal combining all strategy votes
    """
    # 1. Fetch OHLCV bars from TimescaleDB
    bars = await get_ohlcv_bars(db, symbol, timeframe="1d", limit=bars_limit)

    if len(bars) < 60:
        logger.warning("Insufficient bars for %s: %d bars", symbol, len(bars))
        from app.domains.strategies.signal_aggregator import _hold_signal
        return _hold_signal(symbol, f"Only {len(bars)} bars available (need 60+)")

    # Convert to DataFrame
    df = pd.DataFrame(bars)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 2. Run all enabled strategies concurrently
    async def _run_strategy(name: str, params: dict) -> SignalResult | None:
        cls = STRATEGY_REGISTRY.get(name)
        if cls is None:
            logger.warning("Unknown strategy: %s", name)
            return None
        try:
            strategy = cls(parameters=params)
            # Run CPU-bound indicator math in thread pool
            result = await asyncio.to_thread(strategy.generate_signal, df, symbol)
            return result
        except Exception as exc:
            logger.error("Strategy %s failed for %s: %s", name, symbol, exc)
            return None

    tasks = [_run_strategy(name, params) for name, params in enabled_strategies.items()]
    raw_results = await asyncio.gather(*tasks)
    signals = [r for r in raw_results if r is not None]

    # 3. Aggregate
    aggregated = aggregate_signals(signals)

    # 4. Cache in Redis (TTL: 5 minutes)
    cache_payload = {
        "symbol":          symbol,
        "direction":       aggregated.direction.value,
        "confidence":      aggregated.confidence,
        "agreement_ratio": aggregated.agreement_ratio,
        "net_score":       aggregated.net_score,
        "explanation":     aggregated.explanation,
        "contributing":    aggregated.contributing,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }
    await redis.setex(
        f"signal:{symbol.upper()}",
        300,
        json.dumps(cache_payload),
    )

    # 5. Publish to WebSocket channel
    await redis.publish(
        "realtime:signals",
        json.dumps({"type": "signal", "data": cache_payload}),
    )

    logger.info(
        "Signal generated | %s → %s (confidence=%.2f, strategies=%d)",
        symbol,
        aggregated.direction.value.upper(),
        aggregated.confidence,
        len(signals),
    )
    return aggregated


async def run_strategies_for_portfolio(
    portfolio_symbols: list[str],
    db: AsyncSession,
    redis: aioredis.Redis,
    enabled_strategies: dict[str, dict],
) -> dict[str, AggregatedSignal]:
    """
    Run strategies for all symbols in portfolio concurrently.
    Returns dict of {symbol: AggregatedSignal}
    """
    tasks = {
        sym: run_strategies_for_symbol(sym, db, redis, enabled_strategies)
        for sym in portfolio_symbols
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    output = {}
    for sym, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error("Strategy run failed for %s: %s", sym, result)
        else:
            output[sym] = result
    return output


async def get_cached_signal(redis: aioredis.Redis, symbol: str) -> dict | None:
    """Read latest aggregated signal from Redis cache."""
    raw = await redis.get(f"signal:{symbol.upper()}")
    return json.loads(raw) if raw else None


async def save_signals_to_db(
    db: AsyncSession,
    user_id: str,
    signals: list[SignalResult],
) -> None:
    """Persist individual strategy signals to TimescaleDB for history."""
    query = text("""
        INSERT INTO signals
            (user_id, strategy_id, symbol, direction, confidence,
             technical_score, explanation, raw_indicators)
        SELECT
            :user_id,
            s.id,
            :symbol,
            :direction,
            :confidence,
            :technical_score,
            :explanation,
            :raw_indicators::jsonb
        FROM strategies s
        WHERE s.user_id = :user_id AND s.name = :strategy_name
        LIMIT 1
    """)
    for sig in signals:
        await db.execute(query, {
            "user_id":        user_id,
            "symbol":         sig.symbol.upper(),
            "strategy_name":  sig.strategy_name,
            "direction":      sig.direction.value,
            "confidence":     sig.confidence,
            "technical_score": sig.technical_score,
            "explanation":    sig.explanation,
            "raw_indicators": json.dumps(sig.indicators),
        })
    await db.commit()
