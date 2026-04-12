export interface RAGQuery {
  query: string
  top_k?: number
}

export interface RAGResponse {
  answer: string
  citations: Citation[]
  confidence: number
  model_used: string
  chunks_retrieved: number
  latency_ms: number
}

export interface Citation {
  source: string
  content: string
  score: number
  metadata?: Record<string, unknown>
}

export interface RAGDocument {
  id: string
  filename: string
  file_type: string
  file_size_bytes: number
  chunk_count: number
  created_at: string
}

export interface Collection {
  name: string
  document_count?: number
}

export interface RAGStats {
  documents: number
  queries: number
  collections: number
}

export interface URLUploadRequest {
  url: string
  max_depth?: number | null
}
