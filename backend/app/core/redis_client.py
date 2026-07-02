import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        if self.redis is None:
            self.redis = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
            self.redis = None

    async def get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            await self.connect()
        return self.redis

    async def get(self, key: str) -> Optional[Any]:
        r = await self.get_redis()
        val = await r.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val

    async def set(self, key: str, value: Any, expire: int = None) -> None:
        r = await self.get_redis()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if expire:
            await r.setex(key, expire, value)
        else:
            await r.set(key, value)

    async def delete(self, key: str) -> None:
        r = await self.get_redis()
        await r.delete(key)

    async def publish(self, channel: str, message: Any) -> None:
        r = await self.get_redis()
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        await r.publish(channel, message)


redis_client = RedisClient()

async def get_redis_client() -> RedisClient:
    return redis_client
