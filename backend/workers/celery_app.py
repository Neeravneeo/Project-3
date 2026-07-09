"""
Celery Worker — background tasks for the trading platform.

CRITICAL: Order execution is NOT done here.
          Celery is only for: data refresh, signal generation,
          risk monitoring, reports, news ingestion.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "trading_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.data_refresh",
        "workers.tasks.signals",
        "workers.tasks.risk_monitor",
        "workers.tasks.news",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # fair scheduling
)

# ── Beat schedule (recurring tasks) ──────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Market data refresh — every 60 seconds during market hours
    "refresh-market-data": {
        "task": "workers.tasks.data_refresh.refresh_all_quotes",
        "schedule": settings.market_data_refresh_interval,
    },
    # Signal generation — every 5 minutes
    "generate-signals": {
        "task": "workers.tasks.signals.generate_signals_all_users",
        "schedule": settings.signal_generation_interval,
    },
    # Risk monitoring — every 60 seconds
    "monitor-risk": {
        "task": "workers.tasks.risk_monitor.monitor_all_portfolios",
        "schedule": settings.risk_monitoring_interval,
    },
    # News ingestion — every 15 minutes
    "fetch-news": {
        "task": "workers.tasks.news.fetch_news_headlines",
        "schedule": 900,  # 15 minutes
    },
    # Daily risk snapshot — at 18:00 UTC (after US market close)
    "daily-risk-snapshot": {
        "task": "workers.tasks.risk_monitor.generate_daily_snapshots",
        "schedule": crontab(hour=18, minute=0),
    },
}
