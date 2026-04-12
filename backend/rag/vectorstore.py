import os
import logging
from langchain_core.documents import Document
from typing import Optional

logger = logging.getLogger(__name__)

_vectorstore = None
_collection_name = "supplychaingpt"


def get_vectorstore(collection_name: str = None):
    global _vectorstore, _collection_name
    _collection_name = collection_name or _collection_name

    if _vectorstore is not None:
        return _vectorstore

    try:
        _vectorstore = _get_chroma(_collection_name)
        logger.info(f"Using ChromaDB vectorstore (collection: {_collection_name})")
        return _vectorstore
    except Exception as e:
        logger.warning(f"ChromaDB unavailable: {e}")

    try:
        _vectorstore = _get_pinecone(_collection_name)
        logger.info(f"Using Pinecone vectorstore (index: {_collection_name})")
        return _vectorstore
    except Exception as e:
        logger.warning(f"Pinecone unavailable: {e}")

    raise RuntimeError("No vector store available. Install chromadb or set PINECONE_API_KEY.")


def _get_chroma(collection_name: str):
    from langchain_chroma import Chroma
    from backend.rag.embedder import get_embeddings

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data")
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )


def _get_pinecone(collection_name: str):
    from langchain_pinecone import PineconeVectorStore
    from backend.rag.embedder import get_embeddings
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY", ""))
    index = pc.Index(os.environ.get("PINECONE_INDEX_NAME", "supplychaingpt"))
    return PineconeVectorStore(
        index=index,
        embedding=get_embeddings(),
    )


async def add_documents(docs: list[Document], collection_name: str = None) -> int:
    vs = get_vectorstore(collection_name)
    ids = vs.add_documents(docs)
    logger.info(f"Added {len(ids)} documents to vectorstore")
    return len(ids)


async def similarity_search(query: str, top_k: int = 5, collection_name: str = None) -> list[Document]:
    vs = get_vectorstore(collection_name)
    results = vs.similarity_search_with_score(query, k=top_k)
    for doc, score in results:
        doc.metadata["relevance_score"] = float(score)
    return [doc for doc, _ in results]


async def delete_collection(collection_name: str = None):
    global _vectorstore
    try:
        vs = get_vectorstore(collection_name)
        vs.delete_collection()
        _vectorstore = None
        logger.info(f"Deleted collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")


async def list_collections() -> list[str]:
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data"))
        collections = client.list_collections()
        return [c.name if hasattr(c, 'name') else str(c) for c in collections]
    except Exception as e:
        logger.warning(f"List collections failed: {e}")
        return []
