"""Backtesting API endpoints — run historical tests and get reports."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.schemas import (
    BacktestReportResponse,
    BacktestResultResponse,
    BacktestRunRequest,
    BacktestRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run", response_model=BacktestRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(
    request: BacktestRunRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BacktestRunResponse:
    """Queue a backtesting run using Celery."""
    # Note: Antigravity will handle the actual Celery task logic here
    # For now, we return a mock task_id
    mock_task_id = "mock-celery-task-id-1234"
    return BacktestRunResponse(task_id=mock_task_id)


@router.get("/results/{task_id}", response_model=BacktestResultResponse)
async def get_backtest_results(
    task_id: str,
    current_user: CurrentUser,
) -> BacktestResultResponse:
    """Get status and results of a backtest run."""
    # Note: Antigravity will handle fetching results from Celery backend
    # For now, we return mock results
    return BacktestResultResponse(
        status="completed",
        results={"sharpe": 1.5, "mdd": -0.15, "returns": 0.25},
    )


@router.get("/reports/{task_id}", response_model=BacktestReportResponse)
async def get_backtest_report(
    task_id: str,
    current_user: CurrentUser,
) -> BacktestReportResponse:
    """Get the URL for the generated quantstats HTML report."""
    # Note: Antigravity will handle generating and serving the report
    # For now, we return a mock URL
    return BacktestReportResponse(
        report_url=f"/static/reports/{task_id}.html"
    )
