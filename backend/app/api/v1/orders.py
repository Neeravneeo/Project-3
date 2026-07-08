"""Orders API endpoints — list, create (paper), cancel."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import Order, Portfolio
from app.schemas import OrderCreate, OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_active_portfolio(user_id: UUID, db: AsyncSession) -> Portfolio:
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id, Portfolio.is_active == True)
        .limit(1)
    )
    portfolio = result.scalar_one_or_none()
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active portfolio found")
    return portfolio


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    order_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
) -> list[OrderResponse]:
    """Return order history for the current user's portfolio."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    query = select(Order).where(Order.portfolio_id == portfolio.id)
    if order_status:
        query = query.where(Order.status == order_status)

    query = query.order_by(Order.created_at.desc()).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    return [OrderResponse.model_validate(o) for o in orders]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    """Submit a paper order. Real broker execution is handled by the Celery worker."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    order = Order(
        portfolio_id=portfolio.id,
        symbol=body.symbol.upper(),
        side=body.side,
        order_type=body.order_type,
        quantity=body.quantity,
        limit_price=body.limit_price,
        stop_price=body.stop_price,
        strategy=body.strategy,
        signal_id=body.signal_id,
        is_paper=True,
        reason=body.reason,
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    logger.info(
        "Paper order created",
        extra={
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side,
            "quantity": float(order.quantity),
        },
    )
    return OrderResponse.model_validate(order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel an open order."""
    portfolio = await _get_active_portfolio(current_user.id, db)

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.portfolio_id == portfolio.id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status not in ("pending", "partial"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel order with status '{order.status}'",
        )

    order.status = "cancelled"
    await db.commit()
    logger.info("Order cancelled", extra={"order_id": str(order_id)})
