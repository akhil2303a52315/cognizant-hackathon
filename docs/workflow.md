# SupplyChainGPT — Workflow Specification

Complete specification for all workflows: user journeys, system pipelines, data flows, agent orchestration, RAG pipeline, MCP execution, deployment, and operational runbooks.

---

## 1. Workflow Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       WORKFLOW ARCHITECTURE                                   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     USER WORKFLOWS                                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Council  │  │ RAG      │  │ Brand    │  │ Optimize │  │ Settings │ │  │
│  │  │ Query    │  │ Upload+  │  │ Crisis   │  │ Route    │  │ Config   │ │  │
│  │  │ Workflow │  │ Ask      │  │ Comms    │  │ Workflow │  │ Workflow │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     SYSTEM WORKFLOWS                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Council  │  │ RAG      │  │ MCP Tool │  │ LLM      │  │ Cache    │ │  │
│  │  │ Graph    │  │ Pipeline │  │ Execution│  │ Routing  │  │ Invaldn  │ │  │
│  │  │ Flow     │  │ Flow     │  │ Flow     │  │ Flow     │  │ Flow     │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     OPERATIONAL WORKFLOWS                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Deploy   │  │ Monitor  │  │ Incident │  │ Backup   │  │ Scale    │ │  │
│  │  │ Workflow │  │ Workflow │  │ Response │  │ Workflow │  │ Workflow │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. User Workflow: Council Query

### 2.1 Happy Path

```
USER                    BROWSER                  BACKEND                 DATABASES
  │                       │                        │                       │
  │  Type query           │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  POST /council/analyze │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Create session       │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │                        │  Compile graph        │
  │                       │                        │  + checkpointer       │
  │                       │                        │                       │
  │                       │  ws: council:start     │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │                       │
  │                       │                        │  ┌─────────────────┐  │
  │                       │                        │  │ Round 0: Parse  │  │
  │                       │                        │  └────────┬────────┘  │
  │                       │                        │           │            │
  │                       │                        │  ┌────────▼────────┐  │
  │                       │                        │  │ Round 1: 6     │  │
  │  ws: agent:status     │  ws: agent:status      │  │ agents parallel │  │
  │◄──────────────────────│◄───────────────────────│  │                 │  │
  │                       │                        │  │ Each calls LLM  │  │
  │  ws: agent:           │  ws: agent:            │  │ + MCP tools     │  │
  │  contribution         │  contribution          │  └────────┬────────┘  │
  │◄──────────────────────│◄───────────────────────│           │            │
  │                       │                        │           │            │
  │                       │                        │  ┌────────▼────────┐  │
  │                       │                        │  │ Debate Check    │  │
  │                       │                        │  │ Gap ≤ 20%      │  │
  │                       │                        │  └────────┬────────┘  │
  │                       │                        │           │            │
  │                       │                        │  ┌────────▼────────┐  │
  │                       │                        │  │ Synthesize      │  │
  │  ws: council:complete │  ws: council:complete  │  │ (Moderator)     │  │
  │◄──────────────────────│◄───────────────────────│  └────────┬────────┘  │
  │                       │                        │           │            │
  │                       │                        │  Update session      │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │  200 OK + result       │                       │
  │  See recommendation   │◄───────────────────────│                       │
  │◄──────────────────────│                        │                       │
  │                       │                        │                       │
  │  Click "View Fallbacks"│                       │                       │
  │──────────────────────►│                        │                       │
  │                       │  GET /council/{id}/audit│                      │
  │                       │───────────────────────►│                       │
  │                       │                        │  Query audit trail    │
  │                       │                        │──────────────────────►│
  │  View 3-tier plan     │◄───────────────────────│                       │
  │◄──────────────────────│                        │                       │
```

### 2.2 Debate Path

```
Same as above until Debate Check:

  ┌──────────────────────────────────────────────────────────────────┐
  │ Debate Check: Gap > 20%                                         │
  │                                                                  │
  │  ┌────────────────────────────────────────────────────────────┐ │
  │ │ Round 2: DEBATE                                             │ │
  │ │                                                              │ │
  │ │  1. Identify highest vs lowest confidence agents            │ │
  │ │  2. High-confidence agent CHALLENGES low-confidence agent   │ │
  │ │     ws: debate:round {round: 2, type: "challenge"}          │ │
  │ │  3. Low-confidence agent RESPONDS to challenge              │ │
  │ │     ws: debate:round {round: 2, type: "response"}           │ │
  │ │  4. Both may revise confidence scores                       │ │
  │ │  5. Check debate condition again                            │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                  │
  │  If still gap > 20% and round < 3:                              │
  │    → Round 3: Another debate round                              │
  │  Else:                                                           │
  │    → Synthesize                                                  │
  └──────────────────────────────────────────────────────────────────┘
```

