# Day 3 Development — Agentic RAG Integration

> **Date:** Day 3 (Apr 14)
> **Focus:** Agentic RAG + Graph RAG on Neo4j integrated into all 7 agents
> **Status:** ✅ Complete

---

## Overview

Day 3 focused on building a production-grade Retrieval-Augmented Generation (RAG) pipeline with three retrieval strategies: vector search, BM25 keyword search, and Neo4j graph traversal. The hybrid RAG system combines all three with Reciprocal Rank Fusion (RRF) and is integrated into every council agent.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     AGENTIC RAG PIPELINE                         │
│                                                                   │
│  User Query                                                       │
│      │                                                            │
│      ▼                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Vector      │    │  BM25       │    │  Graph RAG   │          │
│  │  Search      │    │  Search     │    │  (Neo4j)     │          │
│  │  (Pinecone)  │    │  (Neon PG)  │    │              │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                    │
│         └──────────────────┼──────────────────┘                  │
│                            │                                      │
│                   ┌────────▼────────┐                           │
│                   │  Reciprocal     │                            │
│                   │  Rank Fusion    │                            │
│                   │  (k=60)         │                            │
│                   └────────┬────────┘                           │
│                            │                                      │
│                   ┌────────▼────────┐                           │
│                   │  Context Builder │                           │
│                   │  + Graph Context │                           │
│                   └────────┬────────┘                           │
│                            │                                      │
│                   ┌────────▼────────┐                           │
│                   │  LLM Generator   │                           │
│                   │  (with citations)│                           │
│                   └─────────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## RAG Module Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `backend/rag/api.py` | FastAPI router for RAG endpoints | `/rag/upload`, `/rag/ask`, `/rag/graph`, `/rag/hybrid` |
| `backend/rag/loader.py` | Document loading (PDF, DOCX, TXT, URL, crawl) | `load_document`, `load_from_url`, `load_from_crawl` |
| `backend/rag/chunker.py` | Recursive text splitting with overlap | `chunk_documents` |
| `backend/rag/embedder.py` | HuggingFace embeddings via API | `embed_texts`, `embed_query` |
| `backend/rag/vectorstore.py` | Pinecone vector store operations | `add_documents`, `similarity_search`, `delete_collection`, `list_collections` |
| `backend/rag/retriever.py` | Hybrid retrieval with RRF | `vector_retrieve`, `bm25_retrieve`, `hybrid_retrieve`, `reciprocal_rank_fusion` |
| `backend/rag/context.py` | Context window builder | `build_context` |
| `backend/rag/generator.py` | LLM answer generation with citations | `generate_answer` |
| `backend/rag/graph_rag.py` | Neo4j graph traversal RAG | `graph_rag_query`, `_extract_entities` |
| `backend/rag/hybrid_rag.py` | Combined vector + BM25 + graph RAG | `hybrid_rag_query` |

---

## RAG API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rag/upload` | POST | Upload document (PDF/DOCX/TXT) |
| `/rag/upload-url` | POST | Load from URL (single page) |
| `/rag/crawl` | POST | Crawl URL with Firecrawl (multi-page) |
| `/rag/ask` | POST | Vector-only RAG query |
| `/rag/graph` | POST | Graph-only RAG query (Neo4j) |
| `/rag/hybrid` | POST | Hybrid RAG (vector + BM25 + graph) |
| `/rag/collections` | GET | List all vector store collections |
| `/rag/collections/{name}` | DELETE | Delete a collection |

---

## Retrieval Strategies

### 1. Vector Search (Pinecone)
- Embedding model: HuggingFace `all-MiniLM-L6-v2` (384 dims)
- Index: `supplychaingpt` on Pinecone
- Top-K: configurable (default 5)
- Metadata filtering by source, collection, date

### 2. BM25 Keyword Search (Neon PostgreSQL)
- Full-text search using `to_tsvector` + `to_tsquery`
- Stored in `rag_document_chunks` table
- English language configuration
- Fallback if Pinecone unavailable

### 3. Graph RAG (Neo4j)
- Entity extraction from query (supplier names, locations, components)
- Cypher queries: `MATCH (s:Supplier)-[r]->(c:Component) WHERE s.name CONTAINS $name`
- Returns supplier-component relationships
- Fallback: return all suppliers if no entities matched

### 4. Hybrid RAG (Combined)
- Runs all three retrievers in parallel
- Reciprocal Rank Fusion (RRF) with k=60
- Combines vector context + graph context
- LLM generates answer with `[1]`, `[2]` citations

---

## RRF Algorithm

```python
def reciprocal_rank_fusion(result_lists, k=60):
    scores = {}
    docs = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc.metadata.get("chunk_id", hash(doc.page_content))
            scores[doc_id] += 1.0 / (k + rank + 1)
    return sorted(docs, key=scores.get, reverse=True)
```

- **k=60**: Standard RRF constant — dampens rank position impact
- Combines vector semantic similarity with BM25 exact match
- Graph results appended as additional context section

