"""Signals API endpoints — list, history, detail."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import Signal
from app.schemas import PaginatedResponse, SignalResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[SignalResponse])
async def list_signals(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=200),
) -> list[SignalResponse]:
    """Return the most recent signals for the current user."""
    result = await db.execute(
        select(Signal)
        .where(Signal.user_id == current_user.id)
        .order_by(Signal.created_at.desc())
        .limit(limit)
    )
    signals = result.scalars().all()
    return [SignalResponse.model_validate(s) for s in signals]


@router.get("/history", response_model=PaginatedResponse[SignalResponse])
async def signal_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, le=100),
    strategy_id: UUID | None = Query(default=None),
    symbol: str | None = Query(default=None),
) -> PaginatedResponse[SignalResponse]:
    """Paginated signal history with optional strategy/symbol filters."""
    query = select(Signal).where(Signal.user_id == current_user.id)

    if strategy_id is not None:
        query = query.where(Signal.strategy_id == strategy_id)
    if symbol is not None:
        query = query.where(Signal.symbol == symbol.upper())

    # Count total
    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Paginate
    query = query.order_by(Signal.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    signals = result.scalars().all()

    return PaginatedResponse(
        items=[SignalResponse.model_validate(s) for s in signals],
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total,
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SignalResponse:
    """Return a single signal with full indicator breakdown."""
    result = await db.execute(
        select(Signal).where(Signal.id == signal_id, Signal.user_id == current_user.id)
    )
    signal = result.scalar_one_or_none()
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")
    return SignalResponse.model_validate(signal)