### 2.3 Error Path

```
  POST /council/analyze
          │
          ├── LLM Provider Down
          │     └── Fallback chain tries next provider
          │     └── If ALL providers down: Return error output (confidence=20)
          │
          ├── MCP Tool Timeout
          │     └── Return cached result if available
          │     └── If no cache: Return "data unavailable" in agent output
          │
          ├── Database Connection Lost
          │     └── Session not saved → Return 503 Service Unavailable
          │
          ├── Rate Limit Hit
          │     └── Return 429 Too Many Requests + Retry-After header
          │
          └── Prompt Injection Detected
                └── Sanitize input → Re-process
                └── If repeated: Log security event → Return 400 Bad Request
```

---

## 3. User Workflow: RAG Upload + Ask

### 3.1 Document Upload Flow

```
USER                    BROWSER                  BACKEND                 RAG PIPELINE
  │                       │                        │                       │
  │  Drag & drop PDF      │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  POST /rag/upload      │                       │
  │                       │  (multipart/form-data) │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Validate file        │
  │                       │                        │  (type + size)       │
  │                       │                        │                       │
  │                       │                        │  Load document        │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ PyPDF2 /        │
  │                       │                        │              │ Unstructured    │
  │                       │                        │              │ Extract text    │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ Chunk text      │
  │                       │                        │              │ 512 tokens      │
  │                       │                        │              │ 50 overlap      │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ Embed chunks    │
  │                       │                        │              │ HuggingFace     │
  │                       │                        │              │ nomic-embed     │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ Store vectors   │
  │                       │                        │              │ ChromaDB /      │
  │                       │                        │              │ Pinecone        │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │                       │                        │  Register doc in PG  │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │  "24 docs indexed"    │  200 OK                │                       │
  │◄──────────────────────│◄───────────────────────│                       │
```

### 3.2 RAG Ask Flow

```
USER                    BROWSER                  BACKEND                 RAG PIPELINE
  │                       │                        │                       │
  │  "What is SOP for     │                        │                       │
  │   supplier delays?"   │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  POST /rag/ask         │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Check Redis cache    │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │                        │  ┌─── Cache HIT ──────┐
  │                       │                        │  │ Return cached      │
  │                       │                        │  │ answer immediately │
  │                       │                        │  └───────────────────┘
  │                       │                        │                       │
  │                       │                        │  ┌─── Cache MISS ─────┐
  │                       │                        │  │                    │
  │                       │                        │  │  Embed question    │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  Vector search     │
  │                       │                        │  │  (top 5 chunks)    │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  BM25 search       │
  │                       │                        │  │  (keyword match)   │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  Merge + Rerank    │
  │                       │                        │  │  (Cohere Rerank)   │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  Build context     │
  │                       │                        │  │  + citations       │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  LLM generate      │
  │                       │                        │  │  (grounded answer) │
  │                       │                        │  │───────────────────►│
  │                       │                        │  │                    │
  │                       │                        │  │  Cache result      │
  │                       │                        │  │  (Redis, TTL=1h)   │
  │                       │                        │  │───────────────────►│
  │                       │                        │  └───────────────────┘
  │                       │                        │                       │
  │  Answer + citations   │  200 OK                │                       │
  │◄──────────────────────│◄───────────────────────│                       │
```

---

## 4. User Workflow: Brand Crisis Comms

