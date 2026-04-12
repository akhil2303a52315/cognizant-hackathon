import json
import logging

logger = logging.getLogger(__name__)


async def cache_get(key: str) -> dict | None:
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
        return None


async def cache_set(key: str, value: dict, ttl: int = 3600):
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")


async def cache_delete(pattern: str):
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache delete failed: {e}")
