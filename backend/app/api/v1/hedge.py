"""Hedge API Router — /api/v1/hedge/*"""

from __future__ import annotations

import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.brokers.paper import PaperBroker
from app.core.database import get_db
from app.domains.hedge.engine import run_hedge_cycle
from app.domains.hedge.trigger import classify_regime, evaluate_hedge_triggers
from app.domains.market_data.services import get_cached_quote

router = APIRouter()


def _get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis


# ── GET /hedge/status ─────────────────────────────────────────────────────────
@router.get("/status")
async def get_hedge_status(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Current hedge state — active hedge positions, last trigger, regime."""
    redis = _get_redis(request)

    # 1. Fetch user portfolio
    port_q = await db.execute(text("""
        SELECT id FROM portfolios WHERE user_id = :uid AND is_active = true LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()

    # 2. Check active hedge positions in Redis / DB
    vix_quote = await get_cached_quote(redis, "VXX")
    vix = float(vix_quote["price"]) if vix_quote else 18.2
    regime = classify_regime(vix)

    # 3. Check for recent hedge_events
    last_event = None
    if port:
        evt_q = await db.execute(text("""
            SELECT trigger_type, trigger_value, portfolio_beta_before,
                   portfolio_beta_after, hedge_instrument, hedge_quantity,
                   hedge_cost, explanation, created_at
            FROM hedge_events
            WHERE portfolio_id = :pid
            ORDER BY created_at DESC LIMIT 1
        """), {"pid": str(port.id)})
        last_event = evt_q.fetchone()

    # Check active hedge position in positions table
    hedge_pos = None
    if port:
        pos_q = await db.execute(text("""
            SELECT symbol, quantity, avg_cost, current_price
            FROM positions
            WHERE portfolio_id = :pid AND symbol IN ('SH', 'SDS', 'PSQ') AND quantity > 0
        """), {"pid": str(port.id)})
        hedge_pos = pos_q.fetchall()

    is_hedged = bool(hedge_pos and len(hedge_pos) > 0)
    last = last_event

    return {
        "is_hedged": is_hedged,
        "regime": regime,
        "vix_level": vix,
        "active_hedge_positions": [
            {
                "symbol": r.symbol,
                "quantity": float(r.quantity),
                "avg_cost": float(r.avg_cost),
                "current_price": float(r.current_price or r.avg_cost),
            }
            for r in (hedge_pos or [])
        ],
        "last_trigger_event": {
            "trigger_type":    last.trigger_type,
            "trigger_value":   float(last.trigger_value),
            "beta_before":     float(last.portfolio_beta_before or 0),
            "beta_after":      float(last.portfolio_beta_after or 0),
            "instrument":      last.hedge_instrument,
            "quantity":        float(last.hedge_quantity),
            "cost":            float(last.hedge_cost),
            "explanation":     last.explanation,
            "timestamp":       last.created_at.isoformat(),
        } if last else None,
    }


# ── GET /hedge/history ────────────────────────────────────────────────────────
@router.get("/history")
async def get_hedge_history(
    current_user: CurrentUser,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Paginated hedge event log."""
    port_q = await db.execute(text("""
        SELECT id FROM portfolios WHERE user_id = :uid AND is_active = true LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()
    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio")

    events_q = await db.execute(text("""
        SELECT trigger_type, trigger_value, trigger_threshold,
               portfolio_beta_before, portfolio_beta_after,
               hedge_instrument, hedge_quantity, hedge_cost,
               estimated_risk_reduction, explanation, status, created_at
        FROM hedge_events
        WHERE portfolio_id = :pid
        ORDER BY created_at DESC
        LIMIT :lim
    """), {"pid": str(port.id), "lim": limit})

    return {
        "events": [
            {
                "trigger_type":       r.trigger_type,
                "trigger_value":      float(r.trigger_value),
                "trigger_threshold":  float(r.trigger_threshold or 0),
                "beta_before":        float(r.portfolio_beta_before or 0),
                "beta_after":         float(r.portfolio_beta_after or 0),
                "instrument":         r.hedge_instrument,
                "quantity":           float(r.hedge_quantity),
                "cost":               float(r.hedge_cost),
                "risk_reduction":     float(r.estimated_risk_reduction or 0),
                "explanation":        r.explanation,
                "status":             r.status,
                "timestamp":          r.created_at.isoformat(),
            }
            for r in events_q.fetchall()
        ]
    }


# ── POST /hedge/trigger ───────────────────────────────────────────────────────
@router.post("/trigger")
async def manual_trigger_hedge(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a hedge analysis cycle (dry_run by default)."""
    redis = _get_redis(request)

    port_q = await db.execute(text("""
        SELECT id, cash_balance,
               COALESCE(SUM(pos.quantity * COALESCE(pos.current_price, pos.avg_cost)), 0) AS pos_val
        FROM portfolios p
        LEFT JOIN positions pos ON pos.portfolio_id = p.id
        WHERE p.user_id = :uid AND p.is_active = true
        GROUP BY p.id, p.cash_balance LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()
    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio")

    portfolio_value = float(port.cash_balance) + float(port.pos_val or 0)
    broker = PaperBroker(redis=redis, initial_capital=portfolio_value)

    result = await run_hedge_cycle(
        portfolio_id=str(port.id),
        user_id=str(current_user.id),
        broker=broker,
        db=db,
        redis=redis,
        portfolio_value=portfolio_value,
        dry_run=False,
    )

    return result


# ── GET /hedge/analysis ───────────────────────────────────────────────────────
@router.get("/analysis")
async def get_hedge_analysis(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Run a dry-run hedge analysis — see what WOULD happen without executing."""
    redis = _get_redis(request)

    port_q = await db.execute(text("""
        SELECT p.id, p.cash_balance,
               COALESCE(SUM(pos.quantity * COALESCE(pos.current_price, pos.avg_cost)), 0) AS pos_val
        FROM portfolios p
        LEFT JOIN positions pos ON pos.portfolio_id = p.id
        WHERE p.user_id = :uid AND p.is_active = true
        GROUP BY p.id, p.cash_balance LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()
    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio")

    portfolio_value = float(port.cash_balance) + float(port.pos_val or 0)
    broker = PaperBroker(redis=redis, initial_capital=portfolio_value)

    result = await run_hedge_cycle(
        portfolio_id=str(port.id),
        user_id=str(current_user.id),
        broker=broker,
        db=db,
        redis=redis,
        portfolio_value=portfolio_value,
        dry_run=True,
    )

    return result