```
USER                    BROWSER                  BACKEND                 BRAND AGENT
  │                       │                        │                       │
  │  Navigate to /brand   │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  GET /brand data       │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Fetch sentiment      │
  │                       │                        │──────────────────────►│
  │  See sentiment: 62▼   │◄───────────────────────│                       │
  │◄──────────────────────│                        │                       │
  │                       │                        │                       │
  │  Click "Generate      │                        │                       │
  │   Crisis Comms"       │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  POST /council/agent/  │                       │
  │                       │  brand                 │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Brand agent runs     │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ social_sentiment │
  │                       │                        │              │ competitor_ads   │
  │                       │                        │              │ content_generate │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │                       │                        │  PII redaction on     │
  │                       │                        │  brand output         │
  │                       │                        │                       │
  │  See draft comms      │◄───────────────────────│                       │
  │◄──────────────────────│                        │                       │
  │                       │                        │                       │
  │  Edit press release   │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  (local edit only)     │                       │
  │                       │                        │                       │
  │  Click "Approve"      │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  Mark as approved      │                       │
  │                       │  (UI state only —     │                       │
  │                       │   no auto-publish)     │                       │
  │                       │                        │                       │
  │  ⚠️ Human review      │                        │                       │
  │  confirmation dialog  │                        │                       │
  │◄──────────────────────│                        │                       │
```

---

## 5. User Workflow: Route Optimization

```
USER                    BROWSER                  BACKEND                 OR-TOOLS
  │                       │                        │                       │
  │  Enter origin + dest  │                        │                       │
  │  "Shanghai → Rotterdam│                        │                       │
  │   Max lead time: 30d" │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │  POST /optimize/routes │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │  Build OR-Tools model │
  │                       │                        │──────────────────────►│
  │                       │                        │                       │
  │                       │                        │              ┌────────▼────────┐
  │                       │                        │              │ Define variables │
  │                       │                        │              │ Add constraints  │
  │                       │                        │              │ Set objective    │
  │                       │                        │              │ Solve            │
  │                       │                        │              └────────┬────────┘
  │                       │                        │                       │
  │  See route options    │◄───────────────────────│                       │
  │◄──────────────────────│                        │                       │
  │                       │                        │                       │
  │  Routes:              │                        │                       │
  │  1. Direct sea: 28d, $78K (recommended)       │                       │
  │  2. Dubai reroute: 22d, $95K                  │                       │
  │  3. Air freight: 3d, $185K                    │                       │
```

---

## 6. System Workflow: Council Graph Execution

### 6.1 Full Graph Step-by-Step

```
Step 1: INITIALIZE
  ├── Create CouncilState with query + context
  ├── Generate session_id (UUID)
  ├── Insert session into Neon PG (status=pending)
  └── Set LangGraph checkpointer thread_id = session_id

Step 2: MODERATOR PARSE (Round 0)
  ├── Moderator node receives state
  ├── Parse query type (supplier_delay, port_congestion, market_shift, etc.)
  ├── Extract context (supplier_id, component_id, region)
  ├── Increment round_number to 1
  └── Return updated state

Step 3: PARALLEL AGENT EXECUTION (Round 1)
  ├── LangGraph fan-out to all 6 agent nodes
  │
  ├── For each agent (concurrent):
  │   ├── Load system prompt for this agent
  │   ├── Load MCP tools authorized for this agent
  │   ├── Call LLM via router (primary → fallback chain)
  │   │   ├── Try primary provider
  │   │   ├── If fails: try fallback 1
  │   │   ├── If fails: try fallback 2
  │   │   └── If all fail: return error output (confidence=20)
  │   │
  │   ├── For each MCP tool call:
  │   │   ├── Check agent-tool authorization
  │   │   ├── Check sandbox rules
  │   │   ├── Check Redis cache
  │   │   ├── If cache miss: execute tool
  │   │   ├── Sanitize external content
  │   │   ├── Redact PII
  │   │   ├── Cache result in Redis
  │   │   └── Log to mcp_audit_log
  │   │
  │   ├── Parse structured output
  │   ├── Create AgentOutput (confidence, contribution, key_points, evidence)
  │   ├── Log LLM call to llm_calls table
  │   └── Stream agent:status + agent:contribution via WebSocket
  │
  └── LangGraph fan-in: collect all 6 outputs into state

Step 4: DEBATE CONDITION CHECK
  ├── Calculate confidence gap (max - min)
  ├── If gap > 20% AND round < 3: → DEBATE
  ├── If any agent confidence < 30%: → SELF-REFLECT
  ├── If round ≥ 3: → SYNTHESIZE
  └── Else: → SYNTHESIZE

Step 5: DEBATE ROUND (if triggered)
  ├── Identify challenger (highest confidence) and challenged (lowest)
  ├── Generate challenge prompt for challenger
  ├── Challenger calls LLM → returns challenge_points + evidence
  ├── Generate response prompt for challenged
  ├── Challenged calls LLM → returns responses + revised_confidence
  ├── Score debate round
  ├── Log to debate_history table
  ├── Stream debate:round via WebSocket
  ├── Increment round_number
  └── Return to Step 4 (debate condition check)

Step 5b: SELF-REFLECTION (if triggered)
  ├── For each low-confidence agent (< 30%):
  │   ├── Re-query LLM with other agents' context
  │   ├── Cap confidence boost at +15 (max 95%)
  │   └── Update agent output
  └── Return to Step 4

Step 6: SYNTHESIZE
  ├── Moderator node receives all outputs + debate history
  ├── Calculate weighted confidence average
  ├── Call LLM (moderator routing) with synthesis prompt
  ├── Parse recommendation + fallback_options + evidence
  ├── Generate Monte Carlo simulation (10K scenarios)
  ├── Generate 30/60/90-day predictions
  ├── PII redaction on Brand Agent output
  ├── LlamaGuard classification on final output
  ├── Update state: recommendation, confidence, fallback_options
  └── Stream council:complete via WebSocket

Step 7: PERSIST & RETURN
  ├── Update council_sessions table (status=complete)
  ├── Insert agent_outputs rows
  ├── Insert debate_history rows (if any)
  ├── Insert evidence rows
  ├── Insert llm_calls rows
  ├── Save checkpoint to Neon PG via LangGraph
  └── Return CouncilAnalyzeResponse to client
```

