"""
Hedge Engine — full orchestration of trigger → recommend → execute → log.

This is called by the risk monitor Celery task every 60 seconds.
It coordinates trigger evaluation, hedge recommendation, and order placement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.brokers.base import BaseBroker, OrderRequest, OrderSide, OrderType
from app.core.config import settings
from app.domains.hedge.recommender import compute_hedge_recommendation, should_rehedge
from app.domains.hedge.trigger import HedgeTriggerResult, TriggerType, evaluate_hedge_triggers
from app.domains.market_data.services import get_cached_quote
from app.domains.risk.metrics import portfolio_beta, rolling_beta

logger = logging.getLogger(__name__)


async def run_hedge_cycle(
    portfolio_id:      str,
    user_id:           str,
    broker:            BaseBroker,
    db:                AsyncSession,
    redis:             aioredis.Redis,
    portfolio_value:   float,
    portfolio_returns: "pd.Series | None" = None,
    benchmark_returns: "pd.Series | None" = None,
    thresholds:        dict | None = None,
    dry_run:           bool = False,
) -> dict:
    """
    Full hedge cycle: evaluate → recommend → execute → log.

    Args:
        dry_run: If True, compute recommendation but don't place orders.

    Returns dict with full hedge cycle result.
    """
    import pandas as pd

    result = {
        "portfolio_id": portfolio_id,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "action":       "none",
        "trigger":      None,
        "recommendation": None,
        "order":        None,
        "error":        None,
    }

    try:
        # ── 1. Get current market data ────────────────────────────────────────
        vix_quote = await get_cached_quote(redis, "VXX")
        vix = float(vix_quote["price"]) if vix_quote else 18.0  # neutral default

        # ── 2. Get portfolio metrics from DB ──────────────────────────────────
        pos_q = await db.execute(text("""
            SELECT symbol, quantity, avg_cost, current_price,
                   (current_price - avg_cost) / avg_cost AS pnl_pct
            FROM positions
            WHERE portfolio_id = :pid
        """), {"pid": portfolio_id})
        positions = pos_q.fetchall()

        if not positions:
            result["action"] = "skipped"
            result["error"]  = "No open positions"
            return result

        # Calculate portfolio-level stats
        total_value    = sum(p.quantity * (p.current_price or p.avg_cost) for p in positions)
        largest_loss   = min((p.pnl_pct or 0.0) for p in positions)
        largest_weight = max((p.quantity * (p.current_price or p.avg_cost)) / portfolio_value
                            for p in positions) if portfolio_value > 0 else 0.0

        # Get beta from cache or calculate
        cached_beta_raw = await redis.get(f"portfolio:beta:{portfolio_id}")
        if cached_beta_raw:
            curr_beta = float(json.loads(cached_beta_raw).get("beta", 1.0))
        else:
            curr_beta = 1.0  # assume market-neutral default

        # Get drawdown from risk snapshot
        snap_q = await db.execute(text("""
            SELECT max_drawdown FROM risk_snapshots
            WHERE portfolio_id = :pid
            ORDER BY snapshot_date DESC LIMIT 1
        """), {"pid": portfolio_id})
        snap = snap_q.fetchone()
        portfolio_drawdown = float(snap.max_drawdown) if snap else 0.0

        # ── 3. Get user thresholds ────────────────────────────────────────────
        if not thresholds:
            t_q = await db.execute(text("""
                SELECT max_drawdown_trigger, max_position_beta,
                       single_position_loss, vix_caution_level,
                       vix_hedge_level, vix_aggressive_level
                FROM user_settings WHERE user_id = :uid
            """), {"uid": user_id})
            t_row = t_q.fetchone()
            if t_row:
                thresholds = {
                    "max_drawdown_trigger": float(t_row.max_drawdown_trigger),
                    "max_position_beta":    float(t_row.max_position_beta),
                    "single_position_loss": float(t_row.single_position_loss),
                    "vix_caution_level":    float(t_row.vix_caution_level),
                    "vix_hedge_level":      float(t_row.vix_hedge_level),
                    "vix_aggressive_level": float(t_row.vix_aggressive_level),
                }

        # ── 4. Evaluate triggers ──────────────────────────────────────────────
        trigger = evaluate_hedge_triggers(
            vix=vix,
            portfolio_drawdown=portfolio_drawdown,
            portfolio_beta=curr_beta,
            largest_position_loss=largest_loss,
            thresholds=thresholds,
        )
        result["trigger"] = {
            "should_hedge":      trigger.should_hedge,
            "trigger_type":      trigger.trigger_type.value,
            "trigger_value":     trigger.trigger_value,
            "hedge_ratio":       trigger.hedge_ratio,
            "regime":            trigger.regime.value,
            "explanation":       trigger.explanation,
        }

        if not trigger.should_hedge:
            result["action"] = "monitoring"
            # Publish no-action status to WebSocket
            await redis.publish("realtime:alerts", json.dumps({
                "type": "hedge_status",
                "data": {"status": "monitoring", **result["trigger"]},
            }))
            return result

        # ── 5. Get instrument prices ──────────────────────────────────────────
        instrument_prices = {}
        for sym in ["SH", "SDS", "PSQ"]:
            quote = await get_cached_quote(redis, sym)
            if quote:
                instrument_prices[sym] = float(quote["price"])

        if not instrument_prices:
            result["error"] = "Hedge instrument prices unavailable"
            return result

        # ── 6. Compute recommendation ─────────────────────────────────────────
        tech_symbols = {"AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "AMZN"}
        tech_val = sum(
            p.quantity * (p.current_price or p.avg_cost)
            for p in positions if p.symbol in tech_symbols
        )
        tech_weight = tech_val / portfolio_value if portfolio_value > 0 else 0.0

        rec = compute_hedge_recommendation(
            trigger=trigger,
            portfolio_value=portfolio_value,
            portfolio_beta=curr_beta,
            instrument_prices=instrument_prices,
            tech_weight=tech_weight,
        )

        if not rec:
            result["error"] = "Could not compute hedge recommendation"
            return result

        result["recommendation"] = {
            "instrument":         rec.instrument,
            "shares":             rec.shares,
            "estimated_cost":     rec.estimated_cost,
            "beta_reduction":     rec.beta_reduction,
            "new_portfolio_beta": rec.new_portfolio_beta,
            "hedge_effectiveness": rec.hedge_effectiveness,
            "explanation":        rec.explanation,
        }

        if dry_run:
            result["action"] = "dry_run"
            return result

        # ── 7. Place hedge order ──────────────────────────────────────────────
        order_req = OrderRequest(
            symbol=rec.instrument,
            side=OrderSide.BUY,
            quantity=float(rec.shares),
            order_type=OrderType.MARKET,
            is_hedge=True,
            reason=trigger.explanation,
        )
        order_result = await broker.place_order(order_req)
        result["order"] = {
            "broker_order_id": order_result.broker_order_id,
            "status":          order_result.status.value,
            "filled_price":    order_result.filled_price,
        }
        result["action"] = "hedged" if order_result.is_success else "failed"

        # ── 8. Log hedge event to DB ──────────────────────────────────────────
        if order_result.is_success:
            await db.execute(text("""
                INSERT INTO hedge_events (
                    portfolio_id, trigger_type, trigger_value, trigger_threshold,
                    portfolio_beta_before, portfolio_beta_after,
                    hedge_instrument, hedge_quantity, hedge_cost,
                    estimated_risk_reduction, explanation, status
                ) VALUES (
                    :pid, :ttype, :tval, :tthresh,
                    :beta_before, :beta_after,
                    :instrument, :qty, :cost,
                    :risk_reduction, :explanation, 'executed'
                )
            """), {
                "pid":            portfolio_id,
                "ttype":          trigger.trigger_type.value,
                "tval":           trigger.trigger_value,
                "tthresh":        trigger.trigger_threshold,
                "beta_before":    curr_beta,
                "beta_after":     rec.new_portfolio_beta,
                "instrument":     rec.instrument,
                "qty":            rec.shares,
                "cost":           rec.estimated_cost,
                "risk_reduction": rec.hedge_effectiveness,
                "explanation":    trigger.explanation + " | " + rec.explanation,
            })
            await db.commit()

            # Update cached beta
            await redis.setex(
                f"portfolio:beta:{portfolio_id}",
                300,
                json.dumps({"beta": rec.new_portfolio_beta, "ts": datetime.now(timezone.utc).isoformat()}),
            )

            # Broadcast hedge alert to WebSocket
            await redis.publish("realtime:alerts", json.dumps({
                "type": "hedge_alert",
                "data": {
                    "portfolio_id": portfolio_id,
                    "instrument":   rec.instrument,
                    "shares":       rec.shares,
                    "beta_before":  curr_beta,
                    "beta_after":   rec.new_portfolio_beta,
                    "trigger":      trigger.trigger_type.value,
                    "explanation":  trigger.explanation,
                },
            }))

        logger.info(
            "Hedge cycle complete | portfolio=%s action=%s instrument=%s shares=%d",
            portfolio_id[:8], result["action"], rec.instrument, rec.shares,
        )

    except Exception as exc:
        logger.error("Hedge cycle error for portfolio %s: %s", portfolio_id, exc)
        result["error"]  = str(exc)
        result["action"] = "error"

    return result
