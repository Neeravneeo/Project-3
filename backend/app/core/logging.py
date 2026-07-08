"""Structured logging configuration.

In *production* every log record is emitted as a single-line JSON object
so it can be ingested by Grafana Loki or any log-aggregation pipeline.

In *development* (default) a human-readable coloured format is used.

Usage::

    from app.core.logging import setup_logging
    setup_logging()          # call once at app startup (before imports that log)

Individual loggers are retrieved via the standard library::

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a compact JSON line."""

    LEVEL_FIELD = "level"
    RESERVED = frozenset({"message", "level", "timestamp", "logger", "module", "lineno"})

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        # Include any extra fields attached by the caller
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and key not in self.RESERVED:
                try:
                    json.dumps(value)  # only include JSON-serialisable extras
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


_DEV_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)


def setup_logging(level: int | str | None = None) -> None:
    """Configure the root logger for the application.

    Args:
        level: Override the log level (defaults to DEBUG in dev, INFO in prod).
    """
    if level is None:
        level = logging.DEBUG if settings.debug else logging.INFO

    root = logging.getLogger()
    root.setLevel(level)

    # Clear any existing handlers to avoid duplicate log lines
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.is_production:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(_DEV_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        )

    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "hpack"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging configured",
        extra={"environment": settings.app_env, "level": logging.getLevelName(level)},
    )