---

## 7. System Workflow: RAG Pipeline

### 7.1 Ingestion Pipeline

```
INPUT: File (PDF/DOCX/TXT/XLSX/CSV/MD)
  │
  ├── Step 1: VALIDATE
  │   ├── Check file extension against whitelist
  │   ├── Check MIME type
  │   ├── Check file size ≤ 50MB
  │   └── Reject if invalid → 422 Unprocessable Entity
  │
  ├── Step 2: EXTRACT
  │   ├── PDF → PyPDF2 or Unstructured
  │   ├── DOCX → python-docx
  │   ├── TXT → Direct read
  │   ├── XLSX → openpyxl
  │   ├── CSV → pandas
  │   └── MD → markdown library
  │
  ├── Step 3: CHUNK
  │   ├── Split text into 512-token chunks
  │   ├── 50-token overlap between chunks
  │   ├── Attach metadata: {source, page, chunk_id, token_count}
  │   ├── Deduplicate near-identical chunks
  │   └── Result: List[Document] with chunk metadata
  │
  ├── Step 4: EMBED
  │   ├── Free: HuggingFace nomic-embed-text-v1.5 (768d)
  │   ├── Quality: OpenAI text-embedding-3-small (1536d)
  │   ├── Batch embed all chunks
  │   └── Result: List[Document] with embedding vectors
  │
  ├── Step 5: STORE
  │   ├── Primary: ChromaDB (local, unlimited)
  │   ├── Cloud: Pinecone (free tier, 100K vectors)
  │   ├── Collection: supplychaingpt_docs
  │   └── Upsert vectors + metadata
  │
  ├── Step 6: REGISTER
  │   ├── Insert into rag_documents table (Neon PG)
  │   ├── Record: filename, file_type, chunk_count, upload_source
  │   └── Return doc_id to client
  │
  └── OUTPUT: {doc_id, chunk_count, status: "indexed"}
```

### 7.2 Query Pipeline

