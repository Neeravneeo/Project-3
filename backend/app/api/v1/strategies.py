"""Strategies API endpoints — list, update, performance."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import Strategy
from app.schemas import StrategyResponse, StrategyUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[StrategyResponse])
async def list_strategies(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StrategyResponse]:
    """Return all strategies for the current user."""
    result = await db.execute(
        select(Strategy).where(Strategy.user_id == current_user.id)
    )
    strategies = result.scalars().all()
    return [StrategyResponse.model_validate(s) for s in strategies]


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    body: StrategyUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StrategyResponse:
    """Update a strategy's enabled state and parameters."""
    result = await db.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    if body.is_enabled is not None:
        strategy.is_enabled = body.is_enabled
    if body.parameters is not None:
        strategy.parameters = body.parameters
    if body.risk_per_trade is not None:
        strategy.risk_per_trade = body.risk_per_trade

    await db.commit()
    await db.refresh(strategy)
    return StrategyResponse.model_validate(strategy)


@router.get("/{strategy_id}/performance", response_model=dict)
async def get_strategy_performance(
    strategy_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return performance stats for a single strategy."""
    result = await db.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
    )
    strategy = result.scalar_one_or_none()
    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    return {
        "id": str(strategy.id),
        "name": strategy.name,
        "win_rate": float(strategy.win_rate) if strategy.win_rate else None,
        "total_signals": strategy.total_signals,
        "avg_return": float(strategy.avg_return) if strategy.avg_return else None,
    }
