"""Structured JSON logging middleware for SupplyChainGPT Council.

Provides:
  - JSON-formatted log output for production
  - Request/response logging with latency, status, path
  - Correlation ID injection
  - PII redaction in logs
"""

import json
import time
import uuid
import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.config import settings


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Emit log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        for key in ("session_id", "agent", "tool", "trace_id", "span_id",
                     "duration_ms", "status_code", "path", "method", "correlation_id"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Include exception info
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_json_logging():
    """Configure root logger with JSON formatter."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level, logging.INFO))


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request/response with structured fields."""

    SKIP_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/metrics", "/test"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = (time.monotonic() - start) * 1000

        # Redact query from log if PII redaction enabled
        query_param = ""
        if request.query_params:
            from backend.middleware.security import redact_pii
            query_param = redact_pii(str(request.query_params))

        logging.getLogger("access").info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
                "correlation_id": correlation_id,
            },
        )

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        return response