```
INPUT: Question (string)
  │
  ├── Step 1: CACHE CHECK
  │   ├── Hash question → Redis key
  │   ├── If HIT: Return cached answer (latency < 50ms)
  │   └── If MISS: Continue pipeline
  │
  ├── Step 2: EMBED QUESTION
  │   ├── Same model as ingestion (nomic-embed-text-v1.5)
  │   └── Result: question_embedding (768d vector)
  │
  ├── Step 3: VECTOR SEARCH
  │   ├── Query ChromaDB/Pinecone with question_embedding
  │   ├── top_k = 5 (configurable)
  │   ├── Filter by metadata if context provided
  │   └── Result: top 5 chunks by cosine similarity
  │
  ├── Step 4: BM25 SEARCH
  │   ├── Keyword-based search on same collection
  │   ├── top_k = 5
  │   └── Result: top 5 chunks by BM25 score
  │
  ├── Step 5: MERGE + RERANK
  │   ├── Combine vector + BM25 results (Reciprocal Rank Fusion)
  │   ├── Deduplicate overlapping chunks
  │   ├── Cohere Rerank: re-score by semantic relevance
  │   ├── Return top 5 reranked chunks
  │   └── Result: List[Document] sorted by relevance
  │
  ├── Step 6: BUILD CONTEXT
  │   ├── Concatenate top chunks with source citations
  │   ├── Format: [Source: doc.pdf, Page 3] chunk text...
  │   ├── Respect max_tokens limit (3000)
  │   └── Result: context_string + citations list
  │
  ├── Step 7: GENERATE ANSWER
  │   ├── LLM call with: system_prompt + context + question
  │   ├── System prompt enforces grounded answers
  │   ├── Must cite document IDs in response
  │   ├── If insufficient context: say "insufficient information"
  │   └── Result: answer_string + confidence
  │
  ├── Step 8: GRAPH RAG (optional)
  │   ├── If question involves supplier relationships:
  │   │   ├── Query Neo4j for tier map / impact / alternates
  │   │   ├── Merge graph context with vector context
  │   │   └── Re-generate answer with graph evidence
  │   └── Skip if not relevant
  │
  ├── Step 9: PII REDACTION
  │   ├── Apply standard PII redaction on answer
  │   └── Result: clean answer
  │
  ├── Step 10: CACHE + LOG
  │   ├── Cache answer in Redis (TTL = 1 hour)
  │   ├── Log query to rag_queries table (Neon PG)
  │   └── Record: question, answer, citations, confidence, model, latency
  │
  └── OUTPUT: {answer, citations, graph_context?, confidence, model_used, cached}
```

---

## 8. System Workflow: MCP Tool Execution

```
INPUT: {agent, tool, params}
  │
  ├── Step 1: AUTHENTICATE
  │   ├── Validate MCP API key
  │   └── Reject if invalid → 401
  │
  ├── Step 2: AUTHORIZE
  │   ├── Check agent-tool mapping (AGENT_TOOL_MAP)
  │   ├── If tool not allowed for agent → 403 Forbidden
  │   └── If authorized: continue
  │
  ├── Step 3: SANDBOX CHECK
  │   ├── Validate Cypher queries (read-only)
  │   ├── Validate SQL queries (SELECT only)
  │   ├── Validate parameter lengths
  │   ├── Block injection patterns in params
  │   └── If violation → 400 Bad Request + log security event
  │
  ├── Step 4: CACHE CHECK
  │   ├── Generate cache key: {agent}:{tool}:{hash(params)}
  │   ├── Check Redis for cached result
  │   ├── If HIT: Return cached result (log was_cached=true)
  │   └── If MISS: Continue to execution
  │
  ├── Step 5: EXECUTE TOOL
  │   ├── Call external API / database / computation
  │   ├── Apply timeout (5 seconds default)
  │   ├── If timeout: Return cached data if available, else error
  │   └── Result: raw_tool_output
  │
  ├── Step 6: SANITIZE OUTPUT
  │   ├── Strip prompt injection patterns → [FILTERED]
  │   ├── Redact PII (email, phone, CC, SSN, API keys)
  │   ├── Brand agent: strict redaction (includes IP addresses)
  │   └── Result: clean_tool_output
  │
  ├── Step 7: CACHE RESULT
  │   ├── Store in Redis with TTL from SANDBOX_RULES
  │   ├── Write tools (insurance_claim): TTL = 0 (no cache)
  │   └── Read tools: TTL = 900–3600 seconds
  │
  ├── Step 8: AUDIT LOG
  │   ├── Insert into mcp_audit_log (Neon PG)
  │   ├── Record: agent, tool, params, result_summary, latency, was_cached
  │   └── If sandbox violations: log to security_audit_log
  │
  └── OUTPUT: {result: clean_tool_output, cached: bool, latency_ms: int}
```

---

## 9. System Workflow: LLM Routing + Fallback

