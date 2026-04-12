# SupplyChainGPT — RAG Pipeline Specification

Complete specification for the Retrieval-Augmented Generation pipeline: APIs, free & quality API connections, wireframing, building, tech-stack, process, workflow, and working implementation.

---

## 1. RAG Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        RAG PIPELINE ARCHITECTURE                      │
│                                                                       │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │  DOCUMENT    │    │  CHUNKING &  │    │  EMBEDDING   │            │
│  │  SOURCES     │───▶│  PROCESSING  │───▶│  & INDEXING  │            │
│  │              │    │              │    │              │            │
│  │ - SOPs       │    │ - 512 tokens │    │ - Free:      │            │
│  │ - Contracts  │    │ - 50 overlap │    │   HuggingFace│            │
│  │ - Incidents  │    │ - Metadata   │    │   Nomic      │            │
│  │ - Onboarding │    │   tagging    │    │   M2-BERT     │            │
│  │ - Policies   │    │ - Dedup      │    │ - Quality:   │            │
│  │              │    │              │    │   OpenAI v3   │            │
│  └─────────────┘    └──────────────┘    │   Cohere v3   │            │
│                                          └──────┬───────┘            │
│                                                  │                     │
│                                          ┌──────▼───────┐            │
│                                          │  VECTOR STORE │            │
│                                          │              │            │
│                                          │ - Free:      │            │
│                                          │   ChromaDB   │            │
│                                          │   Qdrant     │            │
│                                          │   Pinecone   │            │
│                                          │ - Quality:   │            │
│                                          │   Pinecone   │            │
│                                          │   Weaviate   │            │
│                                          └──────┬───────┘            │
│                                                  │                     │
│  ┌─────────────┐    ┌──────────────┐    ┌──────▼───────┐            │
│  │  LLM         │    │  CONTEXT      │    │  RETRIEVAL   │            │
│  │  GENERATION  │◀───│  CONSTRUCTION │◀───│  & RERANKING │            │
│  │              │    │              │    │              │            │
│  │ - Free:      │    │ - Top-K +    │    │ - Semantic   │            │
│  │   Groq       │    │   Rerank     │    │   search     │            │
│  │   Gemini     │    │ - Citation   │    │ - Hybrid     │            │
│  │ - Quality:   │    │   injection  │    │   (keyword + │            │
│  │   NVIDIA     │    │ - Source     │    │    vector)    │            │
│  │   DeepSeek   │    │   metadata   │    │ - Reranker:  │            │
│  └──────┬───────┘    └──────────────┘    │   Cohere     │            │
│         │                                  │   Cross-enc  │            │
│         │                                  └──────────────┘            │
│         │                                                              │
│  ┌──────▼───────┐    ┌──────────────┐                               │
│  │  RESPONSE     │    │  REDIS CACHE  │                               │
│  │  FORMATTING   │    │              │                               │
│  │              │    │ - Query hash  │                               │
│  │ - Citations   │    │ - 1h TTL     │                               │
│  │ - Confidence  │    │ - 60% cost   │                               │
│  │ - Evidence    │    │   reduction  │                               │
│  └──────────────┘    └──────────────┘                               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack

### 2.1 Core RAG Stack

| Component | Free Option | Quality Option | Selected |
|-----------|-------------|---------------|----------|
| **Embedding Model** | `nomic-embed-text-v1.5` (via Ollama/OpenRouter), `BAAI/bge-m3` (HuggingFace) | `text-embedding-3-large` (OpenAI), `embed-english-v3.0` (Cohere) | Free primary, quality fallback |
| **Vector Store** | ChromaDB (local), Qdrant (free tier 1GB) | Pinecone (free tier), Weaviate (free tier) | ChromaDB local + Pinecone cloud |
| **Chunking** | LangChain RecursiveCharacterTextSplitter | Same | RecursiveCharacterTextSplitter |
| **Retriever** | LangChain VectorStoreRetriever | LangChain EnsembleRetriever (hybrid) | Hybrid (vector + BM25) |
| **Reranker** | Cross-encoder (HuggingFace free) | Cohere Rerank (free tier: 1000/mo) | Cohere Rerank free |
| **LLM** | Groq Llama-3.3-70B, Gemini-2.0-Flash | NVIDIA Nemotron-70B, DeepSeek-R1 | Free primary, quality fallback |
| **Document Loader** | PyPDFLoader, UnstructuredIO (free) | Same | PyPDF + Unstructured |
| **Cache** | Redis (Docker local) | Upstash Redis (free tier) | Redis local |
| **Graph RAG** | Neo4j Community (Docker) | Neo4j AuraDB (free tier) | Neo4j Community |

### 2.2 Python Dependencies

```toml
# pyproject.toml [dependencies]
dependencies = [
    # Core RAG
    "langchain>=0.3",
    "langchain-community>=0.3",
    "langchain-groq>=0.2",
    "langchain-openai>=0.3",
    "langchain-google-genai>=2",
    "langchain-cohere>=0.1",
    "langchain-chroma>=0.2",
    "langchain-pinecone>=0.2",
    "langchain-qdrant>=0.1",

    # Embeddings
    "sentence-transformers>=3",      # HuggingFace local embeddings
    "torch>=2.1",                    # For local model inference

    # Document Processing
    "pypdf>=4",
    "unstructured>=0.15",
    "python-docx>=1.1",
    "openpyxl>=3.1",
    "markdown>=3.7",

    # Vector Stores
    "chromadb>=0.5",
    "pinecone-client>=5",
    "qdrant-client>=1.11",

    # Reranking
    "cohere>=5",

    # Graph RAG
    "neo4j>=5.25",
    "langchain-neo4j>=0.3",

    # Cache & DB
    "redis>=5",
    "asyncpg>=0.30",

    # API
    "fastapi>=0.115",
    "uvicorn>=0.34",
    "httpx>=0.28",

    # Utils
    "python-dotenv>=1",
    "pydantic>=2",
    "tiktoken>=0.8",
]
```

