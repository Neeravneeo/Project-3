"""Async Redis client helpers.

The actual Redis connection is stored in ``app.state.redis`` during the
application lifespan (see ``main.py``).  These helpers provide a thin
typed interface on top of that connection so route handlers and domain
modules don't need to interact with the raw client directly.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


# ─── Module-level client (available for workers / scripts outside FastAPI) ─────
_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Return (or lazily create) the module-level async Redis client.

    FastAPI routes should prefer ``request.app.state.redis`` so the
    connection is shared across the application lifespan.  Celery workers
    and standalone scripts use this helper instead.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close the module-level client if it was opened."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# ─── Typed helper functions ───────────────────────────────────────────────────

async def redis_set_json(
    client: aioredis.Redis,
    key: str,
    value: Any,
    ttl_seconds: int | None = None,
) -> None:
    """Serialize *value* to JSON and store it under *key*.

    Args:
        client: The async Redis client.
        key: Redis key string.
        value: Any JSON-serialisable value.
        ttl_seconds: Optional TTL in seconds (None = no expiry).
    """
    serialized = json.dumps(value)
    if ttl_seconds is not None:
        await client.setex(key, ttl_seconds, serialized)
    else:
        await client.set(key, serialized)


async def redis_get_json(
    client: aioredis.Redis,
    key: str,
) -> Any | None:
    """Retrieve and deserialize a JSON value from Redis.

    Returns:
        The deserialized Python object, or ``None`` if the key does not exist.
    """
    raw = await client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Redis key %r contained non-JSON data", key)
        return None


async def redis_delete(client: aioredis.Redis, *keys: str) -> int:
    """Delete one or more keys. Returns the number of keys removed."""
    if not keys:
        return 0
    return await client.delete(*keys)


# ─── Standard key builders ────────────────────────────────────────────────────

def price_key(symbol: str) -> str:
    """Redis key for the latest price snapshot of a symbol."""
    return f"quote:{symbol.upper()}"


def signal_key(symbol: str, strategy: str) -> str:
    """Redis key for the latest signal for a given symbol + strategy."""
    return f"signal:{symbol.upper()}:{strategy}"


def portfolio_key(portfolio_id: str) -> str:
    """Redis key for the cached portfolio summary."""
    return f"portfolio:{portfolio_id}"
