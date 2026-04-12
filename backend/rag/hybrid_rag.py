import logging
from backend.rag.retriever import hybrid_retrieve
from backend.rag.context import build_context
from backend.rag.graph_rag import graph_rag_query

logger = logging.getLogger(__name__)


async def hybrid_rag_query(query: str, top_k: int = 5) -> dict:
    vector_chunks = await hybrid_retrieve(query, top_k=top_k)
    graph_data = await graph_rag_query(query)

    vector_context = build_context(vector_chunks)

    graph_context_str = ""
    if graph_data.get("graph_results"):
        for entity, data in graph_data["graph_results"].items():
            graph_context_str += f"\n--- Graph: {entity} ---\n"
            for record in data[:5]:
                graph_context_str += f"{record}\n"

    combined_context = vector_context["context"]
    if graph_context_str:
        combined_context += f"\n\n--- Supply Chain Graph Data ---{graph_context_str}"

    try:
        from backend.llm.router import llm_router
        messages = [
            {"role": "system", "content": "You are a supply chain analyst. Use the provided context and graph data to answer. Cite sources with [1], [2] etc."},
            {"role": "user", "content": f"Context:\n{combined_context}\n\nQuestion: {query}\n\nAnswer with citations:"},
        ]
        response, model = await llm_router.invoke_with_fallback("market", messages)
        answer = response.content
    except Exception as e:
        logger.error(f"Hybrid RAG generation failed: {e}")
        answer = f"Generation failed: {e}"
        model = "none"

    return {
        "answer": answer,
        "vector_citations": vector_context["citations"],
        "graph_entities": graph_data.get("entities_found", []),
        "confidence": round(min(len(vector_context["citations"]) / max(top_k, 1), 1.0), 2),
        "chunks_retrieved": vector_context["chunk_count"],
        "model_used": model,
    }