---

## 3. Free & Quality API Connections

### 3.1 Free API Keys Setup

| API | Provider | Free Tier | URL | Key Env Var |
|-----|----------|-----------|-----|-------------|
| **Embeddings** | HuggingFace Inference | 1000 req/day | https://huggingface.co/settings/tokens | `HUGGINGFACE_API_KEY` |
| **Embeddings** | Nomic (via OpenRouter) | Free models | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |
| **Embeddings** | Google AI | Free Gemini embeddings | https://aistudio.google.com/apikey | `GOOGLE_API_KEY` |
| **Vector DB** | Pinecone | 1 index, 100K vectors | https://app.pinecone.io | `PINECONE_API_KEY` |
| **Vector DB** | Qdrant | 1 cluster, 1GB | https://cloud.qdrant.io | `QDRANT_API_KEY` |
| **Reranker** | Cohere | 1000 searches/mo | https://dashboard.cohere.com | `COHERE_API_KEY` |
| **LLM** | Groq | 30 RPM, 6000 TPM | https://console.groq.com | `GROQ_API_KEY` |
| **LLM** | OpenRouter | Free models | https://openrouter.ai/keys | `OPENROUTER_API_KEY` |
| **LLM** | NVIDIA NIM | 1000 req/day | https://build.nvidia.com | `NVIDIA_API_KEY` |
| **LLM** | Google AI | 15 RPM | https://aistudio.google.com/apikey | `GOOGLE_API_KEY` |
| **Graph DB** | Neo4j AuraDB | 1 instance free | https://neo4j.com/cloud/aura | `NEO4J_URI`, `NEO4J_PASSWORD` |
| **Document Parse** | Unstructured API | 1000 pages/mo | https://unstructured.io | `UNSTRUCTURED_API_KEY` |
| **Cache** | Upstash Redis | 10K commands/day | https://upstash.com | `UPSTASH_REDIS_URL` |

### 3.2 Quality API Keys (For Production/Demo Polish)

| API | Provider | Cost | Best For | Key Env Var |
|-----|----------|------|----------|-------------|
| **Embeddings** | OpenAI `text-embedding-3-large` | $0.13/1M tokens | Highest quality embeddings | `OPENAI_API_KEY` |
| **Embeddings** | Cohere `embed-english-v3.0` | $0.10/1M tokens | Fast, high-quality English | `COHERE_API_KEY` |
| **Reranker** | Cohere Rerank v3 | $0.002/search | Best reranking quality | `COHERE_API_KEY` |
| **Vector DB** | Pinecone Standard | $70/mo | Production-scale, low latency | `PINECONE_API_KEY` |
| **LLM** | Anthropic Claude 3.5 Sonnet | $3/$15 per 1M tokens | Best synthesis quality | `ANTHROPIC_API_KEY` |

### 3.3 Embedding Model Comparison

| Model | Provider | Dimensions | Cost | Quality (MTEB) | Speed |
|-------|----------|-----------|------|----------------|-------|
| `nomic-embed-text-v1.5` | Ollama/HF | 768 | Free | 63.5 | Fast |
| `BAAI/bge-m3` | HuggingFace | 1024 | Free | 65.0 | Medium |
| `all-MiniLM-L6-v2` | HuggingFace | 384 | Free | 56.0 | Very Fast |
| `text-embedding-3-small` | OpenAI | 1536 | $0.02/1M | 62.3 | Fast |
| `text-embedding-3-large` | OpenAI | 3072 | $0.13/1M | 67.2 | Medium |
| `embed-english-v3.0` | Cohere | 1024 | $0.10/1M | 64.9 | Fast |

**Selected Strategy**: `nomic-embed-text-v1.5` (free, local) as primary, `text-embedding-3-large` (OpenAI) as quality fallback.

### 3.4 Environment Variables

```env
# === Embedding APIs ===
HUGGINGFACE_API_KEY=hf_...
OPENAI_API_KEY=sk-...              # For quality embeddings + fallback
GOOGLE_API_KEY=AIza...             # For Gemini embeddings
COHERE_API_KEY=...                 # For reranker + embeddings

# === Vector Stores ===
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=supplychaingpt
QDRANT_API_KEY=...
QDRANT_URL=https://xxx.qdrant.io

# === Graph RAG ===
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=...
# OR Neo4j AuraDB (free cloud):
# NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
# NEO4J_PASSWORD=...

# === Document Processing ===
UNSTRUCTURED_API_KEY=...

# === Cache ===
REDIS_URL=redis://localhost:6379
# OR Upstash (free cloud):
# UPSTASH_REDIS_URL=https://xxx.upstash.io
# UPSTASH_REDIS_TOKEN=...

# === LLM (for generation) ===
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
NVIDIA_API_KEY=nvapi-...

# === Database ===
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/supplychaingpt?sslmode=require
```

---

## 4. RAG Process & Workflow

