# SupplyChainGPT — Feature List

Complete feature breakdown for the Council of Debate AI Agents system, derived from the project documentation.

---

## 1. Agent Features

### 1.1 Risk Sentinel Agent
- Real-time supplier risk scoring (0–100 scale)
- Geopolitical disruption prediction
- Financial health monitoring of suppliers
- Natural disaster impact assessment
- Multi-signal correlation engine (news + financials + social + geopolitical)
- BERT fine-tuned on supply chain risk news
- XGBoost risk scoring model
- LSTM time-series anomaly detection

### 1.2 Supply Optimizer Agent
- Alternate supplier recommendation engine
- Demand forecasting (seasonal + event-driven)
- Multi-tier supplier mapping (Tier 1, 2, 3 visibility)
- Safety stock optimization
- Lead time comparison across suppliers
- Graph Neural Networks on Neo4j supplier graph
- Prophet + LSTM for demand forecasting
- Cosine similarity for alternate supplier matching

### 1.3 Logistics Navigator Agent
- Multi-modal route optimization (sea/air/land)
- Real-time port congestion alerts
- Carrier reliability scoring
- Carbon footprint tracking per route
- Customs clearance time estimation
- Google OR-Tools route optimization
- Dijkstra's + A* path finding
- Regression model for freight rate prediction

### 1.4 Market Intelligence Agent
- Commodity price trend forecasting
- Trade war / tariff impact modeling
- Competitive supply chain benchmarking
- Market demand shift prediction
- "What-if" scenario modeling (10+ variables)
- Prophet + ARIMA for price forecasting
- Monte Carlo simulation for scenario modeling
- Web scraping + NLP for competitor intelligence

### 1.5 Finance Guardian Agent
- Disruption cost estimation (direct + indirect)
- Mitigation ROI calculation
- Currency risk assessment
- Insurance claim automation
- Budget impact forecasting
- Z-score model for financial health
- Monte Carlo for cost scenarios
- Linear programming for budget optimization

### 1.6 Brand Protector Agent
- Real-time brand sentiment monitoring
- Auto-generated crisis communications (press releases, social posts, ad copies)
- Advertising pivot recommendations
- Competitor exploitation detection
- Customer notification drafting
- BERT sentiment analysis (fine-tuned)
- GPT-4 / LLM for content generation
- Social listening APIs + trend detection

### 1.7 Moderator / Orchestrator Agent
- Query routing to relevant agents
- Parallel agent processing
- Conflict identification between agent recommendations
- Forced debate when agents disagree
- Confidence-weighted recommendation synthesis
- Executive summary generation
- LangGraph multi-agent orchestration
- Custom debate protocol (chain-of-thought prompting)
- Confidence-weighted ensemble decision making

---

## 2. Council & Debate Features

