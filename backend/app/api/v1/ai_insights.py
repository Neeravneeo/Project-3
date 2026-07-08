"""AI Insights API endpoints — market summary, news, sentiment, regime.

NOTE: Full LangGraph + FinBERT + Gemini implementation is Phase 1D.
These endpoints return the correct schema with placeholder/cached data
so the frontend can be built and wired up now.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import CurrentUser
from app.core.database import get_db
from app.models import NewsItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
async def get_market_summary(current_user: CurrentUser) -> dict:
    """Return AI-generated daily market summary (Gemini, cached 1h).

    Full implementation in Phase 1D — returns placeholder text now.
    """
    return {
        "summary": "AI market summary will be powered by Gemini in Phase 1D.",
        "generated_at": None,
        "cached": False,
    }


@router.get("/news")
async def get_news(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> list[dict]:
    """Return recent news items with FinBERT sentiment scores."""
    result = await db.execute(
        select(NewsItem).order_by(desc(NewsItem.published_at)).limit(limit)
    )
    items = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "headline": item.headline,
            "source": item.source,
            "url": item.url,
            "symbols": item.symbols or [],
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "sentiment_label": item.sentiment_label,
            "sentiment_score": float(item.sentiment_score) if item.sentiment_score else None,
        }
        for item in items
    ]


@router.get("/sentiment")
async def get_sentiment(current_user: CurrentUser) -> dict:
    """Return aggregated sentiment per ticker for the last 24h.

    Full FinBERT implementation in Phase 1D.
    """
    return {
        "sentiments": [],
        "message": "Sentiment aggregation powered by FinBERT — available in Phase 1D.",
    }


@router.get("/regime")
async def get_market_regime(current_user: CurrentUser) -> dict:
    """Return the current market regime classification.

    Full classification model in Phase 1D.
    """
    return {
        "regime": "UNKNOWN",
        "confidence": None,
        "message": "Market regime detection available in Phase 1D.",
    }


@router.get("/observations")
async def get_observations(current_user: CurrentUser) -> dict:
    """Return Gemini-generated portfolio observations.

    Full implementation in Phase 1D.
    """
    return {
        "observations": [],
        "message": "Portfolio observations powered by Gemini — available in Phase 1D.",
    }
