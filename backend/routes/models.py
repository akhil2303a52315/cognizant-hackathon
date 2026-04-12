from fastapi import APIRouter
from backend.llm.router import PROVIDER_FACTORIES
import os
import time

router = APIRouter()


@router.get("/status")
async def models_status():
    providers = {}
    for name, factory in PROVIDER_FACTORIES.items():
        try:
            start = time.time()
            client = factory()
            await client.ainvoke([{"role": "user", "content": "ping"}])
            providers[name] = {"available": True, "latency_ms": int((time.time() - start) * 1000)}
        except:
            providers[name] = {"available": False, "latency_ms": None}
    return {"providers": providers}
