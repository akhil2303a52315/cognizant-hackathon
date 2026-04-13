# Day 5 Development — Debate Engine + Predictions + Brand Enhancement + Fallbacks

> **Date:** Day 5 (Apr 13)
> **Focus:** Structured multi-round debate, ensemble predictions, tiered fallbacks, brand agent enhancement
> **Status:** ✅ Complete

---

## Overview

Day 5 implements the core decision-making infrastructure: a 3-round structured debate engine, ensemble predictions (Prophet + LSTM stub + Monte Carlo), tiered fallback options with cost/ROI analysis, and an enhanced brand agent with real-time sentiment analysis, crisis communications, ad pivot recommendations, and competitor counter-messaging.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DAY 5 FULL WORKFLOW                               │
│                                                                      │
│  Phase 1 (Days 3-4):                                                │
│  Moderator → RAG Pre-fetch → MCP Escalation → Agent Fan-out         │
│                                                                      │
│  Phase 2 (Day 5 NEW):                                               │
│  All 6 Agents → Predictions → Debate Engine → Fallback Engine       │
│                                                                      │
│  Phase 3 (Day 5 NEW):                                               │
│  Fallback → Brand Enhancement? → Final Synthesis                   │
│              (conditional)                                           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              DEBATE ENGINE (3 Rounds)                     │       │
│  │  Round 1: Parallel Analysis Summary                      │       │
│  │  Round 2: Challenge & Counter (agents critique each)    │       │
│  │  Round 3: Validation & Synthesis                         │       │
│  │  → Confidence-weighted consensus + risk score           │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              PREDICTIONS ENGINE                           │       │
│  │  Prophet (time-series) + LSTM Stub + Monte Carlo         │       │
│  │  → Ensemble with 95% confidence intervals               │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              FALLBACK ENGINE (3 Tiers)                    │       │
│  │  Tier 1: Immediate (near-shoring, air freight, inventory)│       │
│  │  Tier 2: Short-term (safety stock, dual-source, routes) │       │
│  │  Tier 3: Strategic (regional hubs, vertical integration) │       │
│  │  → One-click MCP execution + cost/ROI analysis           │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              BRAND ENHANCEMENT                            │       │
│  │  Real-time sentiment analysis (RAG + MCP news/social)    │       │
│  │  Auto-generated crisis communication drafts              │       │
│  │  Advertising pivot recommendations                       │       │
│  │  Competitor counter-messaging                            │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## New Files

| File | Lines | Purpose |
|------|-------|---------|
| `backend/debate_engine.py` | ~290 | `DebateEngine` class: 3-round structured debate with challenge/counter, confidence-weighted consensus, max 3 rounds, structured `DebateRound` outputs |
| `backend/predictions_engine.py` | ~280 | Ensemble predictions: Prophet, LSTM stub, Monte Carlo simulation, simple trend fallback. Returns `Prediction` with 95% CI |
| `backend/fallback_engine.py` | ~260 | `FallbackEngine` with 9 pre-defined fallback templates across 3 tiers. Cost/ROI analysis, one-click MCP execution |
| `backend/brand_agent_enhancement.py` | ~250 | `BrandAgentEnhancer`: sentiment analysis, crisis comms, ad pivot, competitor counter-messaging. Uses RAG + MCP tools |

---

## Updated Files

| File | Changes |
|------|---------|
| `backend/state.py` | Added `DebateRound`, `FallbackOption`, `Prediction`, `BrandSentiment` Pydantic models. Added `debate_rounds`, `predictions`, `tiered_fallbacks`, `brand_sentiment`, `human_approved` to `CouncilState` |
| `backend/graph.py` | Added 4 new nodes: `predictions`, `debate`, `fallback`, `brand_enhancement`. New flow: agents → predictions → debate → fallback → (brand?) → synthesize |
| `backend/agents/moderator.py` | `moderator_synthesize` now uses debate results, predictions, tiered fallbacks, and brand sentiment for comprehensive final recommendation |

---

## Debate Engine Details

### 3-Round Structure

