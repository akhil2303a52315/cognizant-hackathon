"""Security middleware: prompt injection guardrails and PII redaction.

- Scans incoming queries for prompt injection patterns
- Redacts PII (SSN, email, phone, credit card) from logs and responses
- Input sanitization (length limits, control chars)
"""

import re
import logging
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt injection patterns
# ---------------------------------------------------------------------------
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+(instructions|context)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|system\|>", re.IGNORECASE),
    re.compile(r"\[SYSTEM\]", re.IGNORECASE),
    re.compile(r"disregard\s+(your|the)\s+(training|rules|guidelines)", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+are\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\s+you\s+are\s+", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
    re.compile(r"sudo\s+mode", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"override\s+safety", re.IGNORECASE),
    re.compile(r"output\s+your\s+(system|initial)\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+(system|initial)\s+prompt", re.IGNORECASE),
    re.compile(r"print\s+your\s+instructions", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

REDACTED = {
    "ssn": "[SSN_REDACTED]",
    "email": "[EMAIL_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "ip_address": "[IP_REDACTED]",
}


def detect_injection(text: str) -> tuple[bool, Optional[str]]:
    """Check text for prompt injection patterns.

    Returns (is_injection, matched_pattern_or_None).
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)
    return False, None


def redact_pii(text: str) -> str:
    """Redact PII from text, replacing with placeholders."""
    if not settings.pii_redaction_enabled:
        return text
    for pii_type, pattern in PII_PATTERNS.items():
        text = pattern.sub(REDACTED[pii_type], text)
    return text


def sanitize_input(text: str) -> str:
    """Sanitize user input: strip control chars, enforce length limit."""
    # Remove control characters except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Enforce max length
    if len(text) > settings.max_query_length:
        text = text[: settings.max_query_length]
    return text.strip()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware that scans request bodies for prompt injection and sanitizes input."""

    INJECTION_ENDPOINTS = {"/council/analyze", "/council/query", "/council/stream",
                           "/rag/query", "/rag/agentic", "/rag/graph", "/rag/hybrid",
                           "/rag/url-upload"}

    async def dispatch(self, request: Request, call_next):
        # Only check JSON body endpoints
        if request.method in ("POST", "PUT", "PATCH") and request.url.path in self.INJECTION_ENDPOINTS:
            try:
                body = await request.body()
                if body:
                    import json
                    data = json.loads(body)
                    query = data.get("query", "")
                    if query and settings.prompt_injection_guard:
                        is_injection, pattern = detect_injection(query)
                        if is_injection:
                            logger.warning(
                                f"Prompt injection blocked: path={request.url.path} "
                                f"pattern={pattern} ip={request.client.host if request.client else 'unknown'}"
                            )
                            return JSONResponse(
                                status_code=400,
                                content={
                                    "success": False,
                                    "error": "Potential prompt injection detected. Please rephrase your query.",
                                    "data": None,
                                },
                            )
                    # Sanitize query
                    if query:
                        data["query"] = sanitize_input(data["query"])
                        # Rebuild the request with sanitized body
                        from starlette.datastructures import Headers
                        new_body = json.dumps(data).encode("utf-8")
                        request._body = new_body
                        # Update content-length
                        request.headers.__dict__["_list"] = [
                            (k.lower(), v) for k, v in request.headers.__dict__.get("_list", [])
                            if k.lower() != "content-length"
                        ] + [(b"content-length", str(len(new_body)).encode())]

            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # Not JSON, skip check

        # Security headers on response
        response = await call_next(request)

        if settings.security_headers_enabled:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response
