from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
import logging
from collections import defaultdict
from backend.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _key(self, request: Request) -> str:
        if request.url.path.startswith("/mcp/"):
            prefix = "mcp"
            key = request.headers.get("X-MCP-API-Key", "anon")
        else:
            prefix = "api"
            key = request.headers.get("X-API-Key", "anon")
        return f"{prefix}:{key}"

    def _limit(self, request: Request) -> int:
        if request.url.path.startswith("/mcp/"):
            return settings.mcp_rate_limit
        return settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/test"}:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        key = self._key(request)
        limit = self._limit(request)
        now = time.time()

        timestamps = self._buckets[key]
        self._buckets[key] = [t for t in timestamps if now - t < 60]
        self._buckets[key].append(now)

        if len(self._buckets[key]) > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "limit": limit, "window": "60s"},
            )

        return await call_next(request)
