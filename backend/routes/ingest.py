from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import uuid
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ERPIngestRequest(BaseModel):
    data: list[dict]
    source: Optional[str] = "manual"


class NewsIngestRequest(BaseModel):
    articles: list[dict]
    source: Optional[str] = "api"


class SocialIngestRequest(BaseModel):
    posts: list[dict]
    platform: Optional[str] = "twitter"


@router.post("/erp")
async def ingest_erp(request: ERPIngestRequest):
    count = len(request.data)
    try:
        from backend.db.neon import execute_query
        for row in request.data[:100]:
            await execute_query(
                """INSERT INTO ingested_erp (id, source, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.source, row,
            )
    except Exception as e:
        logger.warning(f"ERP ingest DB write failed: {e}")

    return {"status": "ok", "records_ingested": count, "source": request.source}


@router.post("/news")
async def ingest_news(request: NewsIngestRequest):
    count = len(request.articles)
    try:
        from backend.db.neon import execute_query
        for article in request.articles[:100]:
            await execute_query(
                """INSERT INTO ingested_news (id, source, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.source, article,
            )
    except Exception as e:
        logger.warning(f"News ingest DB write failed: {e}")

    return {"status": "ok", "articles_ingested": count, "source": request.source}


@router.post("/social")
async def ingest_social(request: SocialIngestRequest):
    count = len(request.posts)
    try:
        from backend.db.neon import execute_query
        for post in request.posts[:100]:
            await execute_query(
                """INSERT INTO ingested_social (id, platform, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.platform, post,
            )
    except Exception as e:
        logger.warning(f"Social ingest DB write failed: {e}")

    return {"status": "ok", "posts_ingested": count, "platform": request.platform}
