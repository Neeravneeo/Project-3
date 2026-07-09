"""
Celery Task: News ingestion + FinBERT sentiment scoring.

Flow:
  1. Fetch RSS headlines from Yahoo Finance for watchlist symbols
  2. Store raw news in DB
  3. Score each headline with FinBERT (ProsusAI/finbert)
  4. Update Redis aggregate sentiment per ticker
"""

import asyncio
import logging
from datetime import datetime, timezone

import feedparser

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Yahoo Finance RSS URLs per ticker
def _rss_url(symbol: str) -> str:
    return f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"


@celery_app.task(name="workers.tasks.news.fetch_news_headlines", bind=True, max_retries=2)
def fetch_news_headlines(self, symbols: list[str] | None = None):
    """Fetch RSS news for all symbols, queue sentiment scoring."""
    from workers.tasks.data_refresh import DEFAULT_WATCHLIST
    symbols = symbols or DEFAULT_WATCHLIST[:15]

    async def _run():
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        headlines_inserted = 0
        async with AsyncSessionLocal() as db:
            for symbol in symbols:
                try:
                    feed = await asyncio.to_thread(feedparser.parse, _rss_url(symbol))
                    for entry in feed.entries[:5]:  # latest 5 per symbol
                        published = datetime.now(timezone.utc)
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            import time
                            published = datetime.fromtimestamp(
                                time.mktime(entry.published_parsed), tz=timezone.utc
                            )
                        await db.execute(text("""
                            INSERT INTO news_items (headline, source, url, symbols, published_at)
                            VALUES (:headline, :source, :url, :symbols, :published_at)
                            ON CONFLICT DO NOTHING
                        """), {
                            "headline":     entry.get("title", "")[:500],
                            "source":       feed.feed.get("title", "Yahoo Finance"),
                            "url":          entry.get("link", ""),
                            "symbols":      [symbol.upper()],
                            "published_at": published,
                        })
                        headlines_inserted += 1
                    await db.commit()
                except Exception as exc:
                    logger.warning("News fetch failed for %s: %s", symbol, exc)

        logger.info("News ingestion: %d headlines stored", headlines_inserted)
        return headlines_inserted

    count = asyncio.run(_run())

    # Queue sentiment scoring for unscored items
    score_unscored_headlines.delay()
    return {"headlines_stored": count}


@celery_app.task(name="workers.tasks.news.score_unscored_headlines", bind=True, max_retries=1)
def score_unscored_headlines(self):
    """
    Run FinBERT sentiment on all unscored news_items.
    FinBERT: ProsusAI/finbert — 3-class: positive, negative, neutral
    Falls back to VADER for speed if GPU not available.
    """
    async def _run():
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        import redis.asyncio as aioredis
        import json
        from app.core.config import settings

        async with AsyncSessionLocal() as db:
            # Fetch unscored items
            result = await db.execute(text("""
                SELECT id, headline, symbols
                FROM news_items
                WHERE sentiment_label IS NULL
                ORDER BY created_at DESC
                LIMIT 50
            """))
            items = result.fetchall()

        if not items:
            return 0

        # Load FinBERT (loaded once, cached in worker memory)
        scored = await asyncio.to_thread(_score_batch, [(str(r.id), r.headline) for r in items])

        r = await aioredis.from_url(settings.redis_url, decode_responses=True)
        async with AsyncSessionLocal() as db:
            for item_id, label, score in scored:
                await db.execute(text("""
                    UPDATE news_items
                    SET sentiment_label = :label, sentiment_score = :score
                    WHERE id = :id
                """), {"id": item_id, "label": label, "score": score})

            # Update Redis aggregate per symbol
            for row in items:
                for sym in (row.symbols or []):
                    key = f"sentiment:{sym.upper()}"
                    await r.setex(key, 3600, json.dumps({
                        "symbol": sym.upper(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }))
            await db.commit()
        await r.aclose()
        return len(scored)

    return asyncio.run(_run())


# ── FinBERT inference (runs in thread pool) ───────────────────────────────────
_finbert_pipeline = None

def _get_finbert():
    """Lazy-load FinBERT pipeline (cached in worker process memory)."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        try:
            from transformers import pipeline
            _finbert_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=-1,  # CPU; set to 0 for GPU
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT pipeline loaded successfully")
        except Exception as exc:
            logger.warning("FinBERT unavailable (%s), falling back to VADER", exc)
    return _finbert_pipeline


def _score_batch(items: list[tuple[str, str]]) -> list[tuple[str, str, float]]:
    """
    Score headlines with FinBERT.
    Returns list of (id, label, score).
    Falls back to VADER if FinBERT unavailable.
    """
    pipe = _get_finbert()
    results = []

    if pipe:
        headlines = [h for _, h in items]
        try:
            preds = pipe(headlines, batch_size=8)
            for (item_id, _), pred in zip(items, preds):
                label = pred["label"].lower()   # 'positive' | 'negative' | 'neutral'
                score = round(pred["score"], 4)
                results.append((item_id, label, score))
            return results
        except Exception as exc:
            logger.warning("FinBERT batch scoring failed: %s — falling back to VADER", exc)

    # VADER fallback (< 1ms per headline, no GPU needed)
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    for item_id, headline in items:
        compound = analyzer.polarity_scores(headline)["compound"]
        if compound >= 0.05:
            label, score = "positive", round(compound, 4)
        elif compound <= -0.05:
            label, score = "negative", round(abs(compound), 4)
        else:
            label, score = "neutral", round(1 - abs(compound), 4)
        results.append((item_id, label, score))
    return results