### 2.1 Multi-Agent Debate Protocol
- **Round 1**: Individual Agent Analysis (parallel processing — all 6 domain agents respond independently)
- **Round 2**: Challenge Round (agents challenge each other's recommendations, provide counter-arguments)
- **Round 3**: Final Synthesis (Moderator synthesizes unified recommendation)
- Maximum 3 debate rounds before forced synthesis
- Each agent submits recommendation + confidence score
- Agents can "challenge" other agents' recommendations
- Majority confidence-weighted vote on final decision

### 2.2 Structured Output
- Each agent returns Pydantic model with `confidence` (float 0–100) and `contribution`
- Final recommendation includes: summary, actions, fallbacks, confidence score
- Agent outputs include: agent name, confidence, key points
- Evidence references: type, ID, tag, lane, days

### 2.3 Human-in-the-Loop
- Interrupt before moderator synthesis for human review
- Suggestions reviewed before execution (especially supplier switches, customer communications, financial actions)
- Human approval gates for critical actions

---

## 3. Predictions Engine

- **30-day predictions**: Immediate risk mitigation + short-term sourcing
- **60-day predictions**: Supply rebalancing + logistics optimization
- **90-day predictions**: Strategic shifts + brand recovery + financial hedging
- Prophet + LSTM ensemble forecasting
- Monte Carlo simulation (10,000 scenarios)
- Confidence-weighted ensemble across agents
- Visual charts (Recharts) for forecast display

---

## 4. Fallback Options Engine

### Tier 1 — IMMEDIATE (0–48 Hours)
- Activate pre-qualified backup supplier (auto-PO generation)
- Emergency air freight routing (auto-booking via API)
- Pause product ads → Launch "Coming Soon" campaign
- Auto-notify affected customers (GenAI-drafted emails)

### Tier 2 — SHORT-TERM (2–4 Weeks)
- Multi-source procurement split across 2–3 suppliers
- Explore contract manufacturing options (Tier 3 fallback)
- Adjust product launch timeline → Marketing pivot
- Activate cargo insurance claim (auto-documented)

### Tier 3 — STRATEGIC (1–6 Months)
- Geographic diversification strategy (new country sourcing)
- Near-shoring / Friend-shoring recommendation
- Safety stock policy revision (AI-optimized buffer levels)
- Full brand narrative reset ("Supply Chain Excellence" story)

### Per-Fallback Auto-Includes
- Cost estimate
- Time to implement
- Risk score of the fallback itself

---

## 5. Brand Crisis Features

### Scenario A: Product Shortage
- Pause product availability ads
- Launch brand sentiment campaign
- Push substitute/alternative products
- Run "Pre-order now" campaign
- Auto-draft CEO/brand social posts

### Scenario B: Price Increase
- Value messaging push
- Loyalty rewards campaign
- High-LTV customer exclusive pricing
- Transparent pricing communication

### Scenario C: Competitor Exploiting Disruption
- Monitor competitor ad spend on brand keywords
- Launch differentiation campaigns
- Retarget lost customers
- Accelerate social proof (reviews, testimonials)

### Scenario D: Sustainability Disruption
- Sustainability commitment campaign
- Publish supplier audit results & corrective actions
- Target ESG-conscious customer segment
- Stakeholder communication on ethical sourcing

---

## 6. Risk Scoring Pipeline

1. **Signal Ingestion**: Collect from GDELT, NewsAPI, carrier APIs, ERP, geopolitical indices, social sentiment
2. **Signal Normalization**: Convert signals into comparable numeric features
3. **Score Aggregation**: Weighted transparent score or XGBoost model score
4. **Evidence Attachment**: Store why score changed (event tags, lane delays, PO impact)

**Output**:
- Risk score: 0–100 (or Low/Medium/High)
- Drivers: top 3–5 factors
- Impacted items: affected components/POs
- Suggested actions: triggers Council analysis

---

## 7. RAG (GenAI Q&A) Features

- Document-grounded Q&A using your own documents (SOPs, contracts, incident reports, onboarding checklists)
- Chunk → embed → store vectors pipeline
- Top-K chunk retrieval on query
- LLM answers using only retrieved context
- Citations to internal document IDs (no free-form guessing)
- Example queries:
  - "What is our SOP if a critical supplier lead time increases by 2 weeks?"
  - "What steps are required to qualify an alternate supplier for Component C2?"
  - "Summarize the last incident involving port congestion and what we changed."

---

## 8. MCP (Model Context Protocol) Features

- MCP servers for secure tool calling in every agent
- MCP sandboxing with least-privilege scopes
- MCP tool management via Settings modal in UI
- Tool permissions restricted per agent
- External content sanitization before adding to RAG context

---

## 9. Optimization (OR-Tools) Features

- **Routing**: Choose route/mode/carrier minimizing cost while meeting delivery deadline
- **Allocation**: Split demand across suppliers based on capacity, MOQ, lead time, and risk
- **Expedite tradeoffs**: Compare reroute vs air freight vs safety stock usage
- Constraint support: lead time, budget, supplier capacity, MOQ, service level targets

---

## 10. API Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest/erp` | Ingest POs, inventory |
| POST | `/signals/news` | Ingest news/events batch |
| GET | `/risk/suppliers/{supplier_id}` | Get supplier risk score |
| POST | `/council/analyze` | Run council on query/incident |
| POST | `/optimize/routes` | Optimize routes |
| POST | `/rag/ask` | Ask RAG a question |

- Async endpoints via FastAPI
- Error middleware
- CORS support
- Rate limiting
- API key authentication

---

## 11. UI Features

### Page 1: Dashboard Home (`/` or `/dashboard`)
- Live Risk Score gauge (0–100)
- Active Disruptions count
- Predicted Savings (₹ or $)
- Interactive Risk Heatmap (world map / supplier graph)
- Clickable supplier nodes
- Recent Queries cards with confidence %
- Quick Query Input + "Convene Council" button

### Page 2: Council Chat Interface (`/chat`)
- Query History sidebar
- Saved Scenarios (Taiwan Chip Crisis, etc.)
- Streaming messages from Moderator + Agent highlights
- Real-time Agent Status panel (7 avatars with live confidence bars)
- "Run Full Council" / "Run Specific Agent" dropdown
- WebSocket streaming for live debate updates

### Page 3: Live Debate & Predictions Viewer (`/debate`)
- Query Summary + Overall Confidence
- Debate Round timeline (Round 1 → Round 2 → Round 3)
- Agent Cards: role, contribution, confidence %, "View Full Reasoning" modal
- Predictions charts (Prophet/LSTM forecasts, Monte Carlo scenarios)
- Brand Sentiment Widget (real-time score + crisis alert)

### Page 4: Brand Crisis Control Room (`/brand`)
- Live Twitter/Reddit sentiment metrics + trend chart
- Auto-Generated Comms (editable press releases, social posts, ad copies)
- Competitor Intelligence side-by-side comparison
- Action Buttons: "Launch Campaign", "Pause Ads", "Notify Stakeholders"

### Modals (Radix UI + shadcn/ui)
- **Fallback & Action Plan**: Tier 1–3 options, cost/risk/ROI calculator, one-click "Execute"
- **Audit & Observability Log**: Full debate history, LangSmith traces, confidence logs, export PDF/JSON, searchable + filterable
- **Settings & Configuration**: MCP Tool Management, RAG Knowledge Base upload, Human-in-Loop toggles, LLM selection (Groq/Claude), Notification preferences

### Shared UI Components
- Global fixed Navbar
- Toast notifications (shadcn Toast)
- Loading skeletons during Council processing
- Dark/Light theme toggle
- Responsive / mobile-friendly design
- Framer Motion animations for modals and agent status

---

## 12. State Management & Persistence Features

- LangGraph Checkpointer with PostgreSQL + Redis
- Persistent state across restarts
- Audit-ready `debate_history` list
- Confidence-weighted routing
- `CouncilState` TypedDict: `query`, `messages`, `risk_score`, `recommendation`, `confidence`, `debate_history`, `fallback_options`

---

## 13. Observability Features

- Full LangSmith tracing (agent_name, confidence, mcp_calls metadata)
- LangSmith trace sharing (public links for demo)
- Prometheus metrics endpoint (latency, token usage, error rate)
- Grafana dashboard JSON stub
- Custom metadata tagging per agent run
- Export debate trail → PDF/JSON

---

## 14. Security Features

- Prompt injection protection (LlamaGuard or custom guardrails per agent)
- Rate limiting + CORS + API key authentication in FastAPI
- PII redaction in Brand Agent outputs
- MCP sandboxing with least-privilege scopes
- Data minimization (ingest only needed fields)
- Role-based access control (Procurement vs Finance vs Comms)
- RAG grounding (cite internal doc IDs, no free-form guessing)
- Auditability (store agent outputs + evidence references)
- Prompt injection hygiene (sanitize external content, isolate tools, restrict tool permissions)

---

## 15. Cost Optimization Features

- Redis caching for RAG results and MCP responses (60%+ cost reduction)
- LLM fallback chain (Groq → Claude on high latency)
- Batch processing for multiple agent calls
- Token usage monitoring via LangSmith

---

## 16. Deployment Features

- Docker Compose (multi-container: FastAPI, React, Redis, Postgres, Neo4j)
- Multi-stage Dockerfile for backend
- Vite build + nginx/FastAPI static for frontend
- AWS ECS/Fargate deployment ready
- Kubernetes manifests (optional, separate namespaces for dev/stage/prod)
- One-click local run: `docker compose up --build`

---

## 17. Testing Features

- **Backend**: pytest unit tests, httpx API tests, mypy static typing, ruff linting
- **Frontend**: vitest/jest unit tests, eslint
- **E2E**: pytest + Playwright for all 4 pages + modals
- **Load**: 50 concurrent query simulation
- **Edge cases**: Low confidence → self-reflection, MCP failure → cached fallback, human-in-loop interrupt

---

## 18. Export & Reporting Features

- Debate trail → PDF download
- Debate trail → JSON download
- Action Plan PDF download
- Email to Leadership button
- Auto-Execute Approved Steps button
- ROI calculator in UI (live $ savings, time saved, risk reduction)

---

## Feature Summary Matrix

| Feature | Agent(s) | Technology | Business Value |
|---------|----------|------------|----------------|
| Real-time Supplier Risk Scoring | Risk | BERT + LSTM + GDELT | Early crisis prevention |
| Alternate Supplier Recommendation | Supply | GNN + Neo4j | Zero supply gaps |
| Intelligent Query Routing | Moderator | LLM intent classification | Better insights, faster |
| Debate & Consensus Engine | Moderator | LangGraph state machine | Balanced decisions |
| 30/60/90-day Predictions | All | Ensemble ML + Monte Carlo | Proactive planning |
| Multi-modal Route Optimization | Logistics | OR-Tools + Shipping APIs | Fastest delivery recovery |
| Commodity Price Forecasting | Market | Prophet + ARIMA | Cost avoidance |
| Financial Impact & ROI | Finance | Z-score + Monte Carlo | Dollar-quantified decisions |
| Brand Crisis Auto-Response | Brand | BERT + GPT-4 + Social APIs | Reputation protection |
| Tiered Fallback Options | All | Constraint optimization | Never without a plan |
| RAG-powered Q&A | All | LangChain + Pinecone | Grounded, cited answers |
| MCP Tool Integration | All | MCP protocol (45 tools) | Real system actions |
| Parallel Agent Execution | Moderator | LangGraph Send/parallel | Speed (all agents run at once) |
| Persistent State | All | PostgreSQL + Redis | Audit trail + restart recovery |
| SSE Streaming Debate | All | Groq + SSE (4029 events verified) | Real-time token-by-token output |
| Live Market Data Dashboard | All | Finnhub + Frankfurter + Yahoo Finance | Real-time stocks, forex, commodities |
| Risk Dashboard (Earthquakes/Weather) | Risk | USGS + Open-Meteo + GDACS | Live disaster monitoring |
| Brand Intelligence | Brand | Reddit + Wikipedia + Arxiv | Live social sentiment + knowledge |
| Market API (4 endpoints) | All | FastAPI aggregation | Frontend-ready market data |
| Cost Optimization | All | Redis cache + LLM fallback | 60%+ cost reduction |
| Security Hardening | All | LlamaGuard + rate limit + PII redaction | Production-safe system |
| Live API Status Monitor | Settings | Health check via market ticker | Real-time API health visibility |
