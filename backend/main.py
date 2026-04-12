from fastapi import FastAPI
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
from backend.routes.health import router as health_router
from backend.routes.models import router as models_router
from backend.routes.council import router as council_router
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

    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# Middleware order matters: added LAST runs FIRST
# So: CORS (last) -> Auth -> ErrorHandler (first to execute)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["Health"])
app.include_router(models_router, prefix="/models", tags=["Models"])
app.include_router(council_router, prefix="/council", tags=["Council"])


@app.get("/test")
async def test_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "test.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