---

## Document Processing Pipeline

```
Upload (PDF/DOCX/TXT/URL)
    │
    ▼
Loader (PyPDFLoader / Docx2txtLoader / TextLoader / Firecrawl)
    │
    ▼
Chunker (RecursiveCharacterTextSplitter)
    - chunk_size: 512 (configurable)
    - chunk_overlap: 50 (configurable)
    - separators: ["\n\n", "\n", ". ", " ", ""]
    │
    ▼
Embedder (HuggingFace API)
    - Model: all-MiniLM-L6-v2
    - Batch embedding for efficiency
    │
    ▼
VectorStore (Pinecone upsert)
    - Namespace per collection
    - Metadata: source, page, chunk_id, timestamp
    │
    ▼
BM25 Index (Neon PostgreSQL INSERT)
    - Full-text search index on content column
    - Metadata stored as JSONB
```

---

## Agent Integration

Every council agent has access to the `rag_query` MCP tool:

```python
# backend/mcp/registry.py — rag_query tool
@tool("rag_query", "Query the RAG system for supply chain knowledge")
async def rag_query(params):
    query = params.get("query", "")
    mode = params.get("mode", "hybrid")  # vector | graph | hybrid
    top_k = params.get("top_k", 5)

    if mode == "hybrid":
        return await hybrid_rag_query(query, top_k)
    elif mode == "graph":
        return await graph_rag_query(query)
    else:
        return await vector_retrieve(query, top_k)
```

### Agent-RAG Usage Patterns

| Agent | RAG Use Case | Typical Queries |
|-------|-------------|-----------------|
| **Risk** | Find historical disruption patterns | "semiconductor shortage 2021 causes" |
| **Supply** | Find alternate supplier details | "TSMC alternative suppliers for 5nm chips" |
| **Logistics** | Route disruption history | "Suez Canal closure impact on shipping" |
| **Market** | Commodity trend research | "copper price forecast 2024" |
| **Finance** | Financial risk research | "supply chain insurance claim process" |
| **Brand** | Crisis communication templates | "product recall communication best practices" |
| **Moderator** | Synthesis context | Cross-references from all agents |

---

## Configuration

```python
# backend/config.py — RAG settings
rag_chunk_size: int = 512
rag_chunk_overlap: int = 50
rag_top_k: int = 5
rag_cache_ttl: int = 3600  # 1 hour cache
```

---

## Database Schema

### Neon PostgreSQL — `rag_document_chunks`

```sql
CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection VARCHAR(100),
    chunk_id VARCHAR(200),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_fts
    ON rag_document_chunks USING GIN(to_tsvector('english', content));
```

### Neo4j — Supplier Graph

```cypher
// Supplier-Component relationships
(:Supplier {name, location, tier})-[:SUPPLIES {lead_time, cost}]->(:Component {name, category})
(:Supplier)-[:DEPENDS_ON]->(:Supplier)  // Multi-tier visibility
```

---

## Testing

```bash
# Upload a document
curl -X POST http://localhost:8000/rag/upload \
  -H "X-API-Key: dev-key" \
  -F "file=@supply_chain_report.pdf"

# Ask a question (vector only)
curl -X POST http://localhost:8000/rag/ask \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "What caused the 2021 semiconductor shortage?", "top_k": 5}'

# Hybrid RAG (vector + BM25 + graph)
curl -X POST http://localhost:8000/rag/hybrid \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "TSMC alternative suppliers", "top_k": 5}'
```

---

## Key Decisions

1. **RRF over weighted merge**: Reciprocal Rank Fusion is rank-based, not score-based — avoids score normalization issues between vector cosine and BM25 TF-IDF
2. **HuggingFace over OpenAI embeddings**: Free tier, no token cost, 384-dim vectors (smaller than OpenAI 1536)
3. **Pinecone serverless**: No infrastructure management, auto-scales
4. **Graph RAG as supplement**: Neo4j provides relationship context that vector search misses (supplier → component → tier dependencies)
5. **Firecrawl for web ingestion**: Handles JS-rendered pages, converts to clean markdown before chunking
6. **Chunk size 512**: Balance between granularity and context window — smaller chunks improve retrieval precision

---

## Day 3 Deliverables ✅

- [x] Document loader (PDF, DOCX, TXT, URL, Firecrawl crawl)
- [x] Recursive text chunker with configurable size/overlap
- [x] HuggingFace embedder (batch + single query)
- [x] Pinecone vector store (upsert, search, delete, list)
- [x] BM25 full-text search on Neon PostgreSQL
- [x] Reciprocal Rank Fusion for hybrid retrieval
- [x] Neo4j Graph RAG with entity extraction
- [x] Combined hybrid RAG (vector + BM25 + graph)
- [x] LLM answer generation with citations
- [x] FastAPI router with 8 endpoints
- [x] `rag_query` MCP tool registered for all agents
- [x] Configurable chunk size, overlap, top_k, cache TTL
