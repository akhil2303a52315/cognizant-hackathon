import redis.asyncio as redis
import json
import os

_redis = None


async def init_redis():
    global _redis
    _redis = redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379"),
        decode_responses=True,
    )
    await _redis.ping()


async def get_redis():
    return _redis


async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def cache_set(key: str, value: dict, ttl: int = 3600):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def cache_delete(pattern: str):
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)