```
INPUT: {agent, messages[]}
  │
  ├── Step 1: LOOKUP ROUTING TABLE
  │   ├── Get primary model for agent
  │   ├── Get fallback chain [fb1, fb2, fb3]
  │   └── Example: risk → primary: groq:llama-3.3-70b, fallbacks: [nvidia, openrouter, google]
  │
  ├── Step 2: TRY PRIMARY
  │   ├── Get or create LLM client for provider:model
  │   ├── Call client.ainvoke(messages)
  │   ├── If success: Return (response, model_info)
  │   ├── If error: Log warning, try fallback
  │   └── Track: latency_ms, input_tokens, output_tokens
  │
  ├── Step 3: TRY FALLBACK 1
  │   ├── Same process with fb1 provider:model
  │   ├── If success: Return (response, model_info) + was_fallback=true
  │   └── If error: Continue to fb2
  │
  ├── Step 4: TRY FALLBACK 2
  │   ├── Same process with fb2
  │   └── If error: Continue to fb3
  │
  ├── Step 5: TRY FALLBACK 3
  │   ├── Same process with fb3
  │   └── If error: Raise RuntimeError("All LLM providers failed")
  │
  ├── Step 6: LOG LLM CALL
  │   ├── Insert into llm_calls table
  │   ├── Record: agent, provider, model, tokens, latency, was_fallback
  │   └── Track in LangSmith trace
  │
  └── OUTPUT: (llm_response, model_info_string)
```

---

## 10. System Workflow: Cache Invalidation

```
TRIGGER: Document deleted, settings changed, TTL expired
  │
  ├── Document Delete (DELETE /rag/documents/{doc_id})
  │   ├── Remove chunks from ChromaDB/Pinecone
  │   ├── Delete from rag_documents table
  │   ├── Invalidate Redis keys matching rag:query:*
  │   └── Result: Document + all associated cache entries removed
  │
  ├── Settings Update (PUT /settings)
  │   ├── Update in-memory config
  │   ├── Persist to Neon PG
  │   ├── Invalidate all Redis cache (flushdb or pattern delete)
  │   └── Result: Fresh data on next request
  │
  ├── TTL Expiry (automatic)
  │   ├── Redis automatically evicts expired keys
  │   ├── RAG cache: 3600s (1 hour)
  │   ├── MCP cache: 900–3600s (15min–1hour, per tool)
  │   └── Result: Next request fetches fresh data
  │
  └── Manual Cache Clear
      ├── DELETE /settings/cache (admin endpoint)
      ├── Flush all Redis keys matching pattern
      └── Result: Clean cache state
```

---

## 11. Operational Workflow: Deployment

```
PRE-DEPLOY CHECKS
  │
  ├── Step 1: VERIFY TESTS PASS
  │   ├── pytest -v (backend)
  │   ├── npm run test (frontend)
  │   ├── npx playwright test (E2E)
  │   └── All green? → Continue
  │
  ├── Step 2: BUILD DOCKER IMAGES
  │   ├── docker build -t supplychaingpt-api ./backend
  │   ├── docker build -t supplychaingpt-web ./frontend
  │   └── docker compose build
  │
  ├── Step 3: SET UP PRODUCTION DATABASE
  │   ├── Create Neon PostgreSQL database
  │   ├── Run migrations: 001_initial.sql, 002_rag_tables.sql, 003_mcp_audit.sql
  │   ├── Verify schema with \dt
  │   └── Seed Neo4j with supplier graph
  │
  ├── Step 4: CONFIGURE ENVIRONMENT
  │   ├── Set all API keys in production .env
  │   ├── Set CORS_ORIGINS to production domain
  │   ├── Set API_KEYS to production keys (not dev-key)
  │   ├── Set REDIS_URL to production Redis (Upstash)
  │   └── Verify all keys with /ready endpoint
  │
  ├── Step 5: DEPLOY
  │   ├── Push to cloud platform (Render/Railway/Fly.io)
  │   ├── Or: docker compose up -d on VPS
  │   ├── Verify health: curl https://api.example.com/health
  │   └── Verify ready: curl https://api.example.com/ready
  │
  ├── Step 6: SMOKE TEST
  │   ├── POST /council/analyze with test query
  │   ├── POST /rag/ask with test question
  │   ├── GET /models/status — verify providers
  │   ├── GET /mcp/tools — verify tool count
  │   └── All pass? → Deploy complete
  │
  └── Step 7: MONITOR
      ├── Watch LangSmith traces for errors
      ├── Watch Neon PG for connection issues
      ├── Watch Redis for cache hit rate
      └── Watch /health endpoint for uptime
```

---

## 12. Operational Workflow: Incident Response

