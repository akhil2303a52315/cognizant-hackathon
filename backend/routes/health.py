from fastapi import APIRouter
from backend.db.redis_client import get_redis
from backend.db.neon import get_pool
import time

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}


@router.get("/ready")
async def ready():
    checks = {}

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["neon_postgres"] = "ok"
    except:
        checks["neon_postgres"] = "error"

    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except:
        checks["redis"] = "error"

    # MCP tools health
    try:
        from backend.mcp.registry import list_tools
        tool_count = len(list_tools())
        checks["mcp_tools"] = "ok" if tool_count > 0 else "error"
    except:
        checks["mcp_tools"] = "error"

    # MCP server scopes health
    try:
        from backend.mcp.mcp_servers import get_tool_manifest
        manifest = get_tool_manifest()
        checks["mcp_servers"] = "ok" if manifest["total_servers"] > 0 else "error"
    except:
        checks["mcp_servers"] = "error"

    # RAG health
    try:
        from backend.rag.embedder import get_embeddings
        get_embeddings()
        checks["rag_embedder"] = "ok"
    except:
        checks["rag_embedder"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