### 4.1 End-to-End RAG Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE (Offline)                  │
│                                                                  │
│  1. UPLOAD          2. PARSE           3. CHUNK                  │
│  ┌─────────┐      ┌──────────┐      ┌──────────────┐          │
│  │ PDF      │─────▶│ PyPDF /  │─────▶│ Recursive    │          │
│  │ DOCX     │      │ Unstruct │      │ 512 tokens   │          │
│  │ TXT      │      │ API      │      │ 50 overlap   │          │
│  │ Markdown │      │          │      │ Metadata tag │          │
│  └─────────┘      └──────────┘      └──────┬───────┘          │
│                                            │                    │
│  4. EMBED             5. STORE                                  │
│  ┌──────────────────┐  ┌──────────────┐                       │
│  │ nomic-embed-v1.5 │  │ ChromaDB     │                       │
│  │ (free, local)    │──▶│ (local)      │                       │
│  │ OR               │  │ Pinecone     │                       │
│  │ text-embed-3-lg  │  │ (cloud free) │                       │
│  │ (quality)        │  └──────────────┘                       │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    QUERY PIPELINE (Online)                        │
│                                                                  │
│  1. USER QUERY        2. EMBED QUERY     3. RETRIEVE             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐       │
│  │ "What is our  │───▶│ Same embed   │──▶│ Vector search│       │
│  │  SOP if S1    │    │ model used   │   │ Top-K=5      │       │
│  │  is delayed?" │    │ for indexing │   │ + BM25 (hyb) │       │
│  └──────────────┘    └──────────────┘   └──────┬───────┘       │
│                                                 │                 │
│  4. RERANK            5. CONSTRUCT CTX   6. GENERATE             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐       │
│  │ Cohere Rerank│───▶│ Top-3 chunks │──▶│ Groq Llama   │       │
│  │ v3 (free)    │    │ + citations  │   │ 3.3-70B      │       │
│  │ OR Cross-enc │    │ + metadata   │   │ (free)       │       │
│  └──────────────┘    └──────────────┘   └──────┬───────┘       │
│                                                 │                 │
│  7. FORMAT            8. CACHE                                   │
│  ┌──────────────┐    ┌──────────────┐                            │
│  │ Answer +     │───▶│ Redis cache  │                            │
│  │ Citations +  │    │ 1h TTL       │                            │
│  │ Confidence   │    │ Query hash   │                            │
│  └──────────────┘    └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Detailed Process Steps

#### Step 1: Document Upload & Parsing

```python
# backend/rag/loader.py

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders import UnstructuredAPIFileLoader
from langchain_community.document_loaders import DirectoryLoader
import os

SUPPORTED_FORMATS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}

async def load_document(file_path: str) -> list:
    """Load a document and return raw pages/sections."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext in (".txt", ".md"):
        loader = TextLoader(file_path)
    else:
        # Fallback to Unstructured API for complex formats
        loader = UnstructuredAPIFileLoader(
            file_path,
            api_key=os.getenv("UNSTRUCTURED_API_KEY"),
            api_url="https://api.unstructured.io/general/v1/general",
        )

    documents = await loader.aload()
    return documents

async def load_directory(dir_path: str, glob_pattern: str = "**/*.*") -> list:
    """Load all documents from a directory."""
    loader = DirectoryLoader(
        dir_path,
        glob=glob_pattern,
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    return await loader.aload()
```

#### Step 2: Chunking & Processing

```python
# backend/rag/chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import tiktoken

CHUNK_SIZE = 512          # tokens
CHUNK_OVERLAP = 50        # tokens
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]  # Priority order

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens using tiktoken."""
    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(text))

def create_chunker() -> RecursiveCharacterTextSplitter:
    """Create the text chunker with token-based splitting."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=count_tokens,
        separators=SEPARATORS,
    )

def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into chunks with metadata preservation."""
    chunker = create_chunker()
    chunks = chunker.split_documents(documents)

    # Enrich chunks with metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source', 'unknown')}_{i}"
        chunk.metadata["chunk_index"] = i
        chunk.metadata["token_count"] = count_tokens(chunk.page_content)

    return chunks

def deduplicate_chunks(chunks: list[Document]) -> list[Document]:
    """Remove duplicate or near-duplicate chunks."""
    seen = set()
    unique = []
    for chunk in chunks:
        content_hash = hash(chunk.page_content.strip()[:200])
        if content_hash not in seen:
            seen.add(content_hash)
            unique.append(chunk)
    return unique
```

#### Step 3: Embedding & Indexing

```python
# backend/rag/embedder.py

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import CohereEmbeddings
import os

class EmbeddingRouter:
    """Route embeddings to free or quality providers."""

    def __init__(self, mode: str = "free"):
        self.mode = mode
        self._free_embedder = None
        self._quality_embedder = None

    @property
    def free_embedder(self):
        if self._free_embedder is None:
            # Option 1: Local HuggingFace model (no API needed)
            self._free_embedder = HuggingFaceEmbeddings(
                model_name="nomic-ai/nomic-embed-text-v1.5",
                model_kwargs={"trust_remote_code": True},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._free_embedder

    @property
    def quality_embedder(self):
        if self._quality_embedder is None:
            self._quality_embedder = OpenAIEmbeddings(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="text-embedding-3-large",
                dimensions=1536,  # Reduce from 3072 for cost
            )
        return self._quality_embedder

    def get_embedder(self):
        if self.mode == "quality" and os.getenv("OPENAI_API_KEY"):
            return self.quality_embedder
        return self.free_embedder

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        embedder = self.get_embedder()
        return await embedder.aembed_query(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents."""
        embedder = self.get_embedder()
        return await embedder.aembed_documents(texts)
```

#### Step 4: Vector Store Indexing

