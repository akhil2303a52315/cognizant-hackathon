"""Comma-separated API keys from app settings (same source as .env via pydantic-settings)."""


def _split_keys(value: str, default: str) -> list[str]:
    raw = (value or "").strip() or default
    return [k.strip() for k in raw.split(",") if k.strip()]


def api_keys_list() -> list[str]:
    from backend.config import settings

    return _split_keys(settings.api_keys, "dev-key")


def mcp_api_keys_list() -> list[str]:
    from backend.config import settings

    return _split_keys(settings.mcp_api_key, "dev-mcp-key")
