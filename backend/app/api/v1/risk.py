"""Risk API endpoints — metrics, exposure, threshold updates."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import Portfolio, RiskSnapshot
from app.schemas import RiskMetricsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskMetricsResponse:
    """Return the latest risk metrics snapshot for the user's portfolio."""
    port_result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id, Portfolio.is_active == True)
        .limit(1)
    )
    portfolio = port_result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active portfolio found")

    snap_result = await db.execute(
        select(RiskSnapshot)
        .where(RiskSnapshot.portfolio_id == portfolio.id)
        .order_by(RiskSnapshot.snapshot_date.desc())
        .limit(1)
    )
    snap = snap_result.scalar_one_or_none()
    if snap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk metrics available yet. Run the daily report task first.",
        )
    return RiskMetricsResponse.model_validate(snap)


@router.get("/exposure", response_model=dict)
async def get_exposure(current_user: CurrentUser) -> dict:
    """Return sector and asset concentration exposure.

    NOTE: Full implementation requires positions + sector classification.
    Returns placeholder structure for Phase 1C.
    """
    return {
        "sectors": [],
        "top_positions": [],
        "message": "Exposure analysis will be computed in Phase 1C.",
    }


@router.put("/thresholds", status_code=status.HTTP_200_OK)
async def update_thresholds(
    body: dict,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Update user risk thresholds in user_settings."""
    from decimal import Decimal

    from app.models import UserSettings

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    us = result.scalar_one_or_none()
    if us is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User settings not found")

    allowed_fields = {
        "max_drawdown_trigger", "max_position_beta", "single_position_loss",
        "vix_caution_level", "vix_hedge_level", "vix_aggressive_level", "max_position_weight",
    }
    for field, value in body.items():
        if field in allowed_fields:
            setattr(us, field, Decimal(str(value)))

    await db.commit()
    return {"message": "Thresholds updated"}
