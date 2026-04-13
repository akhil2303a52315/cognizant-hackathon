"""Base RAG class for SupplyChainGPT Council.

Wraps existing loader/chunker/embedder/vectorstore/retriever into a cohesive
BaseRAG class with document loading, chunking, embedding, hybrid retrieval,
and recency weighting. All agent-specific RAG classes inherit from this.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import BinaryIO, Optional

from langchain_core.documents import Document

from backend.rag.rag_config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS,
    DEFAULT_COLLECTION,
    RECENCY_BOOST_FACTOR,
    get_agent_profile,
)
from backend.rag.loader import load_document, load_from_url, load_from_crawl
from backend.rag.chunker import chunk_documents
from backend.rag.vectorstore import (
    add_documents as vs_add_documents,
    similarity_search,
    get_vectorstore,
)
from backend.rag.retriever import (
    vector_retrieve,
    bm25_retrieve,
    reciprocal_rank_fusion,
    hybrid_retrieve,
)
from backend.rag.context import build_context
from backend.rag.embedder import embed_query

logger = logging.getLogger(__name__)


class BaseRAG:
    """Base RAG pipeline: load → chunk → embed → store → retrieve → weight.

    Each agent domain gets a subclass with domain-specific collection and
    retrieval parameters from rag_config.AGENT_RAG_PROFILES.
    """

    def __init__(self, agent_name: str, collection: Optional[str] = None):
        self.agent_name = agent_name
        self.profile = get_agent_profile(agent_name)
        self.collection = collection or self.profile.get("collection", DEFAULT_COLLECTION)
        self.top_k = self.profile.get("top_k", 6)
        self.recency_days = self.profile.get("recency_days", 7)
        self.confidence_threshold = self.profile.get("confidence_threshold", 0.70)

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------
    async def load_and_index_file(self, file: BinaryIO, filename: str) -> dict:
        """Load a file, chunk it, and index into the vector store."""
        start = time.time()
        try:
            docs = await load_document(file, filename)
            chunks = self._chunk(docs)
            count = await vs_add_documents(chunks, collection_name=self.collection)
            latency = int((time.time() - start) * 1000)
            logger.info(f"[{self.agent_name}] Indexed {count} chunks from {filename} ({latency}ms)")
            return {"filename": filename, "chunks": count, "latency_ms": latency, "status": "ok"}
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to index {filename}: {e}")
            return {"filename": filename, "status": "error", "error": str(e)}

    async def load_and_index_url(self, url: str, max_depth: Optional[int] = None) -> dict:
        """Scrape/crawl a URL, chunk, and index."""
        start = time.time()
        try:
            if max_depth is not None:
                docs = await load_from_crawl(url, max_depth=max_depth)
            else:
                docs = await load_from_url(url)
            if not docs:
                return {"url": url, "status": "error", "error": "No content retrieved"}
            chunks = self._chunk(docs)
            count = await vs_add_documents(chunks, collection_name=self.collection)
            latency = int((time.time() - start) * 1000)
            return {"url": url, "chunks": count, "latency_ms": latency, "status": "ok"}
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to index URL {url}: {e}")
            return {"url": url, "status": "error", "error": str(e)}

    async def index_documents(self, docs: list[Document]) -> int:
        """Chunk and index pre-loaded Document objects."""
        chunks = self._chunk(docs)
        count = await vs_add_documents(chunks, collection_name=self.collection)
        logger.info(f"[{self.agent_name}] Indexed {count} chunks")
        return count

    # ------------------------------------------------------------------
    # Chunking (uses project chunker with agent-specific params)
    # ------------------------------------------------------------------
    def _chunk(self, docs: list[Document]) -> list[Document]:
        """Chunk documents with configured chunk_size/overlap."""
        return chunk_documents(
            docs,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    async def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """Hybrid retrieval: vector + BM25 → RRF fusion → recency weighting.

        Returns list of dicts with content, metadata, score.
        """
        top_k = top_k or self.top_k
        try:
            results = await hybrid_retrieve(query, top_k=top_k)
            results = self._apply_recency_weighting(results)
            return results
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Hybrid retrieval failed: {e}")
            # Fallback to vector-only
            try:
                docs = await vector_retrieve(query, top_k=top_k)
                results = [
                    {"content": d.page_content, "metadata": d.metadata, "score": d.metadata.get("relevance_score", 0)}
                    for d in docs
                ]
                results = self._apply_recency_weighting(results)
                return results
            except Exception as e2:
                logger.error(f"[{self.agent_name}] Vector fallback also failed: {e2}")
                return []

    async def vector_only_retrieve(self, query: str, top_k: Optional[int] = None) -> list[Document]:
        """Pure vector similarity search (no BM25 fusion)."""
        top_k = top_k or self.top_k
        return await vector_retrieve(query, top_k=top_k)

    # ------------------------------------------------------------------
    # Recency weighting
    # ------------------------------------------------------------------
    def _apply_recency_weighting(self, results: list[dict]) -> list[dict]:
        """Boost scores for documents newer than recency_days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.recency_days)
        for r in results:
            metadata = r.get("metadata", {})
            # Check for timestamp fields
            ts_str = metadata.get("timestamp") or metadata.get("date") or metadata.get("created_at")
            if ts_str:
                try:
                    if isinstance(ts_str, str):
                        doc_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    else:
                        doc_time = ts_str
                    if doc_time > cutoff:
                        r["score"] = r.get("score", 0) * RECENCY_BOOST_FACTOR
                        r["recency_boosted"] = True
                except (ValueError, TypeError):
                    pass
        # Re-sort by score after weighting
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------
    def build_prompt_context(self, results: list[dict], max_tokens: int = 4000) -> dict:
        """Build a formatted context string from retrieval results."""
        return build_context(results, max_tokens=max_tokens)

    # ------------------------------------------------------------------
    # Health / diagnostics
    # ------------------------------------------------------------------
    async def health_check(self) -> dict:
        """Check if the vector store and embedder are available."""
        checks = {"vectorstore": "unknown", "embedder": "unknown"}
        try:
            from backend.rag.embedder import get_embeddings
            get_embeddings()
            checks["embedder"] = "ok"
        except Exception:
            checks["embedder"] = "error"
        try:
            get_vectorstore(self.collection)
            checks["vectorstore"] = "ok"
        except Exception:
            checks["vectorstore"] = "error"
        all_ok = all(v == "ok" for v in checks.values())
        return {"agent": self.agent_name, "collection": self.collection, "status": "ok" if all_ok else "degraded", "checks": checks}
