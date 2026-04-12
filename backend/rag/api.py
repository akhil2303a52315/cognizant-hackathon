from fastapi import APIRouter, UploadFile, File, HTTPException, Query as QueryParam
from pydantic import BaseModel
from typing import Optional
import uuid
import time
import logging

from backend.rag.loader import load_document, load_from_url, load_from_crawl
from backend.rag.chunker import chunk_documents
from backend.rag.vectorstore import add_documents, delete_collection, list_collections
from backend.rag.generator import generate_answer
from backend.rag.hybrid_rag import hybrid_rag_query
from backend.rag.graph_rag import graph_rag_query
from backend.db.neon import execute_query

logger = logging.getLogger(__name__)

router = APIRouter()


class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class GraphQueryRequest(BaseModel):
    query: str


class HybridQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class URLUploadRequest(BaseModel):
    url: str
    max_depth: Optional[int] = None  # None = single page scrape, int = crawl


@router.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        start = time.time()
        try:
            docs = await load_document(file.file, file.filename)
            chunks = chunk_documents(docs)
            count = await add_documents(chunks)

            doc_id = str(uuid.uuid4())
            try:
                await execute_query(
                    """INSERT INTO rag_documents (id, filename, file_type, file_size_bytes, chunk_count)
                       VALUES ($1, $2, $3, $4, $5)""",
                    doc_id, file.filename, file.filename.split(".")[-1], 0, count,
                )
            except Exception:
                pass

            results.append({
                "filename": file.filename,
                "chunks": count,
                "latency_ms": int((time.time() - start) * 1000),
                "status": "ok",
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e),
            })
    return {"results": results}


@router.post("/upload-url")
async def upload_from_url(request: URLUploadRequest):
    """Upload documents from a URL using Firecrawl (scrape or crawl)."""
    start = time.time()
    try:
        if request.max_depth is not None:
            docs = await load_from_crawl(request.url, max_depth=request.max_depth)
        else:
            docs = await load_from_url(request.url)

        if not docs:
            raise HTTPException(400, f"No content retrieved from {request.url}")

        chunks = chunk_documents(docs)
        count = await add_documents(chunks)

        doc_id = str(uuid.uuid4())
        try:
            await execute_query(
                """INSERT INTO rag_documents (id, filename, file_type, file_size_bytes, chunk_count)
                   VALUES ($1, $2, $3, $4, $5)""",
                doc_id, request.url, "url", 0, count,
            )
        except Exception:
            pass

        return {
            "url": request.url,
            "chunks": count,
            "pages": len(docs),
            "latency_ms": int((time.time() - start) * 1000),
            "status": "ok",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"URL upload failed: {e}")


@router.post("/query")
async def rag_query(request: RAGQueryRequest):
    start = time.time()
    result = await generate_answer(request.query, top_k=request.top_k)
    result["latency_ms"] = int((time.time() - start) * 1000)

    try:
        await execute_query(
            """INSERT INTO rag_queries (id, question, answer, citations, confidence, model_used, chunks_retrieved, latency_ms)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            str(uuid.uuid4()), request.query, result["answer"],
            result.get("citations", []), result.get("confidence", 0),
            result.get("model_used", ""), result.get("chunks_retrieved", 0),
            result["latency_ms"],
        )
    except Exception:
        pass

    return result


@router.get("/collections")
async def get_collections():
    collections = await list_collections()
    return {"collections": collections}


@router.delete("/collections/{name}")
async def remove_collection(name: str):
    await delete_collection(name)
    return {"status": "deleted", "collection": name}


@router.get("/documents")
async def get_documents():
    try:
        rows = await execute_query("SELECT * FROM rag_documents ORDER BY created_at DESC LIMIT 50")
        return {"documents": [dict(r) for r in rows]}
    except Exception:
        return {"documents": []}


@router.get("/stats")
async def rag_stats():
    try:
        doc_count = await execute_query("SELECT COUNT(*) as cnt FROM rag_documents")
        query_count = await execute_query("SELECT COUNT(*) as cnt FROM rag_queries")
        collections = await list_collections()
        return {
            "documents": doc_count[0]["cnt"] if doc_count else 0,
            "queries": query_count[0]["cnt"] if query_count else 0,
            "collections": len(collections),
        }
    except Exception:
        return {"documents": 0, "queries": 0, "collections": 0}


@router.post("/graph-query")
async def graph_query(request: GraphQueryRequest):
    result = await graph_rag_query(request.query)
    return result


@router.post("/hybrid-query")
async def hybrid_query(request: HybridQueryRequest):
    start = time.time()
    result = await hybrid_rag_query(request.query, top_k=request.top_k)
    result["latency_ms"] = int((time.time() - start) * 1000)
    return result


@router.get("/citations/{query_id}")
async def get_citations(query_id: str):
    try:
        row = await execute_query("SELECT citations FROM rag_queries WHERE id = $1", query_id)
        if row:
            return {"citations": row[0]["citations"]}
    except Exception:
        pass
    return {"citations": []}


@router.get("/health")
async def rag_health():
    checks = {"vectorstore": "unknown", "embedder": "unknown"}
    try:
        from backend.rag.embedder import get_embeddings
        get_embeddings()
        checks["embedder"] = "ok"
    except Exception:
        checks["embedder"] = "error"

    try:
        from backend.rag.vectorstore import get_vectorstore
        get_vectorstore()
        checks["vectorstore"] = "ok"
    except Exception:
        checks["vectorstore"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
