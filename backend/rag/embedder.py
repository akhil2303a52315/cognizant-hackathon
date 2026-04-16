import os
import logging
import asyncio
from typing import List

logger = logging.getLogger(__name__)

_embedding_model = None


def _get_huggingface_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def _get_openai_embeddings():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    )


def get_embeddings():
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    try:
        _embedding_model = _get_huggingface_embeddings()
        logger.info("Using HuggingFace embeddings (sentence-transformers/all-MiniLM-L6-v2)")
        return _embedding_model
    except Exception as e:
        logger.warning(f"HuggingFace embeddings unavailable: {e}")

    try:
        _embedding_model = _get_openai_embeddings()
        logger.info("Using OpenAI embeddings (text-embedding-3-small)")
        return _embedding_model
    except Exception as e:
        logger.warning(f"OpenAI embeddings unavailable: {e}")

    raise RuntimeError("No embedding provider available. Install langchain-huggingface or set OPENAI_API_KEY.")


async def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embeddings()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, model.embed_documents, texts)


async def embed_query(text: str) -> List[float]:
    model = get_embeddings()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, model.embed_query, text)
