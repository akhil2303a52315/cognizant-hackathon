from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


def chunk_documents(docs: list[Document], chunk_size: int = None, chunk_overlap: int = None) -> list[Document]:
    chunk_size = chunk_size or settings.rag_chunk_size
    chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        doc_chunks = splitter.split_documents([doc])
        for i, chunk in enumerate(doc_chunks):
            chunk.metadata["chunk_id"] = f"{doc.metadata.get('filename', 'doc')}_{i}"
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(doc_chunks)
        chunks.extend(doc_chunks)

    logger.info(f"Chunked {len(docs)} documents into {len(chunks)} chunks")
    return chunks
