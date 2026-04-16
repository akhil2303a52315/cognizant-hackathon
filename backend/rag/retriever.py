from langchain_core.documents import Document
from backend.rag.vectorstore import similarity_search
from backend.config import settings
import logging
import math

logger = logging.getLogger(__name__)


async def vector_retrieve(query: str, top_k: int = None) -> list[Document]:
    top_k = top_k or settings.rag_top_k
    try:
        return await similarity_search(query, top_k=top_k)
    except Exception as e:
        logger.warning(f"Vector retrieval failed: {e}")
        return []


async def bm25_retrieve(query: str, top_k: int = None) -> list[Document]:
    top_k = top_k or settings.rag_top_k
    try:
        import re
        from backend.db.neon import execute_query
        terms = [re.sub(r"[^a-zA-Z0-9]", "", t) for t in query.split()]
        terms = [t for t in terms if t]
        if not terms:
            return []
        tsquery = " & ".join(terms)
        rows = await execute_query(
            "SELECT content, metadata FROM rag_document_chunks WHERE to_tsvector('english', content) @@ to_tsquery('english', $1) LIMIT $2",
            tsquery,
            top_k,
        )
        return [Document(page_content=r["content"], metadata=r.get("metadata", {})) for r in rows]
    except Exception as e:
        logger.warning(f"BM25 retrieval failed (DB may not have chunks table): {e}")
        return []


def reciprocal_rank_fusion(result_lists: list[list[Document]], k: int = 60) -> list[Document]:
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc.metadata.get("chunk_id", f"doc_{hash(doc.page_content)}")
            if doc_id not in scores:
                scores[doc_id] = 0
                docs[doc_id] = doc
            scores[doc_id] += 1.0 / (k + rank + 1)

    sorted_ids = sorted(scores, key=scores.get, reverse=True)
    result = []
    for doc_id in sorted_ids:
        doc = docs[doc_id]
        doc.metadata["rrf_score"] = scores[doc_id]
        result.append(doc)
    return result


async def hybrid_retrieve(query: str, top_k: int = None) -> list[dict]:
    top_k = top_k or settings.rag_top_k

    vector_results = await vector_retrieve(query, top_k=top_k)
    bm25_results = await bm25_retrieve(query, top_k=top_k)

    fused = reciprocal_rank_fusion([vector_results, bm25_results])
    fused = fused[:top_k]

    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": doc.metadata.get("rrf_score", 0),
        }
        for doc in fused
    ]