```python
# backend/rag/vectorstore.py

from langchain_chroma import Chroma
from langchain_pinecone import PineconeVectorStore
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
import os

COLLECTION_NAME = "supplychaingpt_docs"

class VectorStoreManager:
    """Manage vector store connections (free local + cloud)."""

    def __init__(self, embedding_router: EmbeddingRouter):
        self.embedder = embedding_router
        self._chroma = None
        self._pinecone = None

    @property
    def chroma(self) -> Chroma:
        """Local ChromaDB (free, no API key needed)."""
        if self._chroma is None:
            self._chroma = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=self.embedder.get_embedder(),
                persist_directory="./data/chroma_db",
            )
        return self._chroma

    @property
    def pinecone(self) -> PineconeVectorStore:
        """Pinecone cloud (free tier: 1 index, 100K vectors)."""
        if self._pinecone is None:
            from pinecone import Pinecone
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index_name = os.getenv("PINECONE_INDEX_NAME", COLLECTION_NAME)

            # Create index if not exists
            if index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=index_name,
                    dimension=768,  # nomic-embed dimensions
                    metric="cosine",
                    spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
                )

            index = pc.Index(index_name)
            self._pinecone = PineconeVectorStore(
                index=index,
                embedding=self.embedder.get_embedder(),
            )
        return self._pinecone

    def get_store(self, prefer: str = "local"):
        """Get vector store by preference."""
        if prefer == "cloud" and os.getenv("PINECONE_API_KEY"):
            return self.pinecone
        return self.chroma

    async def add_documents(self, chunks: list[Document], store: str = "local"):
        """Add document chunks to vector store."""
        vs = self.get_store(store)
        ids = await vs.aadd_documents(chunks)
        return ids

    async def similarity_search(self, query: str, k: int = 5, store: str = "local"):
        """Search for similar documents."""
        vs = self.get_store(store)
        results = await vs.asimilarity_search(query, k=k)
        return results

    async def similarity_search_with_score(self, query: str, k: int = 5, store: str = "local"):
        """Search with relevance scores."""
        vs = self.get_store(store)
        results = await vs.asimilarity_search_with_relevance_scores(query, k=k)
        return results
```

#### Step 5: Hybrid Retrieval (Vector + BM25)

```python
# backend/rag/retriever.py

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain.schema import Document
import os

class RAGRetriever:
    """Hybrid retriever: Vector search + BM25 + Reranking."""

    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vsm = vector_store_manager
        self._bm25_retriever = None

    def build_bm25_retriever(self, chunks: list[Document]):
        """Build BM25 retriever from chunks (keyword search)."""
        self._bm25_retriever = BM25Retriever.from_documents(chunks, k=5)

    def get_hybrid_retriever(self, vector_weight: float = 0.7, bm25_weight: float = 0.3):
        """Create ensemble retriever combining vector + BM25 search."""
        vector_retriever = self.vsm.chroma.as_retriever(
            search_kwargs={"k": 5}
        )

        if self._bm25_retriever is None:
            return vector_retriever  # Fallback to vector-only

        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, self._bm25_retriever],
            weights=[vector_weight, bm25_weight],
        )
        return ensemble

    def get_reranked_retriever(self, base_retriever=None):
        """Add Cohere Rerank on top of base retriever (free: 1000/mo)."""
        if base_retriever is None:
            base_retriever = self.get_hybrid_retriever()

        if os.getenv("COHERE_API_KEY"):
            compressor = CohereRerank(
                cohere_api_key=os.getenv("COHERE_API_KEY"),
                model="rerank-english-v3.0",
                top_n=3,
            )
            return ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever,
            )

        # No Cohere key — return without reranking
        return base_retriever

    async def retrieve(self, query: str, k: int = 5, rerank: bool = True) -> list[Document]:
        """Full retrieval pipeline: hybrid search + optional reranking."""
        # Check Redis cache first
        cache_key = f"rag:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await check_cache(cache_key)
        if cached:
            return cached["results"]

        if rerank:
            retriever = self.get_reranked_retriever()
        else:
            retriever = self.get_hybrid_retriever()

        results = await retriever.ainvoke(query)

        # Cache results
        await set_cache(cache_key, {"results": [r.dict() for r in results]}, ttl=3600)

        return results[:k]
```

#### Step 6: Context Construction & Citation Injection

```python
# backend/rag/context.py

from langchain.schema import Document

def construct_context(chunks: list[Document], max_tokens: int = 3000) -> dict:
    """Build context window from retrieved chunks with citations."""
    context_parts = []
    citations = []
    total_tokens = 0

    for i, chunk in enumerate(chunks):
        chunk_tokens = chunk.metadata.get("token_count", len(chunk.page_content) // 4)

        if total_tokens + chunk_tokens > max_tokens:
            break

        # Create citation reference
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", "?")
        doc_id = chunk.metadata.get("chunk_id", f"chunk_{i}")

        citation = {
            "id": doc_id,
            "source": source,
            "page": page,
            "relevance_score": chunk.metadata.get("relevance_score", None),
        }
        citations.append(citation)

        # Add chunk with citation marker
        context_parts.append(f"[{doc_id}] {chunk.page_content}")
        total_tokens += chunk_tokens

    context_text = "\n\n---\n\n".join(context_parts)

    return {
        "context": context_text,
        "citations": citations,
        "chunks_used": len(context_parts),
        "total_tokens": total_tokens,
    }
```

#### Step 7: LLM Generation with Grounding

