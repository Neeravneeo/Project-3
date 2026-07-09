"""Portfolio API endpoints — portfolio summary, positions, performance."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import Portfolio, Position, RiskSnapshot
from app.schemas import PortfolioSummary, PositionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_active_portfolio(user_id: UUID, db: AsyncSession) -> Portfolio:
    """Return the user's active portfolio or raise 404."""
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id, Portfolio.is_active == True)
        .limit(1)
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active portfolio found")
    return portfolio


@router.get("", response_model=PortfolioSummary)
async def get_portfolio(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortfolioSummary:
    """Return portfolio summary with computed total value and P&L."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    result = await db.execute(
        select(Position).where(Position.portfolio_id == portfolio.id)
    )
    positions = result.scalars().all()

    positions_value = sum(
        (pos.current_price or pos.avg_cost) * pos.quantity for pos in positions
    )
    total_value = portfolio.cash_balance + positions_value
    total_pnl = total_value - portfolio.initial_capital

    # Get latest daily P&L from risk_snapshots
    snap_result = await db.execute(
        select(RiskSnapshot)
        .where(RiskSnapshot.portfolio_id == portfolio.id)
        .order_by(RiskSnapshot.snapshot_date.desc())
        .limit(2)
    )
    snaps = snap_result.scalars().all()
    daily_pnl = Decimal("0")
    if len(snaps) >= 2:
        daily_pnl = (snaps[0].portfolio_value or total_value) - (snaps[1].portfolio_value or total_value)

    return PortfolioSummary(
        id=portfolio.id,
        name=portfolio.name,
        currency=portfolio.currency,
        total_value=total_value,
        cash_balance=portfolio.cash_balance,
        daily_pnl=daily_pnl,
        total_pnl=total_pnl,
        num_positions=len(positions),
    )


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PositionResponse]:
    """Return all open positions for the user's active portfolio."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    result = await db.execute(
        select(Position).where(Position.portfolio_id == portfolio.id)
    )
    positions = result.scalars().all()
    return [PositionResponse.model_validate(p) for p in positions]


@router.get("/performance", response_model=list[dict])
async def get_performance(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: str = "1m",
) -> list[dict]:
    """Return historical portfolio value snapshots for the selected period."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    result = await db.execute(
        select(RiskSnapshot)
        .where(RiskSnapshot.portfolio_id == portfolio.id)
        .order_by(RiskSnapshot.snapshot_date.asc())
    )
    snaps = result.scalars().all()

    return [
        {
            "date": str(s.snapshot_date),
            "value": float(s.portfolio_value) if s.portfolio_value else None,
        }
        for s in snaps
    ]
