"""
Celery Task: Risk Monitor — runs every 60 seconds.
Monitors all active portfolios for risk threshold breaches
and triggers the hedge engine when needed.
"""

import asyncio
import logging
from datetime import date

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.risk_monitor.monitor_all_portfolios", bind=True, max_retries=2)
def monitor_all_portfolios(self):
    """
    For every active portfolio:
    1. Compute current risk metrics
    2. Evaluate hedge triggers
    3. Execute hedge if needed (paper mode)
    4. Publish alerts to WebSocket
    """
    async def _run():
        import redis.asyncio as aioredis
        from sqlalchemy import text
        from app.core.config import settings
        from app.core.database import AsyncSessionLocal
        from app.brokers.paper import PaperBroker
        from app.domains.hedge.engine import run_hedge_cycle

        r = await aioredis.from_url(settings.redis_url, decode_responses=True)

        async with AsyncSessionLocal() as db:
            port_q = await db.execute(text("""
                SELECT p.id, p.user_id, p.cash_balance,
                       COALESCE(SUM(pos.quantity * COALESCE(pos.current_price, pos.avg_cost)), 0)
                           AS positions_value
                FROM portfolios p
                LEFT JOIN positions pos ON pos.portfolio_id = p.id
                WHERE p.is_active = true
                GROUP BY p.id, p.user_id, p.cash_balance
            """))
            portfolios = port_q.fetchall()

            for port in portfolios:
                portfolio_value = float(port.cash_balance) + float(port.positions_value)
                broker = PaperBroker(redis=r, initial_capital=portfolio_value)

                await run_hedge_cycle(
                    portfolio_id=str(port.id),
                    user_id=str(port.user_id),
                    broker=broker,
                    db=db,
                    redis=r,
                    portfolio_value=portfolio_value,
                    dry_run=False,
                )

        await r.aclose()

    asyncio.run(_run())
    return {"status": "complete"}


@celery_app.task(name="workers.tasks.risk_monitor.generate_daily_snapshots", bind=True)
def generate_daily_snapshots(self):
    """
    Generate end-of-day risk snapshots for all portfolios.
    Runs at 18:00 UTC (after US market close).
    Stores in risk_snapshots table for historical charting.
    """
    async def _run():
        import pandas as pd
        import redis.asyncio as aioredis
        from sqlalchemy import text
        from app.core.config import settings
        from app.core.database import AsyncSessionLocal
        from app.domains.risk.metrics import compute_all_metrics
        from app.domains.market_data.services import get_ohlcv_bars

        r = await aioredis.from_url(settings.redis_url, decode_responses=True)
        today = date.today()

        async with AsyncSessionLocal() as db:
            port_q = await db.execute(text("""
                SELECT p.id, p.user_id, p.cash_balance,
                       COALESCE(SUM(pos.quantity * COALESCE(pos.current_price, pos.avg_cost)), 0)
                           AS positions_value,
                       MAX(pos.quantity * COALESCE(pos.current_price, pos.avg_cost))
                           / NULLIF(SUM(pos.quantity * COALESCE(pos.current_price, pos.avg_cost)), 0)
                           AS largest_weight
                FROM portfolios p
                LEFT JOIN positions pos ON pos.portfolio_id = p.id
                WHERE p.is_active = true
                GROUP BY p.id, p.user_id, p.cash_balance
            """))
            portfolios = port_q.fetchall()

            # Fetch SPY benchmark bars for beta calculation
            spy_bars = await get_ohlcv_bars(db, "SPY", timeframe="1d", limit=252)
            spy_df   = pd.DataFrame(spy_bars)
            spy_returns = pd.Series(dtype=float)
            if not spy_df.empty:
                spy_df["close"] = spy_df["close"].astype(float)
                spy_returns = spy_df["close"].pct_change().dropna()

            for port in portfolios:
                try:
                    portfolio_value   = float(port.cash_balance) + float(port.positions_value)
                    largest_weight    = float(port.largest_weight or 0)

                    # Fetch historical portfolio returns from order history
                    orders_q = await db.execute(text("""
                        SELECT DATE(created_at) AS day,
                               SUM(CASE WHEN side='sell'
                                        THEN filled_price * filled_qty ELSE 0 END)
                               - SUM(CASE WHEN side='buy'
                                          THEN filled_price * filled_qty ELSE 0 END) AS daily_pnl
                        FROM orders
                        WHERE portfolio_id = :pid AND status = 'filled'
                        GROUP BY day ORDER BY day
                    """), {"pid": str(port.id)})
                    daily_rows = orders_q.fetchall()

                    if daily_rows:
                        pnl_series  = pd.Series([float(r.daily_pnl) for r in daily_rows])
                        returns     = pnl_series / portfolio_value
                    else:
                        returns = pd.Series(dtype=float)

                    metrics = compute_all_metrics(
                        portfolio_returns=returns,
                        benchmark_returns=spy_returns.tail(len(returns)),
                        portfolio_value=portfolio_value,
                        largest_position_weight=largest_weight,
                    )

                    # Upsert today's snapshot
                    await db.execute(text("""
                        INSERT INTO risk_snapshots (
                            portfolio_id, snapshot_date, portfolio_value,
                            cash_balance, portfolio_beta, var_95, cvar_95,
                            max_drawdown, sharpe_ratio, sortino_ratio,
                            calmar_ratio, risk_score
                        ) VALUES (
                            :pid, :day, :val, :cash, :beta, :var95, :cvar95,
                            :mdd, :sharpe, :sortino, :calmar, :score
                        )
                        ON CONFLICT (portfolio_id, snapshot_date) DO UPDATE SET
                            portfolio_value = EXCLUDED.portfolio_value,
                            portfolio_beta  = EXCLUDED.portfolio_beta,
                            var_95          = EXCLUDED.var_95,
                            max_drawdown    = EXCLUDED.max_drawdown,
                            sharpe_ratio    = EXCLUDED.sharpe_ratio,
                            risk_score      = EXCLUDED.risk_score
                    """), {
                        "pid":     str(port.id),
                        "day":     today,
                        "val":     portfolio_value,
                        "cash":    float(port.cash_balance),
                        "beta":    metrics["portfolio_beta"],
                        "var95":   metrics["var_95_dollar"],
                        "cvar95":  metrics["cvar_95_dollar"],
                        "mdd":     metrics["max_drawdown"],
                        "sharpe":  metrics["sharpe_ratio"],
                        "sortino": metrics["sortino_ratio"],
                        "calmar":  metrics["calmar_ratio"],
                        "score":   metrics["risk_score"],
                    })

                    logger.info("Risk snapshot saved: portfolio=%s score=%d",
                                str(port.id)[:8], metrics["risk_score"])

                except Exception as exc:
                    logger.error("Snapshot failed for portfolio %s: %s", str(port.id)[:8], exc)

            await db.commit()
        await r.aclose()

    asyncio.run(_run())
    return {"status": "snapshots_complete"}
