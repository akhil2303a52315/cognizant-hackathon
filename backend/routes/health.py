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

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
