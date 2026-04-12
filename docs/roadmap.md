# SupplyChainGPT — Product Roadmap

## Current Status (End of Day 5)

| Phase | Name | Status | Completion |
|-------|------|--------|------------|
| 0 | Project Setup | ✅ Complete | 100% |
| 1 | Core LangGraph Council | ✅ Complete | 100% |
| 2 | Agentic RAG Integration | ✅ Complete | 100% |
| 3 | MCP Tool Integration | ✅ Complete | 100% |
| 4 | Debate Engine + Predictions | ✅ Complete | 100% |
| 5 | Backend API + Optimization | ✅ Complete | 100% |
| 6 | Frontend Foundation | ✅ Complete | 100% |
| 7 | Frontend Polish & Integration | 🔲 Upcoming | 0% |
| 8 | Security & Production Hardening | 🔲 Upcoming | 0% |
| 9 | Testing, Deployment & Demo | 🔲 Upcoming | 0% |

**Overall: ~60% complete**

---

## Day 6 (Apr 17) — Backend API + Observability

### Morning: Production API Polish
- [ ] Add request/response validation schemas (Pydantic v2) for all endpoints
- [ ] Implement pagination on list endpoints (`/rag/collections`, `/risk/suppliers`)
- [ ] Add API versioning prefix (`/v1/...`)
- [ ] Swagger/OpenAPI docs polish with examples

### Afternoon: Observability & Monitoring
- [ ] LangSmith tracing integration for all agent runs
- [ ] Prometheus metrics endpoint (`/metrics`) — latency, token usage, error rate
- [ ] Grafana dashboard JSON stub
- [ ] Structured logging with correlation IDs
- [ ] Health check aggregation (DB + Redis + Neo4j + LLM status)

---

## Day 7 (Apr 18) — Frontend Dashboard (4-Page SPA)

### Morning: Dashboard + Chat Pages
- [ ] Dashboard page: Risk heatmap (recharts), supplier stats cards, alert feed
- [ ] Chat page: Council query input, streaming response display, agent cards with confidence bars
- [ ] Connect to backend via TanStack Query mutations
- [ ] SSE streaming integration for council responses

### Afternoon: Debate + Brand Pages
- [ ] Debate page: Multi-round timeline, agent argument cards, prediction charts
- [ ] Brand page: Social sentiment dashboard, competitor intelligence, crisis response templates
- [ ] Settings page: API key management, RAG config, theme toggle
- [ ] Real-time WebSocket updates (agent status, risk alerts)

---

## Day 8 (Apr 19) — Production Polish & Security

### Morning: Security Hardening
- [ ] Input sanitization on all endpoints
- [ ] Rate limiting per-user (not just per-IP)
- [ ] CORS origin whitelist (remove `*`)
- [ ] HTTPS enforcement
- [ ] API key rotation support
- [ ] Audit log persistence (PostgreSQL)

### Afternoon: UI Polish & Integration
- [ ] Responsive design (mobile-friendly)
- [ ] Loading skeletons on all pages
- [ ] Error boundaries with fallback UI
- [ ] Dark/light theme persistence
- [ ] PDF export from frontend (download button)
- [ ] Keyboard shortcuts for power users
- [ ] Accessibility (ARIA labels, focus management)

---

## Day 9 (Apr 20) — Testing, Deployment & Final Prep

### Morning: Dockerization & Deployment
- [ ] Finalize `docker-compose.yml` (multi-container)
- [ ] Production Dockerfiles (multi-stage builds)
- [ ] AWS ECS/Fargate deployment scripts
- [ ] S3 + CloudFront for frontend static hosting
- [ ] Environment variable injection for production

### Afternoon: Testing & Demo Prep
- [ ] End-to-end tests (Playwright) for all 4 pages
- [ ] Load testing (Locust) — 100 concurrent users
- [ ] Record demo video (3–5 min walkthrough)
- [ ] Update presentation with screenshots + architecture diagram
- [ ] Final README polish

---

## Post-Hackathon Roadmap

### Short Term (1–2 weeks)
- [ ] Multi-tenant support (organization-level API keys)
- [ ] Persistent chat history (PostgreSQL)
- [ ] Agent fine-tuning on supply chain domain data
- [ ] Real Firecrawl integration with production API key
- [ ] Email/Slack alert notifications for risk events

### Medium Term (1–3 months)
- [ ] Mobile app (React Native) for on-the-go risk monitoring
- [ ] Custom agent builder (users create their own specialist agents)
- [ ] Supply chain network visualization (D3.js / Cytoscape)
- [ ] Predictive analytics dashboard (Prophet + ARIMA forecasts)
- [ ] Multi-language support (i18n)
- [ ] SSO/SAML authentication for enterprise

### Long Term (3–6 months)
- [ ] Autonomous supply chain agent (takes actions, not just recommendations)
- [ ] ERP integration (SAP, Oracle) via MCP connectors
- [ ] Blockchain-based supply chain traceability
- [ ] Computer vision for warehouse/shipment inspection
- [ ] Regulatory compliance engine (automated reporting)
- [ ] Marketplace for custom MCP tools

---

## Key Metrics & Targets

| Metric | Hackathon Target | Production Target |
|--------|-----------------|-------------------|
| Council response time | < 30s | < 10s |
| API uptime | 95% | 99.9% |
| Test coverage | 50% | 80% |
| Frontend Lighthouse | 70+ | 90+ |
| MCP tool count | 22 | 50+ |
| Concurrent users | 10 | 1000 |
| Risk prediction accuracy | N/A | 85%+ |

---

## Technology Decisions Log

| Decision | Choice | Rationale | Date |
|----------|--------|-----------|------|
| LLM Provider | Groq (Llama-3.3-70B) | Free tier, fast inference | Day 1 |
| Frontend Framework | React 18 + Vite | Fast builds, TypeScript | Day 5 |
| State Management | Zustand | Lightweight, no boilerplate | Day 5 |
| Data Fetching | TanStack Query | Caching, mutations, streaming | Day 5 |
| WebSocket | Native WS (not socket.io) | Simpler, matches FastAPI | Day 5 |
| Web Scraping | Firecrawl MCP | No custom scrapers, mock fallback | Day 5 |
| PDF Generation | ReportLab | Python-native, no external service | Day 5 |
| Styling | Tailwind + shadcn tokens | Consistent, dark-mode ready | Day 5 |
