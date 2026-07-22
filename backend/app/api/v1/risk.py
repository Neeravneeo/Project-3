"""Risk API Router — /api/v1/risk/*"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.domains.market_data.services import get_ohlcv_bars
from app.domains.risk.metrics import compute_all_metrics

router = APIRouter()


def _get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis


# ── GET /risk/metrics ─────────────────────────────────────────────────────────
@router.get("/metrics")
async def get_risk_metrics(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Full portfolio risk metrics — VaR, CVaR, beta, Sharpe, Sortino, drawdown."""
    redis = _get_redis(request)

    # 1. Fetch user portfolio
    port_q = await db.execute(text("""
        SELECT id, cash_balance FROM portfolios WHERE user_id = :uid AND is_active = true LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()

    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio found")

    # 2. Fetch active positions
    pos_q = await db.execute(text("""
        SELECT symbol, quantity, avg_cost, COALESCE(current_price, avg_cost) AS price
        FROM positions WHERE portfolio_id = :pid
    """), {"pid": str(port.id)})
    positions = pos_q.fetchall()

    portfolio_value = float(port.cash_balance) + sum(p.quantity * p.price for p in positions)
    largest_weight = max((p.quantity * p.price / portfolio_value for p in positions), default=0.0) if portfolio_value > 0 else 0.0

    # 3. Fetch historical bars for portfolio estimation (or fallback to benchmark)
    bars = await get_ohlcv_bars(db, redis, "SPY", limit=252)
    if not bars:
        dates = pd.date_range(end=date.today(), periods=252, freq="B")
        returns = pd.Series([0.0005] * 252, index=dates)
        benchmark = pd.Series([0.0004] * 252, index=dates)
    else:
        df = pd.DataFrame(bars)
        df["returns"] = df["close"].pct_change()
        returns = df["returns"].dropna()
        benchmark = returns.copy()

    metrics = compute_all_metrics(
        portfolio_returns=returns,
        benchmark_returns=benchmark.tail(len(returns)),
        portfolio_value=portfolio_value,
        largest_position_weight=largest_weight,
    )

    return {
        "portfolio_id":    str(port.id),
        "portfolio_value": round(portfolio_value, 2),
        **metrics,
    }


# ── GET /risk/exposure ────────────────────────────────────────────────────────
@router.get("/exposure")
async def get_exposure(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Sector and asset exposure breakdown."""
    port_q = await db.execute(text("""
        SELECT id FROM portfolios WHERE user_id = :uid AND is_active = true LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()
    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio")

    pos_q = await db.execute(text("""
        SELECT symbol, quantity, avg_cost, COALESCE(current_price, avg_cost) AS price
        FROM positions WHERE portfolio_id = :pid
    """), {"pid": str(port.id)})
    positions = pos_q.fetchall()

    SECTOR_MAP = {
        "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
        "NVDA": "Technology", "META": "Technology", "TSLA": "Consumer Cyclical",
        "AMZN": "Consumer Cyclical", "JPM": "Financial", "BAC": "Financial",
        "JNJ": "Healthcare", "PFE": "Healthcare", "XOM": "Energy",
        "SPY": "Index", "QQQ": "Index", "IWM": "Index",
        "SH": "Hedge", "SDS": "Hedge", "PSQ": "Hedge",
    }

    total_value = sum(p.quantity * p.price for p in positions)
    sector_exposure: dict[str, float] = {}
    position_weights = []

    for p in positions:
        val    = float(p.quantity) * float(p.price)
        weight = val / total_value if total_value > 0 else 0
        sector = SECTOR_MAP.get(p.symbol, "Other")
        sector_exposure[sector] = sector_exposure.get(sector, 0.0) + weight
        position_weights.append({
            "symbol": p.symbol,
            "value":  round(val, 2),
            "weight": round(weight, 4),
            "sector": sector,
        })

    position_weights.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "total_exposure": round(total_value, 2),
        "sector_exposure": [
            {"sector": k, "weight": round(v, 4)}
            for k, v in sorted(sector_exposure.items(), key=lambda x: -x[1])
        ],
        "positions": position_weights[:20],
    }


# ── PUT /risk/thresholds ──────────────────────────────────────────────────────
@router.put("/thresholds")
async def update_thresholds(
    thresholds: dict,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update user's risk threshold settings."""
    allowed = {
        "max_drawdown_trigger", "max_position_beta", "single_position_loss",
        "vix_caution_level", "vix_hedge_level", "vix_aggressive_level",
        "max_position_weight",
    }
    filtered = {k: v for k, v in thresholds.items() if k in allowed}
    if not filtered:
        raise HTTPException(status_code=400, detail="No valid threshold fields provided")

    set_clause = ", ".join(f"{k} = :{k}" for k in filtered)
    await db.execute(
        text(f"UPDATE user_settings SET {set_clause}, updated_at = NOW() WHERE user_id = :uid"),
        {**filtered, "uid": str(current_user.id)},
    )
    await db.commit()
    return {"message": "Thresholds updated", "updated": filtered}


# ── GET /risk/history ─────────────────────────────────────────────────────────
@router.get("/history")
async def get_risk_history(
    current_user: CurrentUser,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Historical risk snapshots for charts."""
    port_q = await db.execute(text("""
        SELECT id FROM portfolios WHERE user_id = :uid AND is_active = true LIMIT 1
    """), {"uid": str(current_user.id)})
    port = port_q.fetchone()
    if not port:
        raise HTTPException(status_code=404, detail="No active portfolio")

    snaps_q = await db.execute(text("""
        SELECT snapshot_date, portfolio_value, portfolio_beta,
               var_95, max_drawdown, sharpe_ratio, risk_score
        FROM risk_snapshots
        WHERE portfolio_id = :pid
          AND snapshot_date >= CURRENT_DATE - :days
        ORDER BY snapshot_date ASC
    """), {"pid": str(port.id), "days": days})
    rows = snaps_q.fetchall()

    return {
        "snapshots": [
            {
                "date":            str(r.snapshot_date),
                "portfolio_value": float(r.portfolio_value or 0),
                "portfolio_beta":  float(r.portfolio_beta or 1.0),
                "var_95":          float(r.var_95 or 0),
                "max_drawdown":    float(r.max_drawdown or 0),
                "sharpe_ratio":    float(r.sharpe_ratio or 0),
                "risk_score":      int(r.risk_score or 0),
            }
            for r in rows
        ]
    }
