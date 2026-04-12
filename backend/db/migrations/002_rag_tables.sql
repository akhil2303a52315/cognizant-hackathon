CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20),
    file_size_bytes BIGINT,
    chunk_count INT,
    upload_source VARCHAR(50),
    indexed_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rag_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    question TEXT NOT NULL,
    answer TEXT,
    citations JSONB,
    confidence FLOAT,
    model_used VARCHAR(100),
    chunks_retrieved INT,
    reranked BOOLEAN DEFAULT false,
    cached BOOLEAN DEFAULT false,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_queries_created ON rag_queries(created_at DESC);