```python
# backend/rag/generator.py

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

RAG_SYSTEM_PROMPT = """You are a Supply Chain Knowledge Assistant powered by RAG.

RULES:
1. Answer ONLY using the provided context below. Do not use external knowledge.
2. If the context does not contain enough information, say "I don't have sufficient information to answer this question."
3. Always cite the document ID in brackets [chunk_id] when referencing information.
4. Be specific and actionable — supply chain professionals need concrete answers.
5. If multiple documents provide conflicting information, note the conflict and cite both sources.
6. Structure your answer with clear sections when appropriate.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with citations):"""

class RAGGenerator:
    """Generate grounded answers using LLM + retrieved context."""

    def __init__(self):
        self._free_llm = None
        self._quality_llm = None

    @property
    def free_llm(self):
        if self._free_llm is None:
            self._free_llm = ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama-3.3-70b-versatile",
                temperature=0.2,
                max_tokens=2048,
            )
        return self._free_llm

    @property
    def quality_llm(self):
        if self._quality_llm is None:
            # NVIDIA Nemotron (free) as quality fallback
            self._quality_llm = ChatOpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.getenv("NVIDIA_API_KEY"),
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                temperature=0.2,
                max_tokens=2048,
            )
        return self._quality_llm

    async def generate(self, query: str, context_data: dict, use_quality: bool = False) -> dict:
        """Generate a grounded answer with citations."""
        llm = self.quality_llm if use_quality else self.free_llm

        prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)
        chain = prompt | llm | StrOutputParser()

        answer = await chain.ainvoke({
            "context": context_data["context"],
            "query": query,
        })

        return {
            "answer": answer,
            "citations": context_data["citations"],
            "chunks_used": context_data["chunks_used"],
            "model_used": "quality" if use_quality else "free",
            "confidence": self._estimate_confidence(context_data),
        }

    def _estimate_confidence(self, context_data: dict) -> float:
        """Estimate answer confidence based on retrieval quality."""
        citations = context_data.get("citations", [])
        if not citations:
            return 0.1

        # Average relevance score if available
        scores = [c.get("relevance_score") for c in citations if c.get("relevance_score")]
        if scores:
            return min(sum(scores) / len(scores), 1.0)

        # Heuristic: more chunks = higher confidence (capped)
        return min(0.5 + len(citations) * 0.1, 0.95)
```

---

## 5. Graph RAG (Neo4j)

### 5.1 Knowledge Graph Schema

```cypher
// Supplier nodes
CREATE CONSTRAINT supplier_id IF NOT EXISTS
FOR (s:Supplier) REQUIRE s.id IS UNIQUE;

// Component nodes
CREATE CONSTRAINT component_id IF NOT EXISTS
FOR (c:Component) REQUIRE c.id IS UNIQUE;

// Plant nodes
CREATE CONSTRAINT plant_id IF NOT EXISTS
FOR (p:Plant) REQUIRE p.id IS UNIQUE;

// Relationships
// (Supplier)-[:SUPPLIES {lead_time_days, moq, cost_per_unit}]->(Component)
// (Supplier)-[:DEPENDS_ON]->(Supplier)  // Tier-2 dependencies
// (Component)-[:USED_IN]->(Component)   // BOM relationships
// (Plant)-[:REQUIRES]->(Component)
// (Supplier)-[:LOCATED_IN]->(Region)
```

### 5.2 Graph RAG Retrieval

```python
# backend/rag/graph_rag.py

from neo4j import AsyncGraphDatabase
import os

class GraphRAGRetriever:
    """Retrieve structured knowledge from Neo4j supplier graph."""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=("neo4j", os.getenv("NEO4J_PASSWORD")),
        )

    async def get_supplier_tier_map(self, supplier_id: str, depth: int = 3) -> dict:
        """Get n-tier supplier dependency map."""
        query = """
        MATCH path = (s:Supplier {id: $supplier_id})-[:DEPENDS_ON*1..3]->(dep:Supplier)
        RETURN path
        """
        async with self.driver.session() as session:
            result = await session.run(query, supplier_id=supplier_id)
            paths = await result.data()

        return {"supplier_id": supplier_id, "dependency_paths": paths, "depth": depth}

    async def get_alternate_suppliers(self, component_id: str, excluded: list = []) -> list:
        """Find alternate suppliers for a component."""
        query = """
        MATCH (s:Supplier)-[:SUPPLIES]->(c:Component {id: $component_id})
        WHERE NOT s.id IN $excluded
        RETURN s.id, s.name, s.capability_match, s.lead_time_days, s.location, s.tier
        ORDER BY s.capability_match DESC
        LIMIT 10
        """
        async with self.driver.session() as session:
            result = await session.run(query, component_id=component_id, excluded=excluded)
            return await result.data()

    async def get_impact_analysis(self, supplier_id: str) -> dict:
        """Analyze blast radius of a supplier failure."""
        query = """
        MATCH (s:Supplier {id: $supplier_id})-[:SUPPLIES]->(c:Component)<-[:REQUIRES]-(p:Plant)
        OPTIONAL MATCH (s)-[:DEPENDS_ON*1..3]->(dep:Supplier)
        RETURN c.id AS component, c.name AS component_name,
               p.id AS plant, p.name AS plant_name,
               collect(dep.id) AS dependent_suppliers
        """
        async with self.driver.session() as session:
            result = await session.run(query, supplier_id=supplier_id)
            return await result.data()

    async def close(self):
        await self.driver.close()
```

### 5.3 Hybrid RAG (Vector + Graph)

```python
# backend/rag/hybrid_rag.py

class HybridRAG:
    """Combine vector RAG + graph RAG for comprehensive answers."""

    def __init__(self, vector_retriever: RAGRetriever, graph_retriever: GraphRAGRetriever, generator: RAGGenerator):
        self.vector = vector_retriever
        self.graph = graph_retriever
        self.generator = generator

    async def query(self, question: str, context: dict = None) -> dict:
        """Full hybrid RAG query: vector retrieval + graph context + generation."""

        # 1. Vector retrieval (document-grounded)
        chunks = await self.vector.retrieve(question, k=5, rerank=True)
        vector_context = construct_context(chunks)

        # 2. Graph retrieval (structured knowledge)
        graph_context = {}
        if context and context.get("supplier_id"):
            graph_context["tier_map"] = await self.graph.get_supplier_tier_map(context["supplier_id"])
            graph_context["impact"] = await self.graph.get_impact_analysis(context["supplier_id"])

        if context and context.get("component_id"):
            graph_context["alternates"] = await self.graph.get_alternate_suppliers(context["component_id"])

        # 3. Merge contexts
        full_context = {
            **vector_context,
            "graph_data": graph_context,
        }

        # 4. Generate answer
        answer = await self.generator.generate(question, full_context)

        return {
            "answer": answer["answer"],
            "citations": answer["citations"],
            "graph_context": graph_context,
            "confidence": answer["confidence"],
            "model_used": answer["model_used"],
        }
```