| Round | Phase | Description |
|-------|-------|-------------|
| 1 | Analysis | Summarize parallel agent contributions, extract disagreements and consensus via LLM |
| 2 | Challenge | Each agent challenges the most conflicting other agent. Updated confidence scores |
| 3 | Validation | Final convergence round. Force synthesis if no consensus |

### Consensus Logic

```
if confidence_gap < 15% → consensus reached → skip remaining rounds
if confidence_gap >= 15% and round < 3 → continue debate
if round == 3 → forced synthesis regardless of gap
```

### Challenge & Counter

Each agent identifies the most conflicting peer (largest confidence gap) and:
1. Challenges their key assumptions with evidence
2. Acknowledges points of agreement
3. Suggests a compromise position
4. Updates their confidence score

---

## Predictions Engine Details

### Methods

| Method | Description | Confidence Weight |
|--------|-------------|------------------|
| Prophet | Facebook/Meta time-series forecasting with yearly seasonality | 0.40 |
| LSTM Stub | Placeholder for production LSTM (falls back to simple trend) | 0.25 |
| Monte Carlo | 10,000-path geometric Brownian motion with jump-diffusion | 0.35 |
| Simple Trend | Weighted moving average with linear extrapolation (fallback) | 0.20 |
| **Ensemble** | Weighted average of all methods | — |

### Monte Carlo Simulation

- 10,000 simulation paths
- Geometric Brownian motion with daily steps
- Jump-diffusion (1% daily jump probability, Gaussian jump size)
- Calibrated with RAG historical disruption data
- Returns point estimate + 95% confidence interval

### Prediction Metrics

| Agent | Metric | Horizon |
|-------|--------|---------|
| Market | price | 90 days |
| Finance | disruption_probability | 90 days |
| Supply | lead_time | 60 days |

---

## Fallback Engine Details

### Tiered Fallback Options

| Tier | Name | Cost | Time | Risk Reduction | ROI |
|------|------|------|------|----------------|-----|
| 1 | Near-Shoring Emergency | $150K | 3 days | 25% | 180% |
| 1 | Air Freight Emergency | $380K | 1 day | 35% | 120% |
| 1 | Strategic Inventory Release | $50K | 1 day | 15% | 250% |
| 2 | Safety Stock Buffer | $500K | 14 days | 30% | 160% |
| 2 | Dual-Sourcing Qualification | $350K | 21 days | 40% | 200% |
| 2 | Route Diversification | $200K | 14 days | 20% | 140% |
| 3 | Regional Distribution Hubs | $5M | 180 days | 60% | 300% |
| 3 | Vertical Integration | $15M | 365 days | 70% | 250% |
| 3 | Long-Term Contracts | $2M | 90 days | 45% | 180% |

### One-Click Execution

Tier 1 and Tier 2 fallbacks have MCP tools configured:
- `supplier_search` → near-shoring activation
- `route_optimize` → air freight / route diversification
- `erp_query` → inventory release / safety stock
- `contract_lookup` → long-term contract review

### Dynamic Optimization

- Cost adjusted by supply agent confidence (higher confidence → lower cost)
- ROI scaled by disruption probability (higher risk → higher mitigation value)
- Cost scaled by price forecast (rising prices → higher procurement cost)
- Confidence reduced for long implementation times (>90 days)

---

## Brand Agent Enhancement Details

### Pipeline

1. **Sentiment Analysis** — Fetch news + social data via MCP, combine with RAG context, LLM produces structured `BrandSentiment`
2. **Crisis Communication** — Auto-generated press release (only if negative/crisis sentiment)
3. **Ad Pivot** — Advertising strategy recommendations (only if sentiment < -0.3)
4. **Competitor Counter-Messaging** — Competitor analysis via Firecrawl + counter-strategy

### MCP Tools Used

| Tool | Purpose |
|------|---------|
| `news_search` | Latest news about the crisis |
| `reddit_search` | Social media sentiment |
| `firecrawl_search` | Competitor intelligence |
| `social_sentiment` | Aggregate sentiment score |

