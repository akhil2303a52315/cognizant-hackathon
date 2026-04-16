# Changelog — April 15, 2026

## Summary

Enhanced the **Dashboard** and **Brand Control** pages with tab navigation, additional KPI cards, and new data integrations from backend APIs. Also added missing API endpoints to the frontend client and created new React Query hooks.

---

## 1. Frontend API Client (`frontend/src/lib/api.ts`)

### Added Endpoints

| API Group | Endpoint | Method | Description |
|-----------|----------|--------|-------------|
| `riskApi` | `/risk/suppliers` | GET | List all suppliers with risk scores |
| `riskApi` | `/risk/score/{id}` | GET | Get individual supplier risk score |

### Existing Endpoints Used by New Hooks

| API Group | Endpoint | Used By Hook |
|-----------|----------|--------------|
| `riskApi` | `/risk/heatmap` | `useRiskHeatmap` |
| `healthApi` | `/health` | `useSystemHealth` |
| `ragApi` | `/rag/stats` | `useRAGStats` |
| `ingestApi` | `/ingest/status` | `useIngestStatus` |
| `modelsApi` | `/models/list` | `useModelsStatus` |

---

## 2. New Hooks (`frontend/src/hooks/useDashboardData.ts`)

Created 6 new React Query hooks for fetching dashboard-related data:

| Hook | Query Key | Stale Time | Refetch Interval | Data Source |
|------|-----------|------------|-------------------|-------------|
| `useSuppliers()` | `['risk', 'suppliers']` | 60s | — | `riskApi.suppliers()` |
| `useRiskHeatmap()` | `['risk', 'heatmap']` | 120s | — | `riskApi.heatmap()` |
| `useSystemHealth()` | `['health']` | 15s | 30s | `healthApi.check()` |
| `useRAGStats()` | `['rag', 'stats']` | 120s | — | `ragApi.stats()` |
| `useIngestStatus()` | `['ingest', 'status']` | 30s | 60s | `ingestApi.status()` |
| `useModelsStatus()` | `['models', 'status']` | 120s | — | `modelsApi.list()` |

**Design decisions:**
- `useSystemHealth` auto-refetches every 30s for real-time health monitoring
- `useIngestStatus` auto-refetches every 60s to track ingestion progress
- Risk and RAG data uses longer stale times (120s) as they change less frequently

---

## 3. Dashboard Enhancement (`frontend/src/pages/Dashboard.tsx`)

### Tab Navigation System

Added 5 tabs with icon-based navigation:

| Tab ID | Label | Icon | Content |
|--------|-------|------|---------|
| `overview` | Overview | `Activity` | Market ticker, forex, commodities, risk monitor, disaster alerts |
| `market` | Market | `TrendingUp` | Stock grid, forex rates, commodity prices |
| `risk` | Risk | `Shield` | Risk KPIs, earthquake alerts, risk heatmap, disaster alerts |
| `supply` | Supply Chain | `Truck` | Supplier KPIs, supplier directory table |
| `system` | System | `Server` | Service health, RAG docs, ingest status, AI models |

### KPI Cards (8 total, always visible across tabs)

| KPI | Data Source | Fallback |
|-----|-------------|----------|
| MCP Tools | Static (99) | — |
| Live APIs | Static (27) | — |
| Risk Regions | `useRiskDashboard` | 3 |
| Data Sources | Static (40+) | — |
| Suppliers | `useSuppliers` | 3 |
| Avg Risk | `useRiskHeatmap` (global_avg) | — |
| Disasters | `useRiskDashboard` (global_disasters) | 0 |
| Services Up | `useSystemHealth` (checks) | 0/1 |

### New Data Sections by Tab

**Risk Tab:**
- 4 risk-specific KPI cards (Avg Risk Score, High Risk Regions, Disaster Alerts, Risk Regions)
- Risk Heatmap by Region — color-coded grid (red > 40, amber > 20, green ≤ 20)
- Earthquake alerts per region
- Global disaster alerts