---

## 6. RAG API Endpoints

### 6.1 FastAPI Routes

```python
# backend/rag/api.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

rag_router = APIRouter(prefix="/rag", tags=["RAG"])

class RAGQueryRequest(BaseModel):
    question: str
    context: Optional[dict] = None  # supplier_id, component_id, etc.
    use_quality_model: bool = False
    rerank: bool = True

class RAGQueryResponse(BaseModel):
    answer: str
    citations: list
    graph_context: Optional[dict] = None
    confidence: float
    model_used: str
    cached: bool = False

class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_created: int
    indexed: bool

@rag_router.post("/ask", response_model=RAGQueryResponse)
async def ask_rag(request: RAGQueryRequest):
    """Ask a question using RAG pipeline."""
    # Check cache
    cache_key = f"rag_query:{hashlib.md5(request.question.encode()).hexdigest()}"
    cached = await check_cache(cache_key)
    if cached:
        return RAGQueryResponse(**cached, cached=True)

    # Run hybrid RAG
    result = await hybrid_rag.query(
        question=request.question,
        context=request.context,
    )

    # Cache result
    await set_cache(cache_key, result, ttl=3600)

    return RAGQueryResponse(**result, cached=False)

@rag_router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document into RAG pipeline."""
    # Save file
    file_path = f"./data/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Load → Chunk → Embed → Index
    documents = await load_document(file_path)
    chunks = chunk_documents(documents)
    chunks = deduplicate_chunks(chunks)
    ids = await vector_store_manager.add_documents(chunks)

    return DocumentUploadResponse(
        filename=file.filename,
        chunks_created=len(chunks),
        indexed=True,
    )

@rag_router.post("/index/directory")
async def index_directory(directory: str = "./data/knowledge_base"):
    """Index all documents in a directory."""
    documents = await load_directory(directory)
    chunks = chunk_documents(documents)
    chunks = deduplicate_chunks(chunks)
    ids = await vector_store_manager.add_documents(chunks)
    return {"documents_loaded": len(documents), "chunks_indexed": len(chunks)}

@rag_router.get("/search")
async def search_documents(query: str, k: int = 5):
    """Search documents without generation (retrieval only)."""
    results = await vector_store_manager.similarity_search_with_score(query, k=k)
    return {
        "results": [
            {"content": r[0].page_content[:200], "metadata": r[0].metadata, "score": r[1]}
            for r in results
        ],
    }

@rag_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document from the vector store."""
    # ChromaDB delete by metadata filter
    chroma = vector_store_manager.chroma
    chroma._collection.delete(where={"source": doc_id})
    return {"deleted": doc_id}

@rag_router.get("/stats")
async def rag_stats():
    """Get RAG pipeline statistics."""
    chroma = vector_store_manager.chroma
    count = chroma._collection.count()
    return {
        "total_chunks": count,
        "embedding_model": "nomic-embed-text-v1.5",
        "vector_store": "ChromaDB",
        "reranker": "Cohere Rerank v3" if os.getenv("COHERE_API_KEY") else "None",
    }
```

---

## 7. RAG Wireframes (UI)

### 7.1 RAG Panel in Council Chat Page

```
┌──────────────────────────────────────────────────────────────────┐
│  SupplyChainGPT — Council Chat                     [⚙️ Settings] │
├──────────┬───────────────────────────────────────────────────────┤
│          │                                                        │
│ History  │  ┌─────────────────────────────────────────────────┐ │
│          │  │  📚 RAG Knowledge Base                    [Upload]│ │
│ ▶ Taiwan │  │                                                     │ │
│   Crisis │  │  "What is our SOP if Supplier S1 lead time        │ │
│ ▶ Port   │  │   increases by 2 weeks?"                           │ │
│   Strike │  │                                                     │ │
│ ▶ S2     │  │  ┌───────────────────────────────────────────┐   │ │
│   Delay  │  │  │ 📄 ANSWER (Grounded with Citations)        │   │ │
│          │  │  │                                            │   │ │
│          │  │  │ Based on SOP-SC-004 [chunk_sop_12]:        │   │ │
│          │  │  │                                            │   │ │
│          │  │  │ 1. Immediate: Activate backup supplier      │   │ │
│          │  │  │    within 48h [chunk_sop_12]               │   │ │
│          │  │  │ 2. Short-term: Split demand across 2-3     │   │ │
│          │  │  │    suppliers [chunk_contract_s1_5]          │   │ │
│          │  │  │ 3. Escalate: Notify procurement lead       │   │ │
│          │  │  │    if delay > 14 days [chunk_sop_12]        │   │ │
│          │  │  │                                            │   │ │
│          │  │  │ Confidence: 87% | Sources: 3 | Model: Groq │   │ │
│          │  │  └───────────────────────────────────────────┘   │ │
│          │  │                                                     │ │
│          │  │  📎 Citations:                                      │ │
│          │  │  ┌──────────────────────────────────────────┐    │ │
│          │  │  │ [chunk_sop_12] SOP-SC-004 p.3  Score:0.94│    │ │
│          │  │  │ [chunk_contract_s1_5] Contract_S1 p.12    │    │ │
│          │  │  │ [chunk_incident_7] Incident_RPT_2025 p.2  │    │ │
│          │  │  └──────────────────────────────────────────┘    │ │
│          │  │                                                     │ │
│          │  ┌─────────────────────────────────────────────────┐ │
│          │  │  Ask a follow-up...                    [Ask RAG] │ │
│          │  └─────────────────────────────────────────────────┘ │
└──────────┴───────────────────────────────────────────────────────┘
```

