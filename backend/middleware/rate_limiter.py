"""Redis-based rate limiting middleware for SupplyChainGPT Council.

Features:
  - Redis-backed sliding window rate limiting (falls back to in-memory)
  - Per-key and per-endpoint limits
  - Rate limit headers in responses (X-RateLimit-*)
  - Separate limits for council, MCP, and general API
"""

import time
import logging
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis-based sliding window limiter
# ---------------------------------------------------------------------------
class RedisRateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self, redis_url: str = ""):
        self._redis = None
        self._redis_url = redis_url
        self._fallback = InMemoryRateLimiter()

    async def _get_redis(self):
        if self._redis is None:
            try:
                from backend.db.redis_client import get_redis
                self._redis = await get_redis()
            except Exception:
                logger.warning("Redis unavailable for rate limiting, using in-memory fallback")
        return self._redis

    async def is_limited(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        """Check if key is rate limited. Returns (is_limited, current_count)."""
        redis = await self._get_redis()
        if redis is None:
            return await self._fallback.is_limited(key, limit, window_seconds)

        try:
            now = time.time()
            window_start = now - window_seconds
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            count = results[2]
            return count > limit, count
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}, falling back to in-memory")
            return await self._fallback.is_limited(key, limit, window_seconds)


class InMemoryRateLimiter:
    """In-memory sliding window rate limiter (fallback)."""

    def __init__(self):
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def is_limited(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.time()
        timestamps = self._buckets[key]
        self._buckets[key] = [t for t in timestamps if now - t < window_seconds]
        self._buckets[key].append(now)
        count = len(self._buckets[key])
        return count > limit, count


# Singleton
_rate_limiter: RedisRateLimiter | None = None


def get_rate_limiter() -> RedisRateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter(redis_url=settings.redis_url)
    return _rate_limiter


# ---------------------------------------------------------------------------
# Endpoint-specific limits
# ---------------------------------------------------------------------------
ENDPOINT_LIMITS = {
    "/council/query": 10,       # 10/min — expensive LLM calls
    "/council/analyze": 10,
    "/council/stream": 5,       # 5/min — streaming is resource-heavy
    "/council/execute-fallback": 15,
    "/rag/query": 30,
    "/rag/agentic": 20,
    "/rag/graph": 20,
    "/rag/url-upload": 10,
}


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis sliding window."""

    SKIP_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/metrics", "/test"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Determine key and limit
        if request.url.path.startswith("/mcp/"):
            prefix = "mcp"
            api_key = request.headers.get("X-MCP-API-Key", "anon")
            limit = settings.mcp_rate_limit
        else:
            prefix = "api"
            api_key = request.headers.get("X-API-Key", "anon")
            # Check endpoint-specific limit first
            limit = ENDPOINT_LIMITS.get(request.url.path, settings.rate_limit_per_minute)

        key = f"ratelimit:{prefix}:{api_key}:{request.url.path}"
        limiter = get_rate_limiter()

        is_limited, count = await limiter.is_limited(key, limit, window_seconds=60)

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded. Please slow down.",
                    "data": {"limit": limit, "window": "60s", "current": count},
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        remaining = max(0, limit - count)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
