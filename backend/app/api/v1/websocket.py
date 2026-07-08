"""WebSocket hub — real-time price, signal, and alert fan-out.

Architecture
------------
A Redis pub/sub channel fan-out pattern is used so that multiple Uvicorn
workers (or Celery workers) can publish events that are broadcast to all
connected WebSocket clients regardless of which worker process they are
connected to.

Channels:
    realtime:prices   → price tick updates  (JSON)
    realtime:signals  → new signal events   (JSON)
    realtime:alerts   → hedge/risk alerts   (JSON)

Client message format (server → client):
    {
        "type": "price_update" | "signal" | "alert",
        "data": { ... }
    }
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Channel names (keep in sync with redis_client.py) ───────────────────────
CHANNEL_PRICES = "realtime:prices"
CHANNEL_SIGNALS = "realtime:signals"
CHANNEL_ALERTS = "realtime:alerts"

ALL_CHANNELS = [CHANNEL_PRICES, CHANNEL_SIGNALS, CHANNEL_ALERTS]


# ─── Connection manager ───────────────────────────────────────────────────────

class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        # user_id (str) → set of WebSockets
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)
        logger.debug("WS connected", extra={"user_id": user_id, "total": self.total_connections})

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        conns = self._connections.get(user_id, set())
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        logger.debug("WS disconnected", extra={"user_id": user_id, "total": self.total_connections})

    @property
    def total_connections(self) -> int:
        return sum(len(s) for s in self._connections.values())

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send *message* to **all** connected clients."""
        text = json.dumps(message)
        dead: list[tuple[str, WebSocket]] = []

        for user_id, sockets in list(self._connections.items()):
            for ws in list(sockets):
                try:
                    if ws.client_state == WebSocketState.CONNECTED:
                        await ws.send_text(text)
                except Exception:
                    dead.append((user_id, ws))

        for user_id, ws in dead:
            self.disconnect(ws, user_id)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send *message* only to a specific user's connections."""
        text = json.dumps(message)
        for ws in list(self._connections.get(user_id, set())):
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(text)
            except Exception:
                self.disconnect(ws, user_id)


manager = ConnectionManager()


# ─── Redis subscriber (started in background) ─────────────────────────────────

async def _redis_subscriber() -> None:
    """Subscribe to Redis pub/sub channels and fan-out to WebSocket clients.

    Runs as a long-lived background coroutine.  Reconnects automatically
    on transient connection errors.
    """
    while True:
        try:
            client = await aioredis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            pubsub = client.pubsub()
            await pubsub.subscribe(*ALL_CHANNELS)
            logger.info("Redis subscriber connected", extra={"channels": ALL_CHANNELS})

            async for raw in pubsub.listen():
                if raw["type"] != "message":
                    continue
                channel: str = raw["channel"]
                try:
                    data = json.loads(raw["data"])
                except (json.JSONDecodeError, TypeError):
                    continue

                if channel == CHANNEL_PRICES:
                    msg = {"type": "price_update", "data": data}
                elif channel == CHANNEL_SIGNALS:
                    msg = {"type": "signal", "data": data}
                elif channel == CHANNEL_ALERTS:
                    msg = {"type": "alert", "data": data}
                else:
                    continue

                await manager.broadcast(msg)

        except asyncio.CancelledError:
            logger.info("Redis subscriber cancelled")
            return
        except Exception as exc:
            logger.warning(
                "Redis subscriber error, reconnecting in 5 s",
                extra={"error": str(exc)},
            )
            await asyncio.sleep(5)


# ─── Background task handle ───────────────────────────────────────────────────

_subscriber_task: asyncio.Task | None = None


def start_subscriber() -> None:
    """Spawn the Redis subscriber as a background asyncio task."""
    global _subscriber_task
    if _subscriber_task is None or _subscriber_task.done():
        _subscriber_task = asyncio.get_event_loop().create_task(_redis_subscriber())


def stop_subscriber() -> None:
    """Cancel the Redis subscriber background task."""
    global _subscriber_task
    if _subscriber_task and not _subscriber_task.done():
        _subscriber_task.cancel()


# ─── Publish helpers (called by Celery workers) ───────────────────────────────

async def publish_price_update(client: aioredis.Redis, symbol: str, data: dict[str, Any]) -> None:
    """Publish a price tick to the realtime:prices channel."""
    await client.publish(CHANNEL_PRICES, json.dumps({"symbol": symbol, **data}))


async def publish_signal(client: aioredis.Redis, data: dict[str, Any]) -> None:
    """Publish a new signal to the realtime:signals channel."""
    await client.publish(CHANNEL_SIGNALS, json.dumps(data))


async def publish_alert(client: aioredis.Redis, data: dict[str, Any]) -> None:
    """Publish a risk/hedge alert to the realtime:alerts channel."""
    await client.publish(CHANNEL_ALERTS, json.dumps(data))


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time price, signal, and alert updates.

    Query params:
        token (str): JWT access token for authentication.

    The client will receive JSON messages of the form::

        {"type": "price_update" | "signal" | "alert", "data": {...}}

    The client can send ``{"type": "ping"}`` to keep the connection alive,
    and will receive ``{"type": "pong"}`` in response.
    """
    from jose import JWTError

    from app.core.security import get_subject_from_token

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = get_subject_from_token(token)
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)

    # Ensure the subscriber is running
    start_subscriber()

    try:
        # Send a welcome message
        await websocket.send_json({"type": "connected", "data": {"user_id": user_id}})

        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except TimeoutError:
                # Send a keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
            except (json.JSONDecodeError, KeyError):
                pass  # ignore malformed client messages

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user_id)