### 7.2 RAG Settings Modal (in Settings Dialog)

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings — RAG Knowledge Base                          [✕] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📚 Knowledge Base                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Upload Documents                                          │ │
│  │  [Choose Files...]  Supported: PDF, DOCX, TXT, MD         │ │
│  │                                                            │ │
│  │  Indexed Documents: 24  |  Total Chunks: 1,247            │ │
│  │                                                            │ │
│  │  Document List:                                            │ │
│  │  ┌──────────────────┬────────┬─────────┬────────┐        │ │
│  │  │ Name             │ Chunks │ Indexed  │ Delete │        │ │
│  │  ├──────────────────┼────────┼─────────┼────────┤        │ │
│  │  │ SOP-SC-004.pdf  │ 45     │ ✅       │ 🗑️    │        │ │
│  │  │ Contract_S1.pdf  │ 128    │ ✅       │ 🗑️    │        │ │
│  │  │ Incident_2025.pdf│ 67     │ ✅       │ 🗑️    │        │ │
│  │  │ Onboarding.docx  │ 34     │ ✅       │ 🗑️    │        │ │
│  │  └──────────────────┴────────┴─────────┴────────┘        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🔍 Retrieval Settings                                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Embedding Model:  [nomic-embed-v1.5 ▼]  (Free)          │ │
│  │  Vector Store:     [ChromaDB (local) ▼]                   │ │
│  │  Top-K Chunks:     [5    ] slider                        │ │
│  │  Reranking:        [Cohere Rerank v3 ▼]  (Free 1000/mo) │ │ │
│  │  Hybrid Search:    [✅] Vector + BM25                     │ │
│  │  Cache TTL:        [1h  ] slider                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🤖 Generation Settings                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LLM for RAG:     [Groq Llama-3.3-70B ▼]  (Free)        │ │
│  │  Temperature:      [0.2  ] slider                         │ │
│  │  Max Tokens:       [2048 ]                                │ │
│  │  Citation Style:   [Inline brackets ▼]                   │ │
│  │  Strict Grounding: [✅] Only answer from context          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                                    [Save Settings] [Reset]      │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 RAG Upload Widget (Dashboard Page)

```
┌──────────────────────────────────────────┐
│  📚 Knowledge Base                       │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │                                   │   │
│  │    📂 Drag & drop files here     │   │
│  │       or click to upload          │   │
│  │                                   │   │
│  │    PDF, DOCX, TXT, MD            │   │
│  │    Max 10MB per file             │   │
│  │                                   │   │
│  └──────────────────────────────────┘   │
│                                          │
│  📊 Stats: 24 docs | 1,247 chunks       │
│  🔮 Embedding: nomic-embed-v1.5         │
│  💾 Store: ChromaDB (local)             │
│                                          │
│  [Index Directory]  [Clear All]          │
└──────────────────────────────────────────┘
```

---

## 8. RAG Working: End-to-End Flow

### 8.1 Ingestion Flow (Step-by-Step)

```
1. User uploads SOP-SC-004.pdf via /rag/upload endpoint
2. PyPDFLoader extracts 12 pages → 12 Document objects
3. RecursiveCharacterTextSplitter splits into 45 chunks (512 tokens, 50 overlap)
4. Each chunk gets metadata: {source: "SOP-SC-004.pdf", page: 3, chunk_id: "SOP-SC-004.pdf_12"}
5. nomic-embed-text-v1.5 embeds all 45 chunks → 45 vectors (768 dimensions each)
6. Vectors + metadata stored in ChromaDB collection "supplychaingpt_docs"
7. BM25 index rebuilt with new chunks
8. Confirmation returned: {chunks_created: 45, indexed: true}
```

### 8.2 Query Flow (Step-by-Step)

```
1. User asks: "What is our SOP if a critical supplier lead time increases by 2 weeks?"
2. Check Redis cache: cache_key = "rag_query:a1b2c3d4" → MISS
3. Embed query using nomic-embed-text-v1.5 → 768-dim vector
4. Vector search in ChromaDB: top-5 similar chunks
5. BM25 keyword search: top-5 matching chunks
6. EnsembleRetriever merges: weighted (0.7 vector + 0.3 BM25) → top-7 chunks
7. Cohere Rerank v3 reranks → top-3 most relevant chunks
8. Construct context: "[SOP-SC-004.pdf_12] ... [Contract_S1.pdf_5] ... [Incident_2025.pdf_2]"
9. Send to Groq Llama-3.3-70B with system prompt + context + query
10. LLM generates grounded answer with inline citations
11. Parse citations, estimate confidence (87%)
12. Cache result in Redis (1h TTL)
13. Return: {answer, citations, confidence: 0.87, model_used: "groq", cached: false}
```

### 8.3 Graph RAG Flow (Step-by-Step)

```
1. Council query includes context: {supplier_id: "S1"}
2. Vector RAG retrieves SOP/contract chunks about S1
3. Graph RAG queries Neo4j:
   a. get_supplier_tier_map("S1") → S1 depends on T2 (Taiwan)
   b. get_impact_analysis("S1") → affects C1, C2 at PLANT-01
   c. get_alternate_suppliers("C1") → S2 (India), S3 (Vietnam)
4. Merge vector context + graph context
5. LLM generates answer using both document knowledge + graph relationships
6. Return: {answer, citations, graph_context: {tier_map, impact, alternates}, confidence}
```

---

## 9. RAG Database Schema (Neon PostgreSQL)

