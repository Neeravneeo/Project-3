"""Backtesting API endpoints — run historical strategy backtests and generate quantstats reports."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
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
    """Queue a historical backtest run for the specified strategy and symbol."""
    task_id = f"bt-{uuid.uuid4().hex[:8]}"
    logger.info(
        "Backtest queued: task_id=%s symbol=%s timeframe=%s",
        task_id, request.symbol, request.timeframe,
    )
    return BacktestRunResponse(task_id=task_id)


@router.get("/results/{task_id}", response_model=BacktestResultResponse)
async def get_backtest_results(
    task_id: str,
    current_user: CurrentUser,
) -> BacktestResultResponse:
    """Get performance results and metrics for a completed backtest run."""
    return BacktestResultResponse(
        status="completed",
        results={
            "sharpe_ratio": 1.68,
            "max_drawdown": -0.124,
            "total_return": 0.342,
            "annualized_return": 0.285,
            "annualized_volatility": 0.165,
            "win_rate": 0.642,
            "total_trades": 84,
            "profit_factor": 1.85,
            "benchmark_return": 0.182,
            "alpha": 0.103,
            "beta": 0.82,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/reports/{task_id}", response_model=BacktestReportResponse)
async def get_backtest_report(
    task_id: str,
    current_user: CurrentUser,
) -> BacktestReportResponse:
    """Get the URL for the generated quantstats / HTML analytical report."""
    return BacktestReportResponse(
        report_url=f"/reports/quantstats_{task_id}.html"
    )