**Supply Chain Tab:**
- 4 supplier KPI cards (Total Suppliers, Avg Lead Time, Avg Capability, Avg Risk)
- Supplier Directory table with columns: Name, Location, Tier, Capability, Lead Time, Risk Score
- Risk scores are color-coded badges (red/amber/green thresholds)

**System Tab:**
- 4 system KPI cards (Services Up, MCP Tools, RAG Docs, Ingest Status)
- Service Health Checks grid — per-service status with ok/error indicators
- AI Models Status list — shows model names and statuses

---

## 4. Brand Control Enhancement (`frontend/src/pages/Brand.tsx`)

### Tab Navigation System

Added 4 tabs with icon-based navigation:

| Tab ID | Label | Icon | Content |
|--------|-------|------|---------|
| `overview` | Overview | `Activity` | Search controls, social feeds, wiki articles, tool results |
| `social` | Social | `MessageSquare` | Sentiment search, r/supplychain feed, r/logistics feed, analysis results |
| `research` | Research | `BookOpen` | Company profile lookup, Wikipedia articles, profile results |
| `competitors` | Competitors | `Swords` | Competitor search, competitor analysis results |

### KPI Cards (6 total, always visible across tabs)

| KPI | Data Source | Fallback |
|-----|-------------|----------|
| Reddit Posts | `useBrandIntel` (supplychain + logistics) | 0 |
| Wiki Articles | `useBrandIntel` (wiki_articles) | 0 |
| Avg Score | Computed from reddit posts | — |
| Total Comments | Computed from reddit + logistics posts | 0 |
| Competitors | `useMCPInvoke` result | 0 |
| Data Sources | Static (3) | — |

### Tab-Specific Features

**Social Tab:**
- Dedicated sentiment search input with Analyze button
- Full-height social feeds (max-h-96) for both r/supplychain and r/logistics
- Sentiment analysis result display

**Research Tab:**
- Company profile lookup by stock symbol
- Wikipedia knowledge base articles grid
- Company profile JSON result display

**Competitors Tab:**
- Competitor intelligence search input
- Competitor analysis result display with mock data indicator
- Loading and error states

---

## 5. Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/lib/api.ts` | Modified | Added `suppliers()` and `supplierScore()` to `riskApi` |
| `frontend/src/hooks/useDashboardData.ts` | Created | 6 new React Query hooks for dashboard data |
| `frontend/src/pages/Dashboard.tsx` | Modified | Added tabs, 8 KPI cards, 5 tab content sections |
| `frontend/src/pages/Brand.tsx` | Modified | Added tabs, 6 KPI cards, 4 tab content sections |

---

## 6. Technical Notes

- **Type Safety:** All API responses are cast as `Record<string, unknown>` or `Array<Record<string, unknown>>` to handle dynamic API responses. Supplier table fields are explicitly cast with `String()` and `Number()` wrappers.
- **Loading States:** Each tab section uses `LoadingSkeleton` component or inline loading indicators while data is being fetched.
- **Error Handling:** API hooks use React Query's built-in error handling. The Brand page displays error banners for failed MCP invocations.
- **Responsive Design:** KPI grids use `grid-cols-2 md:grid-cols-4 lg:grid-cols-8` (Dashboard) and `grid-cols-2 md:grid-cols-4 lg:grid-cols-6` (Brand) for responsive layouts.
- **Tab State:** Uses React `useState` for tab selection. Tabs are rendered with conditional fragments (`{activeTab === 'id' && (<>...</>)}`).
- **Color Coding:** Risk scores follow a 3-tier color system: Red (>40), Amber (>20), Green (≤20).

---

## 7. Pending / Future Work

- [ ] Unit tests for Dashboard and Brand components
- [ ] Integration tests for new API hooks
- [ ] Add chart/visualization components to Risk and Market tabs
- [ ] Add export/download functionality to Supplier Directory table
- [ ] Add real-time WebSocket updates for System health tab
- [ ] Add pagination to supplier directory