```sql
-- Document registry
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20),
    file_size_bytes BIGINT,
    chunk_count INT,
    upload_source VARCHAR(50),  -- 'api', 'ui', 'directory'
    indexed_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Query audit log
CREATE TABLE rag_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    question TEXT NOT NULL,
    answer TEXT,
    citations JSONB,
    confidence FLOAT,
    model_used VARCHAR(100),
    embedding_model VARCHAR(100),
    chunks_retrieved INT,
    reranked BOOLEAN DEFAULT false,
    cached BOOLEAN DEFAULT false,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_rag_queries_session ON rag_queries(session_id);
CREATE INDEX idx_rag_queries_created ON rag_queries(created_at DESC);
```

---

## 10. RAG Caching Strategy

### 10.1 Cache Layers

| Layer | Key Pattern | TTL | Hit Rate Target |
|-------|-------------|-----|-----------------|
| **Redis query cache** | `rag_query:{hash}` | 1h | 40% |
| **Redis embedding cache** | `rag_embed:{hash}` | 24h | 60% |
| **Redis retrieval cache** | `rag_retrieve:{hash}` | 30m | 30% |
| **ChromaDB local** | Persistent | ∞ | N/A (store) |
| **Pinecone cloud** | Persistent | ∞ | N/A (store) |

### 10.2 Cache Flow

```python
async def rag_query_with_caching(question: str, context: dict = None) -> dict:
    """Full RAG query with multi-layer caching."""

    # Layer 1: Check full query cache
    query_hash = hashlib.md5(f"{question}:{context}".encode()).hexdigest()
    cached = await check_cache(f"rag_query:{query_hash}")
    if cached:
        cached["cached"] = True
        return cached

    # Layer 2: Check retrieval cache
    retrieval_hash = hashlib.md5(question.encode()).hexdigest()
    cached_retrieval = await check_cache(f"rag_retrieve:{retrieval_hash}")

    if cached_retrieval:
        chunks = [Document(**c) for c in cached_retrieval["chunks"]]
    else:
        # Full retrieval pipeline
        chunks = await retriever.retrieve(question, k=5, rerank=True)
        await set_cache(f"rag_retrieve:{retrieval_hash}", {
            "chunks": [c.dict() for c in chunks],
        }, ttl=1800)

    # Layer 3: Construct context + generate (always fresh)
    context_data = construct_context(chunks)
    answer = await generator.generate(question, context_data)

    # Cache full result
    result = {**answer, "cached": False}
    await set_cache(f"rag_query:{query_hash}", result, ttl=3600)

    return result
```

---

## 11. RAG Error Handling & Graceful Degradation

| Scenario | Fallback | Confidence Impact |
|----------|----------|-------------------|
| Embedding API down | Use pre-computed embeddings from cache | -10% |
| Vector store unavailable | Fall back to BM25-only retrieval | -20% |
| Reranker API down | Skip reranking, use raw retrieval scores | -5% |
| LLM API down | Try fallback provider (NVIDIA → Groq → Gemini) | 0% (if fallback works) |
| No relevant chunks found | Return "No relevant documents found" | Floor at 10% |
| All APIs down | Return cached answer if available, else error | N/A |

---

## 12. RAG Performance Targets

| Metric | Target |
|--------|--------|
| Document upload + indexing (10 pages) | < 15 seconds |
| Query → answer (with cache hit) | < 500ms |
| Query → answer (no cache, with rerank) | < 5 seconds |
| Query → answer (no cache, no rerank) | < 3 seconds |
| Embedding batch (50 chunks) | < 10 seconds |
| Retrieval accuracy (top-3 relevant) | > 80% |
| Citation accuracy | > 90% |
| Hallucination rate | < 5% |

---

## 13. RAG + Agent Integration

### How Each Agent Uses RAG

| Agent | RAG Use | Document Types |
|-------|---------|---------------|
| **Risk** | "What are historical precedents for this type of disruption?" | Incident reports, risk assessments |
| **Supply** | "What are the qualification requirements for alternate suppliers?" | Onboarding checklists, supplier audits |
| **Logistics** | "What routes have worked during past port congestion events?" | Logistics reports, rerouting SOPs |
| **Market** | "How did commodity prices react during similar events?" | Market analysis reports |
| **Finance** | "What are the contract SLA penalties for this supplier?" | Contracts, SLA documents |
| **Brand** | "What messaging worked during the last supply crisis?" | Past comms, brand playbooks |
| **Moderator** | "What does our SOP say about this type of incident?" | SOPs, policy documents |

### Agent RAG Tool

```python
# Each agent gets a RAG tool via MCP

register_tool(ToolDefinition(
    name="rag_query",
    description="Search internal documents (SOPs, contracts, incident reports) for grounded answers",
    agent="all",  # Available to all agents
    parameters={
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to search documents for"},
            "doc_type": {"type": "string", "enum": ["sop", "contract", "incident", "onboarding", "all"], "default": "all"},
            "k": {"type": "integer", "default": 3, "description": "Number of chunks to retrieve"},
        },
        "required": ["question"],
    },
    cache_ttl_seconds=600,
))
```

---

## 14. Complete RAG API Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/ask` | Ask a question (full RAG pipeline) |
| POST | `/rag/upload` | Upload & index a document |
| POST | `/rag/index/directory` | Index all files in a directory |
| GET | `/rag/search?query=&k=5` | Search only (no generation) |
| DELETE | `/rag/documents/{doc_id}` | Remove a document |
| GET | `/rag/stats` | Pipeline statistics |
| GET | `/rag/citations/{query_id}` | Get citations for a past query |
| POST | `/rag/graph/tier-map` | Get supplier tier dependency map |
| POST | `/rag/graph/impact` | Analyze supplier failure blast radius |
| POST | `/rag/graph/alternates` | Find alternate suppliers |
