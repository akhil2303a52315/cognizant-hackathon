from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.auth_keys import api_keys_list, mcp_api_keys_list

PUBLIC_ENDPOINTS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/test", "/metrics", "/market/ticker", "/market/risk-dashboard", "/market/brand-intel", "/market/supply-chain-stocks", "/market/commodity-prices", "/market/forex-rates"}
PUBLIC_PREFIXES = ("/market/company/",)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_ENDPOINTS or request.method == "OPTIONS" or any(request.url.path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        if request.url.path.startswith("/mcp/"):
            key = (request.headers.get("X-MCP-API-Key", "") or request.query_params.get("mcp_key", "")).strip()
            if key not in mcp_api_keys_list():
                return JSONResponse(status_code=401, content={"detail": "Invalid MCP API key"})
            return await call_next(request)

        key = (request.headers.get("X-API-Key", "") or request.query_params.get("api_key", "")).strip()
        if key not in api_keys_list():
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

        return await call_next(request)