---

## LangGraph Flow (Full)

```
moderator → rag_prefetch → mcp_escalation
    → risk ──────────────────┐
    → supply ─────────────────┤
    → logistics ──────────────┤
    → market ─────────────────┼──→ predictions → debate → fallback
    → finance ────────────────┤                         │
    → brand ──────────────────┘                         │
                                              ┌─────────┴─────────┐
                                              │ needs_brand_enh?  │
                                              ├───────────────────┤
                                              │ yes → brand_enh   │
                                              │ no  → synthesize  │
                                              └───────────────────┘
                                                       │
                                              brand_enh → synthesize → END
```

---

## Testing

### Sample Query

```
"Taiwan chip crisis impact on EV battery supply chain"
```

### Expected Output Structure

```json
{
  "recommendation": "Executive summary with priority actions...",
  "confidence": 0.72,
  "risk_score": 68.0,
  "debate_rounds": [
    {
      "round_number": 1,
      "phase": "analysis",
      "agent_contributions": [...],
      "key_disagreements": ["Risk agent sees 80% disruption, Finance sees 40%"],
      "consensus_points": ["All agents agree Taiwan dependency is critical"],
      "round_confidence": 62.5
    },
    {
      "round_number": 2,
      "phase": "challenge",
      "agent_contributions": [...],
      "key_disagreements": [...],
      "consensus_points": [...],
      "round_confidence": 71.0
    }
  ],
  "predictions": [
    {
      "metric": "price",
      "method": "ensemble",
      "point_estimate": 2.45,
      "ci_lower": 1.80,
      "ci_upper": 3.20,
      "confidence": 0.65,
      "horizon_days": 90
    },
    {
      "metric": "disruption_probability",
      "method": "monte_carlo",
      "point_estimate": 0.42,
      "ci_lower": 0.28,
      "ci_upper": 0.58,
      "confidence": 0.72,
      "horizon_days": 90
    }
  ],
  "tiered_fallbacks": [
    {
      "tier": 1,
      "name": "Near-Shoring Emergency Activation",
      "cost_estimate_usd": 150000,
      "time_to_implement_days": 3,
      "risk_reduction_pct": 25.0,
      "roi_pct": 180.0,
      "confidence": 0.85,
      "mcp_tool": "supplier_search"
    },
    ...
  ],
  "brand_sentiment": {
    "overall_sentiment": "crisis",
    "sentiment_score": -0.65,
    "trending_topics": ["chip shortage", "EV battery", "Taiwan"],
    "crisis_keywords": ["shortage", "crisis", "disruption"],
    "recommended_actions": ["Issue supplier diversification statement", ...],
    "crisis_comm_draft": "PRESS RELEASE: ...",
    "ad_pivot_recommendation": "Shift from growth messaging to reliability assurance...",
    "competitor_activity": "Competitor X has announced alternative sourcing..."
  }
}
```

---

## Day 5 Deliverables ✅

- [x] DebateEngine with 3-round structured debate
- [x] Confidence-weighted consensus logic
- [x] Challenge & Counter phase (agents critique each other)
- [x] Max 3 rounds to prevent infinite loops
- [x] Structured DebateRound Pydantic outputs
- [x] Ensemble predictions (Prophet + LSTM stub + Monte Carlo)
- [x] 95% confidence intervals on all predictions
- [x] Monte Carlo simulation with jump-diffusion
- [x] RAG-calibrated disruption probability
- [x] Tiered fallback system (9 options across 3 tiers)
- [x] Cost/ROI analysis per fallback option
- [x] One-click MCP execution for Tier 1/2 fallbacks
- [x] Dynamic cost adjustment based on predictions
- [x] Brand sentiment analysis using RAG + MCP
- [x] Auto-generated crisis communication drafts
- [x] Advertising pivot recommendations
- [x] Competitor counter-messaging
- [x] Updated graph.py with full Day 5 workflow
- [x] Updated moderator with debate-aware synthesis
- [x] New Pydantic models in state.py