```
INCIDENT DETECTED (alert / manual observation)
  │
  ├── Step 1: TRIAGE
  │   ├── Severity: P1 (down), P2 (degraded), P3 (minor)
  │   ├── Scope: All users? Single endpoint? Single provider?
  │   └── Assign responder
  │
  ├── Step 2: INVESTIGATE
  │   ├── Check /ready endpoint (DB + Redis + LLM status)
  │   ├── Check LangSmith traces for errors
  │   ├── Check security_audit_log for anomalies
  │   ├── Check LLM provider status pages
  │   └── Identify root cause
  │
  ├── Step 3: MITIGATE
  │   │
  │   ├── LLM Provider Down
  │   │   ├── Fallback chain should auto-handle
  │   │   ├── If all providers down: Display "AI temporarily unavailable"
  │   │   └── Monitor provider status pages
  │   │
  │   ├── Database Connection Lost
  │   │   ├── Check Neon PG status page
  │   │   ├── Restart connection pool
  │   │   └── If persistent: Scale up Neon compute
  │   │
  │   ├── Redis Down
  │   │   ├── System continues without cache (slower but functional)
  │   │   ├── Restart Redis container
  │   │   └── If Upstash: Check status page
  │   │
  │   ├── Rate Limiting Triggered
  │   │   ├── Check if legitimate traffic spike
  │   │   ├── Temporarily increase rate limits
  │   │   └── If abuse: Block source IP
  │   │
  │   └── Prompt Injection Attack
  │       ├── Check security_audit_log for injection_blocked events
  │       ├── Block offending source IP
  │       ├── Verify LlamaGuard is active
  │       └── Review and strengthen injection patterns
  │
  ├── Step 4: RESOLVE
  │   ├── Apply fix
  │   ├── Verify system healthy via /ready
  │   ├── Run smoke tests
  │   └── Mark incident resolved
  │
  └── Step 5: POST-MORTEM
      ├── Document: What happened, why, how long, how fixed
      ├── Action items: Prevent recurrence
      └── Update runbook if needed
```

---

## 13. Operational Workflow: Backup & Recovery

```
DAILY BACKUP (automated)
  │
  ├── Neon PostgreSQL
  │   ├── Neon auto-backup (point-in-time recovery)
  │   ├── pg_dump weekly to S3/GCS
  │   └── Retention: 30 days
  │
  ├── Neo4j
  │   ├── neo4j-admin dump weekly
  │   ├── Store dump in object storage
  │   └── Retention: 14 days
  │
  ├── ChromaDB (local)
  │   ├── Copy persist directory to backup
  │   └── Retention: 7 days
  │
  └── Redis
      ├── No persistent backup needed (cache only)
      └── Rebuild from source on restore

RECOVERY PROCEDURE
  │
  ├── Neon PG Recovery
  │   ├── Use Neon point-in-time recovery
  │   ├── Or: Restore from pg_dump
  │   └── Run migrations to ensure schema current
  │
  ├── Neo4j Recovery
  │   ├── Stop Neo4j container
  │   ├── neo4j-admin load --from=backup.dump
  │   ├── Start Neo4j container
  │   └── Verify with test Cypher query
  │
  └── ChromaDB Recovery
      ├── Stop application
      ├── Restore persist directory from backup
      ├── Start application
      └── Verify with test search query
```

---

## 14. Workflow Summary Matrix

| Workflow | Type | Steps | Latency Target | Error Handling |
|----------|------|-------|---------------|----------------|
| Council Query (no debate) | User | 7 | < 6s | Fallback chain, error output |
| Council Query (1 debate) | User | 10 | < 8s | Same as above |
| RAG Upload | User | 6 | < 10s | File validation, reject invalid |
| RAG Ask (cached) | User | 1 | < 50ms | Return stale cache on error |
| RAG Ask (uncached) | User | 10 | < 5s | "Insufficient information" |
| Brand Crisis Comms | User | 5 | < 4s | PII redaction, human review |
| Route Optimization | User | 4 | < 3s | Return no valid routes |
| MCP Tool Execution | System | 8 | < 500ms | Cache fallback, timeout |
| LLM Routing | System | 6 | < 2s | 4-provider fallback chain |
| Cache Invalidation | System | 3 | < 100ms | Best-effort delete |
| Deployment | Ops | 7 | ~30min | Rollback to previous image |
| Incident Response | Ops | 5 | ~15min | Mitigate → Resolve → Post-mortem |
| Backup & Recovery | Ops | 3+3 | ~10min | Point-in-time recovery |
