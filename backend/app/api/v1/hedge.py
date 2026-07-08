"""Hedge API endpoints — status, history, manual trigger."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import HedgeEvent, Portfolio
from app.schemas import HedgeEventResponse, HedgeStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=HedgeStatusResponse)
async def get_hedge_status(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HedgeStatusResponse:
    """Return the current hedge engine status."""
    port_result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id, Portfolio.is_active == True)
        .limit(1)
    )
    portfolio = port_result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active portfolio found")

    # Latest triggered (not expired) hedge event
    result = await db.execute(
        select(HedgeEvent)
        .where(HedgeEvent.portfolio_id == portfolio.id, HedgeEvent.status == "executed")
        .order_by(HedgeEvent.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    return HedgeStatusResponse(
        is_active=latest is not None,
        trigger_type=latest.trigger_type if latest else None,
        hedge_instrument=latest.hedge_instrument if latest else None,
        hedge_quantity=latest.hedge_quantity if latest else None,
        last_triggered_at=latest.created_at if latest else None,
    )


@router.get("/history", response_model=list[HedgeEventResponse])
async def get_hedge_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
) -> list[HedgeEventResponse]:
    """Return the hedge event log for the user's portfolio."""
    port_result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id, Portfolio.is_active == True)
        .limit(1)
    )
    portfolio = port_result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active portfolio found")

    result = await db.execute(
        select(HedgeEvent)
        .where(HedgeEvent.portfolio_id == portfolio.id)
        .order_by(HedgeEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [HedgeEventResponse.model_validate(e) for e in events]


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def manual_trigger(current_user: CurrentUser) -> dict:
    """Manually trigger the hedge engine (queues a Celery task).

    NOTE: Full Celery task implementation is in Phase 1C.
    """
    logger.info("Manual hedge trigger requested", extra={"user_id": str(current_user.id)})
    return {
        "message": "Hedge evaluation queued. Full execution will be available in Phase 1C.",
        "status": "accepted",
    }
