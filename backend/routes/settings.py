from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_app_settings = {}
_rag_settings = {}
_mcp_settings = {}


class AppSettingsUpdate(BaseModel):
    debug: Optional[bool] = None
    log_level: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    max_debate_rounds: Optional[int] = None
    confidence_gap_threshold: Optional[float] = None


class RAGSettingsUpdate(BaseModel):
    rag_chunk_size: Optional[int] = None
    rag_chunk_overlap: Optional[int] = None
    rag_top_k: Optional[int] = None
    rag_cache_ttl: Optional[int] = None


class MCPSettingsUpdate(BaseModel):
    mcp_rate_limit: Optional[int] = None
    mcp_api_key: Optional[str] = None


@router.get("/app")
async def get_app_settings():
    return {
        "debug": settings.debug,
        "log_level": settings.log_level,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "max_debate_rounds": settings.max_debate_rounds,
        "confidence_gap_threshold": settings.confidence_gap_threshold,
    }


@router.put("/app")
async def update_app_settings(update: AppSettingsUpdate):
    if update.debug is not None:
        _app_settings["debug"] = update.debug
    if update.log_level is not None:
        _app_settings["log_level"] = update.log_level
    if update.rate_limit_per_minute is not None:
        _app_settings["rate_limit_per_minute"] = update.rate_limit_per_minute
    if update.max_debate_rounds is not None:
        _app_settings["max_debate_rounds"] = update.max_debate_rounds
    if update.confidence_gap_threshold is not None:
        _app_settings["confidence_gap_threshold"] = update.confidence_gap_threshold
    return {"status": "updated", "settings": _app_settings}


@router.get("/rag")
async def get_rag_settings():
    return {
        "rag_chunk_size": settings.rag_chunk_size,
        "rag_chunk_overlap": settings.rag_chunk_overlap,
        "rag_top_k": settings.rag_top_k,
        "rag_cache_ttl": settings.rag_cache_ttl,
    }


@router.put("/rag")
async def update_rag_settings(update: RAGSettingsUpdate):
    if update.rag_chunk_size is not None:
        _rag_settings["rag_chunk_size"] = update.rag_chunk_size
    if update.rag_chunk_overlap is not None:
        _rag_settings["rag_chunk_overlap"] = update.rag_chunk_overlap
    if update.rag_top_k is not None:
        _rag_settings["rag_top_k"] = update.rag_top_k
    if update.rag_cache_ttl is not None:
        _rag_settings["rag_cache_ttl"] = update.rag_cache_ttl
    return {"status": "updated", "settings": _rag_settings}


@router.get("/mcp")
async def get_mcp_settings():
    return {
        "mcp_rate_limit": settings.mcp_rate_limit,
        "tools_registered": True,
    }


@router.put("/mcp")
async def update_mcp_settings(update: MCPSettingsUpdate):
    if update.mcp_rate_limit is not None:
        _mcp_settings["mcp_rate_limit"] = update.mcp_rate_limit
    if update.mcp_api_key is not None:
        _mcp_settings["mcp_api_key"] = update.mcp_api_key
    return {"status": "updated", "settings": _mcp_settings}
