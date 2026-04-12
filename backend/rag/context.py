import logging

logger = logging.getLogger(__name__)


def build_context(chunks: list[dict], max_tokens: int = 4000) -> dict:
    context_parts = []
    citations = []
    total_chars = 0
    max_chars = max_tokens * 4

    for i, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})
        citation_id = i + 1

        citation_entry = {
            "id": citation_id,
            "source": metadata.get("filename", "unknown"),
            "page": metadata.get("page"),
            "chunk_id": metadata.get("chunk_id"),
            "score": chunk.get("score", 0),
        }
        citations.append(citation_entry)

        context_parts.append(f"[{citation_id}] {content}")
        total_chars += len(content)

        if total_chars > max_chars:
            break

    context_str = "\n\n".join(context_parts)

    return {
        "context": context_str,
        "citations": citations,
        "chunk_count": len(context_parts),
        "total_chars": total_chars,
    }
