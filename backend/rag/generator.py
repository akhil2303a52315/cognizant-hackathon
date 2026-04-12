import re
import logging
from backend.rag.context import build_context
from backend.rag.retriever import hybrid_retrieve

logger = logging.getLogger(__name__)


async def generate_answer(query: str, top_k: int = 5) -> dict:
    chunks = await hybrid_retrieve(query, top_k=top_k)
    ctx = build_context(chunks)

    if not ctx["context"]:
        return {
            "answer": "No relevant documents found for this query.",
            "citations": [],
            "confidence": 0.0,
            "chunks_retrieved": 0,
        }

    prompt = f"""Answer the following question using ONLY the provided context. 
Cite your sources using [1], [2], etc. If the context doesn't contain enough information, say so.

Context:
{ctx['context']}

Question: {query}

Answer with citations:"""

    try:
        from backend.llm.router import llm_router
        messages = [
            {"role": "system", "content": "You are a supply chain research assistant. Answer using only the provided context. Always cite sources."},
            {"role": "user", "content": prompt},
        ]
        response, model = await llm_router.invoke_with_fallback("market", messages)
        answer = response.content
    except Exception as e:
        logger.error(f"RAG generation failed: {e}")
        answer = f"Generation failed: {e}"
        model = "none"

    cited_ids = _extract_citations(answer)
    matched_citations = [c for c in ctx["citations"] if c["id"] in cited_ids]
    confidence = min(len(matched_citations) / max(len(ctx["citations"]), 1), 1.0)

    return {
        "answer": answer,
        "citations": matched_citations,
        "confidence": round(confidence, 2),
        "chunks_retrieved": ctx["chunk_count"],
        "model_used": model,
    }


def _extract_citations(text: str) -> list[int]:
    return list(set(int(m) for m in re.findall(r'\[(\d+)\]', text)))
