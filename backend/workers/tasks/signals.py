"""
Celery Task: Signal generation for all active users.
Runs every 5 minutes. Reads enabled strategies from DB,
fetches OHLCV, runs strategy engine, stores results.
"""

import asyncio
import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.signals.generate_signals_all_users", bind=True, max_retries=2)
def generate_signals_all_users(self):
    """
    For every active user portfolio:
    1. Load enabled strategies + parameters from DB
    2. Load watchlist symbols
    3. Run strategy engine for each symbol
    4. Store results in Redis + TimescaleDB
    """
    async def _run():
        import redis.asyncio as aioredis
        from sqlalchemy import text
        from app.core.config import settings
        from app.core.database import AsyncSessionLocal
        from app.domains.strategies.engine import run_strategies_for_symbol

        r = await aioredis.from_url(settings.redis_url, decode_responses=True)

        async with AsyncSessionLocal() as db:
            # Get all active users with at least one enabled strategy
            users_q = await db.execute(text("""
                SELECT DISTINCT u.id as user_id
                FROM users u
                JOIN strategies s ON s.user_id = u.id
                WHERE u.is_active = true AND s.is_enabled = true
            """))
            user_ids = [str(row.user_id) for row in users_q.fetchall()]

            for user_id in user_ids:
                # Get enabled strategies for this user
                strat_q = await db.execute(text("""
                    SELECT name, parameters
                    FROM strategies
                    WHERE user_id = :uid AND is_enabled = true
                """), {"uid": user_id})
                enabled = {row.name: row.parameters for row in strat_q.fetchall()}

                if not enabled:
                    continue

                # Get portfolio symbols
                sym_q = await db.execute(text("""
                    SELECT DISTINCT symbol FROM positions
                    WHERE portfolio_id IN (
                        SELECT id FROM portfolios WHERE user_id = :uid AND is_active = true
                    )
                """), {"uid": user_id})
                symbols = [row.symbol for row in sym_q.fetchall()]

                # Always include watchlist defaults
                from workers.tasks.data_refresh import DEFAULT_WATCHLIST
                all_symbols = list(set(symbols + DEFAULT_WATCHLIST[:10]))

                # Run strategy engine for all symbols concurrently
                tasks = [
                    run_strategies_for_symbol(sym, db, r, enabled)
                    for sym in all_symbols
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                ok = sum(1 for r in results if not isinstance(r, Exception))
                logger.info("Signals generated for user %s: %d/%d symbols OK",
                            user_id[:8], ok, len(all_symbols))

        await r.aclose()

    asyncio.run(_run())
    return {"status": "complete"}
