from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")

from backend.config import settings
from backend.middleware.auth import AuthMiddleware
from backend.middleware.error_handler import ErrorHandlerMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.routes.health import router as health_router
from backend.routes.models import router as models_router
from backend.routes.council import router as council_router
from backend.routes.risk import router as risk_router
from backend.routes.ingest import router as ingest_router
from backend.routes.optimize import router as optimize_router
from backend.routes.settings import router as settings_router
from backend.rag.api import router as rag_router
from backend.routes.market import router as market_router
from backend.ws.server import websocket_endpoint
from fastapi.responses import FileResponse

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting SupplyChainGPT Council API...")

    try:
        from backend.db.neon import init_db
        await init_db()
        logger.info("✅ Neon PostgreSQL initialized")
    except Exception as e:
        logger.warning(f"⚠️ Neon PG not available: {e}")

    try:
        from backend.db.redis_client import init_redis
        await init_redis()
        logger.info("✅ Redis initialized")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")

    try:
        from backend.db.neo4j_client import init_neo4j_schema
        await init_neo4j_schema()
        logger.info("✅ Neo4j initialized with sample data")
    except Exception as e:
        logger.warning(f"⚠️ Neo4j not available: {e}")

    try:
        from backend.mcp.registry import register_all_tools
        register_all_tools()
        logger.info("✅ MCP tools registered")
    except Exception as e:
        logger.warning(f"⚠️ MCP tools registration failed: {e}")

    try:
        from backend.mcp.mcp_toolkit import init_all_mcp_clients
        init_all_mcp_clients()
        logger.info("✅ MCP clients initialized for all agents")
    except Exception as e:
        logger.warning(f"⚠️ MCP client initialization failed: {e}")

    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# Middleware order matters: added LAST runs FIRST
# So: CORS (last) -> RateLimit -> Auth -> ErrorHandler (first to execute)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP sub-app
from backend.mcp.server import mcp_app
app.mount("/mcp", mcp_app)

# API Routes
app.include_router(health_router, tags=["Health"])
app.include_router(models_router, prefix="/models", tags=["Models"])
app.include_router(council_router, prefix="/council", tags=["Council"])
app.include_router(risk_router, prefix="/risk", tags=["Risk"])
app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])
app.include_router(optimize_router, prefix="/optimize", tags=["Optimize"])
app.include_router(settings_router, prefix="/settings", tags=["Settings"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(market_router, tags=["Market"])

# WebSocket
app.websocket("/ws")(websocket_endpoint)


@app.get("/test")
async def test_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "test.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
