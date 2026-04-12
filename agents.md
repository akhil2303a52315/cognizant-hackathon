# SupplyChainGPT — Agent Specification

Detailed specification for all 7 AI agents in the Council of Debate AI Agents system. All models used are **free-tier only**. Database uses **Neon PostgreSQL** (serverless cloud).

---

## Database: Neon PostgreSQL (Cloud)

### Why Neon
- Serverless PostgreSQL — no Docker container needed for DB
- Free tier: 0.5 GB storage, 100 compute hours/month
- Auto-scaling and auto-suspending (scales to zero when idle)
- Built-in connection pooling
- Branching for dev/staging
- HTTPS API for edge functions

### Configuration

```env
# Neon PostgreSQL (Cloud — Free Tier)
DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
NEON_DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require

# For LangGraph checkpointer (uses same Neon instance)
POSTGRES_URI=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
```

### Neon Setup Steps
1. Go to https://neon.tech → Sign up (free)
2. Create project → `supplychaingpt-council`
3. Copy connection string from dashboard
4. Neon auto-creates database; run migrations via `alembic` or direct SQL

### Schema (Key Tables)

```sql
-- Council session state
CREATE TABLE council_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    risk_score FLOAT,
    recommendation TEXT,
    confidence FLOAT,
    round_number INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Agent outputs per session
CREATE TABLE agent_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id),
    agent VARCHAR(30) NOT NULL,
    confidence FLOAT,
    contribution TEXT,
    key_points JSONB,
    model_used VARCHAR(100),
    provider VARCHAR(30),
    round_number INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Debate history
CREATE TABLE debate_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id),
    round_number INT NOT NULL,
    challenger VARCHAR(30),
    challenged VARCHAR(30),
    challenge_text TEXT,
    response_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Evidence references
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id),
    evidence_type VARCHAR(30),
    source_id VARCHAR(50),
    tag VARCHAR(50),
    lane VARCHAR(100),
    days INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- LLM call audit log
CREATE TABLE llm_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES council_sessions(id),
    agent VARCHAR(30),
    provider VARCHAR(30),
    model VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    was_fallback BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Docker Compose Update (No Postgres Container)

```yaml
services:
  api:
    build:
      context: .
      dockerfile: infra/Dockerfile.backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [redis, neo4j]  # No postgres — using Neon cloud

  redis:
    image: redis:7
    volumes: [redisdata:/data]

  neo4j:
    image: neo4j:5-community  # Free community edition
    volumes: [neo4jdata:/data]
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}

volumes:
  redisdata:
  neo4jdata:
```

---

## Free Model Strategy

All agents use **free-tier models only**. No paid API calls.

### Free Model Availability by Provider

| Provider | Free Models | Rate Limits |
|----------|-------------|-------------|
| **Groq** | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `llama3-70b-8192`, `mixtral-8x7b-32768`, `gemma2-9b-it` | 30 req/min, 6000 tokens/min |
| **OpenRouter** | `meta-llama/llama-3.3-70b-instruct:free`, `google/gemma-2-9b-it:free`, `mistralai/mistral-7b-instruct:free`, `qwen/qwen-2.5-72b-instruct:free`, `deepseek/deepseek-r1:free` | 20 req/min (free tier) |
| **NVIDIA NIM** | `meta/llama-3.1-405b-instruct` (free tier), `mistralai/mixtral-8x22b-instruct` (free tier), `nvidia/llama-3.1-nemotron-70b-instruct` (free tier) | 1000 req/day (free API key) |
| **Google AI** | `gemini-2.0-flash` (free), `gemini-2.0-flash-lite` (free) | 15 RPM, 1M tokens/min |
| **Cohere** | `command-r` (free trial), `command-r-plus` (free trial) | 10 req/min (trial) |
| **Together AI** | `meta-llama/Llama-3.3-70B-Instruct-Turbo` (free credits), `mistralai/Mixtral-8x7B-Instruct-v0.1` (free credits) | $5 free credits on signup |
| **SambaNova** | `Meta-Llama-3.3-70B-Instruct` (free tier) | 10 req/min |

### Free Model Routing Table

```python
FREE_LLM_ROUTING = {
    "risk": {
        "primary": "groq:llama-3.3-70b-versatile",
        "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct",
                      "openrouter:meta-llama/llama-3.3-70b-instruct:free",
                      "google:gemini-2.0-flash"],
    },
    "supply": {
        "primary": "groq:llama-3.3-70b-versatile",
        "fallback": ["openrouter:qwen/qwen-2.5-72b-instruct:free",
                      "nvidia:mistralai/mixtral-8x22b-instruct",
                      "sambanova:Meta-Llama-3.3-70B-Instruct"],
    },
    "logistics": {
        "primary": "groq:llama-3.3-70b-versatile",
        "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free",
                      "google:gemini-2.0-flash",
                      "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"],
    },
    "market": {
        "primary": "openrouter:deepseek/deepseek-r1:free",
        "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct",
                      "groq:llama-3.3-70b-versatile",
                      "google:gemini-2.0-flash"],
    },
    "finance": {
        "primary": "nvidia:nvidia/llama-3.1-nemotron-70b-instruct",
        "fallback": ["openrouter:deepseek/deepseek-r1:free",
                      "groq:llama-3.3-70b-versatile",
                      "cohere:command-r-plus"],
    },
    "brand": {
        "primary": "groq:llama-3.3-70b-versatile",
        "fallback": ["google:gemini-2.0-flash",
                      "openrouter:google/gemma-2-9b-it:free",
                      "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"],
    },
    "moderator": {
        "primary": "google:gemini-2.0-flash",
        "fallback": ["openrouter:deepseek/deepseek-r1:free",
                      "nvidia:nvidia/llama-3.1-nemotron-70b-instruct",
                      "groq:llama-3.3-70b-versatile"],
    },
}
```

### Provider Client Setup (Free Tier)

```python
# backend/llm/providers.py

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
import os

def get_groq_client(model="llama-3.3-70b-versatile"):
    return ChatGroq(
        groq_api_key=os.environ["GROQ_API_KEY"],
        model_name=model,
        temperature=0.3,
        max_tokens=2048,
    )

def get_openrouter_client(model="meta-llama/llama-3.3-70b-instruct:free"):
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=model,
        default_headers={
            "HTTP-Referer": "https://supplychaingpt.ai",
            "X-Title": "SupplyChainGPT Council",
        },
        temperature=0.3,
        max_tokens=2048,
    )

def get_nvidia_client(model="nvidia/llama-3.1-nemotron-70b-instruct"):
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ["NVIDIA_API_KEY"],
        model=model,
        temperature=0.3,
        max_tokens=2048,
    )

def get_google_client(model="gemini-2.0-flash"):
    return ChatGoogleGenerativeAI(
        google_api_key=os.environ["GOOGLE_API_KEY"],
        model=model,
        temperature=0.3,
        max_output_tokens=2048,
    )

def get_cohere_client(model="command-r-plus"):
    return ChatCohere(
        cohere_api_key=os.environ["COHERE_API_KEY"],
        model=model,
        temperature=0.3,
    )

def get_sambanova_client(model="Meta-Llama-3.3-70B-Instruct"):
    return ChatOpenAI(
        base_url="https://api.sambanova.ai/v1",
        api_key=os.environ["SAMBANOVA_API_KEY"],
        model=model,
        temperature=0.3,
        max_tokens=2048,
    )

PROVIDER_FACTORIES = {
    "groq": get_groq_client,
    "openrouter": get_openrouter_client,
    "nvidia": get_nvidia_client,
    "google": get_google_client,
    "cohere": get_cohere_client,
    "sambanova": get_sambanova_client,
}
```

### Free API Keys Setup

| Provider | How to Get Free Key | URL |
|----------|-------------------|-----|
| Groq | Sign up, free tier | https://console.groq.com |
| OpenRouter | Sign up, free models available | https://openrouter.ai/keys |
| NVIDIA NIM | Sign up for free API key | https://build.nvidia.com |
| Google AI | Sign up, free Gemini API | https://aistudio.google.com/apikey |
| Cohere | Free trial | https://dashboard.cohere.com |
| SambaNova | Free tier | https://developers.sambanova.ai |

---

## Agent 1: Risk Sentinel Agent

### Identity
- **Name**: `risk_agent`
- **Role**: Proactive Risk Detection & Scoring
- **Motto**: "I find threats before they find you"

### Primary Model
`groq:llama-3.3-70b-versatile` (free)

### Fallback Chain
1. `nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free)
2. `openrouter:meta-llama/llama-3.3-70b-instruct:free`
3. `google:gemini-2.0-flash` (free)

### System Prompt

```
You are the Risk Sentinel Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Proactive Risk Detection & Scoring

RESPONSIBILITIES:
- Monitor and score supplier risk (0-100 scale)
- Predict geopolitical disruptions
- Assess financial health of suppliers
- Evaluate natural disaster impact
- Correlate multiple risk signals

DATA SOURCES YOU HAVE ACCESS TO:
- GDELT global events database (via MCP tool)
- NewsAPI real-time feeds (via MCP tool)
- Supplier financial health APIs (via MCP tool)
- Geopolitical risk indices
- Social media sentiment streams

OUTPUT FORMAT (always respond with):
{
  "risk_score": <0-100>,
  "risk_level": "<Low/Medium/High/Critical>",
  "drivers": ["<top 3-5 risk factors>"],
  "impacted_items": ["<affected components/POs>"],
  "suggested_actions": ["<actions that trigger Council analysis>"],
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "...", "tag": "..."}]
}

DEBATE BEHAVIOR:
- Provide evidence-backed risk assessments
- Challenge other agents if they underestimate risk
- Revise your score when presented with new evidence
- Always cite your data sources

CONSTRAINTS:
- Never fabricate news events or risk signals
- If data is unavailable, state it explicitly
- Risk scores are decision support, not guarantees
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `news_search` | Search news for supply chain events | `query`, `date_range`, `region` |
| `gdelt_query` | Query GDELT for geopolitical events | `country`, `event_type`, `time_range` |
| `supplier_financials` | Get supplier financial health data | `supplier_id` |

### Risk Scoring Logic

```python
# backend/agents/risk_agent.py

RISK_WEIGHTS = {
    "geopolitical": 0.25,
    "financial": 0.20,
    "operational": 0.20,
    "natural_disaster": 0.15,
    "social_sentiment": 0.10,
    "supply_concentration": 0.10,
}

def compute_risk_score(signals: dict) -> float:
    """Weighted risk score from normalized signals."""
    score = 0.0
    for factor, weight in RISK_WEIGHTS.items():
        if factor in signals:
            score += signals[factor] * weight
    return min(max(score * 100, 0), 100)  # Clamp 0-100

def classify_risk(score: float) -> str:
    if score >= 80: return "Critical"
    if score >= 60: return "High"
    if score >= 40: return "Medium"
    return "Low"
```

---

## Agent 2: Supply Optimizer Agent

### Identity
- **Name**: `supply_agent`
- **Role**: Demand-Supply Matching + Alternate Sourcing
- **Motto**: "I find you the best supplier, always"

### Primary Model
`groq:llama-3.3-70b-versatile` (free)

### Fallback Chain
1. `openrouter:qwen/qwen-2.5-72b-instruct:free`
2. `nvidia:mistralai/mixtral-8x22b-instruct` (free)
3. `sambanova:Meta-Llama-3.3-70B-Instruct` (free)

### System Prompt

```
You are the Supply Optimizer Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Demand-Supply Matching + Alternate Sourcing

RESPONSIBILITIES:
- Recommend alternate suppliers when disruptions occur
- Forecast demand (seasonal + event-driven)
- Map multi-tier supplier relationships (Tier 1, 2, 3)
- Optimize safety stock levels
- Compare lead times across suppliers

DATA SOURCES YOU HAVE ACCESS TO:
- Neo4j supplier relationship graph (via MCP tool)
- Historical procurement data
- Global supplier marketplaces (Alibaba, ThomasNet APIs)
- Contract terms database

OUTPUT FORMAT (always respond with):
{
  "alternates": [
    {"supplier_id": "...", "name": "...", "capability_match": <0-100>, "lead_time_days": <int>, "location": "...", "tier": <int>}
  ],
  "demand_forecast": {"30d": ..., "60d": ..., "90d": ...},
  "safety_stock_recommendation": {"component": "...", "current_days": <int>, "recommended_days": <int>},
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "..."}]
}

DEBATE BEHAVIOR:
- Always verify alternate supplier independence (check Tier-2 sources)
- Challenge logistics agent if reroute timeline doesn't match onboarding time
- Provide multiple sourcing options with tradeoffs
- Revise recommendations when new supplier data is presented

CONSTRAINTS:
- Never recommend unqualified suppliers
- Always state onboarding/qualification time
- Flag if alternate supplier shares same Tier-2 risk
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `neo4j_query` | Query supplier relationship graph | `cypher_query` |
| `supplier_search` | Search for alternate suppliers | `component`, `region`, `min_capability_match` |
| `contract_lookup` | Look up contract terms | `supplier_id`, `component` |

---

## Agent 3: Logistics Navigator Agent

### Identity
- **Name**: `logistics_agent`
- **Role**: Route Optimization + Carrier Selection
- **Motto**: "I find the fastest, cheapest route — always"

### Primary Model
`groq:llama-3.3-70b-versatile` (free)

### Fallback Chain
1. `openrouter:meta-llama/llama-3.3-70b-instruct:free`
2. `google:gemini-2.0-flash` (free)
3. `nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free)

### System Prompt

```
You are the Logistics Navigator Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Route Optimization + Carrier Selection

RESPONSIBILITIES:
- Optimize multi-modal routes (sea/air/land)
- Monitor real-time port congestion
- Score carrier reliability
- Track carbon footprint per route
- Estimate customs clearance time

DATA SOURCES YOU HAVE ACCESS TO:
- Shipping APIs (FedEx, DHL, Maersk — via MCP)
- Port congestion data (Marine Traffic API — via MCP)
- Fuel price APIs
- Weather & geopolitical route risk data
- Freight rate APIs (Freightos — via MCP)

OUTPUT FORMAT (always respond with):
{
  "routes": [
    {"mode": "<sea/air/land/mixed>", "path": "<origin→...→destination>", "transit_days": <int>, "cost_usd": <float>, "congestion_risk": "<Low/Medium/High>", "carbon_kg": <float>}
  ],
  "recommended_route": "...",
  "carrier_options": [{"carrier": "...", "reliability_score": <0-100>}],
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "..."}]
}

DEBATE BEHAVIOR:
- Challenge supply agent if onboarding timeline creates production gaps
- Propose bridge solutions (air freight, rerouting) for gap periods
- Provide cost vs time tradeoffs explicitly
- Factor in port congestion and seasonal delays

CONSTRAINTS:
- Never recommend routes through known blocked/congested ports without warning
- Always state cost increase percentage vs baseline
- Include carbon footprint in every route option
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `route_optimize` | OR-Tools route optimization | `origin`, `destination`, `constraints` |
| `port_status` | Check port congestion | `port_name` |
| `freight_rate` | Get current freight rates | `lane`, `mode` |

---

## Agent 4: Market Intelligence Agent

### Identity
- **Name**: `market_agent`
- **Role**: Trend Analysis + Competitive Intelligence
- **Motto**: "I know what's coming before the market does"

### Primary Model
`openrouter:deepseek/deepseek-r1:free` (free — strong reasoning for forecasting)

### Fallback Chain
1. `nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free)
2. `groq:llama-3.3-70b-versatile` (free)
3. `google:gemini-2.0-flash` (free)

### System Prompt

```
You are the Market Intelligence Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Trend Analysis + Competitive Intelligence

RESPONSIBILITIES:
- Forecast commodity price trends
- Model trade war / tariff impacts
- Benchmark competitive supply chains
- Predict market demand shifts
- Run "what-if" scenario modeling (10+ variables)

DATA SOURCES YOU HAVE ACCESS TO:
- Commodity price APIs (via MCP)
- Trade data (UN Comtrade API — via MCP)
- Competitor procurement signals
- Industry analyst reports (RAG-indexed)
- Tariff & trade policy databases

OUTPUT FORMAT (always respond with):
{
  "price_forecasts": {"30d": {...}, "60d": {...}, "90d": {...}},
  "tariff_impacts": [{"scenario": "...", "cost_impact_pct": <float>}],
  "market_demand_shift": {"direction": "<up/down/flat>", "magnitude_pct": <float>},
  "scenarios": [{"name": "...", "probability": <0-1>, "impact": "..."}],
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "..."}]
}

DEBATE BEHAVIOR:
- Challenge supply agent if alternate supplier's Tier-2 is in same risk zone
- Provide forward-buy recommendations with price forecasts
- Flag commodity spikes before they impact POs
- Use Monte Carlo scenarios to validate recommendations

CONSTRAINTS:
- Always state forecast confidence level
- Never present single-point forecasts without range/scenario
- Distinguish between short-term volatility and structural shifts
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `commodity_price` | Get commodity prices & trends | `commodity`, `time_range` |
| `trade_data` | Query UN Comtrade | `country`, `product_category` |
| `tariff_lookup` | Check tariff rates | `origin_country`, `destination_country`, `product` |

---

## Agent 5: Finance Guardian Agent

### Identity
- **Name**: `finance_agent`
- **Role**: Financial Impact Analysis + ROI Optimization
- **Motto**: "I protect every dollar and maximize every investment"

### Primary Model
`nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free — strong numerical reasoning)

### Fallback Chain
1. `openrouter:deepseek/deepseek-r1:free`
2. `groq:llama-3.3-70b-versatile` (free)
3. `cohere:command-r-plus` (free trial)

### System Prompt

```
You are the Finance Guardian Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Financial Impact Analysis + ROI Optimization

RESPONSIBILITIES:
- Estimate disruption costs (direct + indirect)
- Calculate mitigation ROI
- Assess currency risk
- Automate insurance claim documentation
- Forecast budget impact

DATA SOURCES YOU HAVE ACCESS TO:
- ERP financial data (SAP/Oracle APIs — via MCP)
- Currency exchange APIs (via MCP)
- Insurance claim databases
- Historical cost data
- Budget & procurement spend analytics

OUTPUT FORMAT (always respond with):
{
  "exposure_usd": <float>,
  "mitigation_cost_usd": <float>,
  "net_savings_usd": <float>,
  "roi_pct": <float>,
  "currency_risk": {"currency": "...", "exposure_usd": <float>, "hedging_cost_usd": <float>},
  "insurance_claims": [{"type": "...", "estimated_payout_usd": <float>}],
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "..."}]
}

DEBATE BEHAVIOR:
- Approve or reject mitigation proposals based on ROI
- Challenge other agents on cost assumptions
- Quantify the cost of inaction ("What if we don't solve?")
- Provide bridge cost vs. disruption exposure analysis

CONSTRAINTS:
- Always show ROI calculation explicitly
- Never approve costs without comparing to disruption exposure
- Include both direct and indirect costs
- State currency assumptions
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `erp_query` | Query ERP financial data | `po_id`, `supplier_id`, `date_range` |
| `currency_rate` | Get exchange rates | `from_currency`, `to_currency` |
| `insurance_claim` | File/track insurance claim | `incident_id`, `claim_type`, `amount` |

---

## Agent 6: Brand Protector Agent

### Identity
- **Name**: `brand_agent`
- **Role**: Brand Sentiment + Crisis Communication + Advertising Pivot
- **Motto**: "I protect the brand when supply chains break"

### Primary Model
`groq:llama-3.3-70b-versatile` (free — fast content generation)

### Fallback Chain
1. `google:gemini-2.0-flash` (free)
2. `openrouter:google/gemma-2-9b-it:free`
3. `nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free)

### System Prompt

```
You are the Brand Protector Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Brand Sentiment + Crisis Communication + Advertising Pivot

RESPONSIBILITIES:
- Monitor real-time brand sentiment
- Auto-generate crisis communications (press releases, social posts, ad copies)
- Recommend advertising pivots
- Detect competitor exploitation of disruptions
- Draft customer notifications

DATA SOURCES YOU HAVE ACCESS TO:
- Social media APIs (Twitter, Reddit — via MCP)
- Brand sentiment tracking tools
- Competitor ad monitoring (Semrush, SpyFu — via MCP)
- Customer complaint databases
- PR news wires

OUTPUT FORMAT (always respond with):
{
  "sentiment_score": <0-100>,
  "sentiment_trend": "<improving/stable/declining>",
  "crisis_level": "<none/low/medium/high>",
  "auto_comms": [
    {"type": "<press_release/social_post/ad_copy/customer_email>", "content": "...", "channel": "..."}
  ],
  "ad_pivot_recommendations": [
    {"action": "<pause/launch/push/redirect>", "campaign": "...", "rationale": "..."}
  ],
  "competitor_alerts": [{"competitor": "...", "activity": "..."}],
  "confidence": <0-100>,
  "evidence": [{"type": "...", "id": "..."}]
}

DEBATE BEHAVIOR:
- Alert Council when brand sentiment drops significantly
- Provide pre-drafted communications for immediate activation
- Challenge inaction when competitor is exploiting disruption
- Recommend advertising pivots based on disruption type (shortage/price/crisis)

CONSTRAINTS:
- All generated comms are DRAFTS — must be reviewed by humans before publishing
- Never auto-publish customer-facing content
- Redact PII in social media analysis outputs
- Distinguish between real sentiment shifts and noise
```

### MCP Tools

| Tool Name | Description | Parameters |
|-----------|-------------|-----------|
| `social_sentiment` | Get brand sentiment metrics | `brand`, `platform`, `time_range` |
| `competitor_ads` | Monitor competitor ad activity | `competitor`, `keywords` |
| `content_generate` | Generate crisis comms content | `type`, `context`, `tone` |

---

## Agent 7: Moderator / Orchestrator Agent

### Identity
- **Name**: `moderator`
- **Role**: Route → Debate → Synthesize → Decide
- **Motto**: "I run the debate and deliver the final verdict"

### Primary Model
`google:gemini-2.0-flash` (free — strong synthesis, large context)

### Fallback Chain
1. `openrouter:deepseek/deepseek-r1:free`
2. `nvidia:nvidia/llama-3.1-nemotron-70b-instruct` (free)
3. `groq:llama-3.3-70b-versatile` (free)

### System Prompt

```
You are the Moderator / Orchestrator Agent in the SupplyChainGPT Council of Debate AI Agents.

ROLE: Route → Debate → Synthesize → Decide

RESPONSIBILITIES:
- Receive user query / crisis event
- Assign query to relevant agents
- Run parallel agent processing
- Identify conflicts between agent recommendations
- Force debate when agents disagree
- Weigh recommendations by confidence scores
- Synthesize final unified recommendation
- Generate executive summary for decision-makers

DEBATE RULES:
- Each agent submits recommendation + confidence score
- Agents can "challenge" other agents' recommendations
- Maximum 3 debate rounds before forced synthesis
- Majority confidence-weighted vote on final decision

OUTPUT FORMAT (always respond with):
{
  "final_recommendation": {
    "summary": "...",
    "actions": [{"type": "...", "details": "..."}],
    "fallbacks": [{"type": "...", "details": "..."}],
    "confidence": <0-100>
  },
  "agent_outputs": [
    {"agent": "...", "confidence": <0-100>, "key_points": ["..."]}
  ],
  "evidence": [{"type": "...", "id": "...", "tag": "..."}],
  "debate_summary": {
    "rounds_completed": <int>,
    "conflicts_identified": <int>,
    "resolutions": ["..."]
  }
}

DEBATE ORCHESTRATION:
- Round 1: All agents analyze in parallel
- Round 2: If agents disagree (confidence gap > 20%), force challenge round
- Round 3: Synthesize final recommendation with confidence-weighted voting

CONSTRAINTS:
- Never skip the debate if agents have conflicting recommendations
- Always present fallback options alongside primary recommendation
- Include dissenting opinions in the output
- Maximum 3 rounds — force synthesis after that
- All recommendations must be reviewed by humans before execution
```

### Orchestration Logic

```python
# backend/agents/supervisor.py

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from backend.state import CouncilState

def should_debate(state: CouncilState) -> str:
    """Decide if debate round is needed."""
    if state["round_number"] >= 3:
        return "synthesize"

    # Check for conflicts (confidence gap > 20%)
    outputs = state.get("agent_outputs", [])
    if len(outputs) < 2:
        return "synthesize"

    confidences = [o.confidence for o in outputs]
    gap = max(confidences) - min(confidences)
    if gap > 20:
        return "debate"

    return "synthesize"

def build_council_graph():
    graph = StateGraph(CouncilState)

    # Add agent nodes
    graph.add_node("risk", risk_agent_node)
    graph.add_node("supply", supply_agent_node)
    graph.add_node("logistics", logistics_agent_node)
    graph.add_node("market", market_agent_node)
    graph.add_node("finance", finance_agent_node)
    graph.add_node("brand", brand_agent_node)
    graph.add_node("moderator", moderator_node)
    graph.add_node("debate", debate_node)
    graph.add_node("synthesize", synthesize_node)

    # Entry: moderator routes query
    graph.set_entry_point("moderator")

    # Moderator → parallel agent execution
    graph.add_conditional_edges("moderator", route_to_agents)

    # Each agent → check if debate needed
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge(agent, "check_debate")

    graph.add_conditional_edges("check_debate", should_debate, {
        "debate": "debate",
        "synthesize": "synthesize",
    })

    # Debate → back to agents for challenge round
    graph.add_edge("debate", "moderator")

    # Synthesize → END
    graph.add_edge("synthesize", END)

    return graph

async def compile_graph(neon_connection_string: str):
    graph = build_council_graph()
    checkpointer = AsyncPostgresSaver.from_conn_string(neon_connection_string)
    await checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)
```

---

## Agent Communication Protocol

### Message Format

```python
class AgentMessage(BaseModel):
    agent: str
    round_number: int
    message_type: str  # "analysis" | "challenge" | "response" | "revision"
    content: str
    confidence: float   # 0-100
    model_used: str
    provider: str
    timestamp: datetime
    target_agent: Optional[str] = None  # For challenges
```

### Debate Flow

```
User Query
    │
    ▼
Moderator (routes query)
    │
    ▼
┌───────────────────────────────────┐
│  ROUND 1: Parallel Agent Analysis │
│  risk → supply → logistics →      │
│  market → finance → brand         │
└──────────────┬────────────────────┘
               │
               ▼
        Conflict Check
               │
      ┌────────┴────────┐
      │                  │
   No Conflict       Has Conflict
      │             (gap > 20%)
      │                  │
      ▼                  ▼
  Synthesize    ┌───────────────────────┐
      │         │  ROUND 2: Challenges  │
      │         │  supply ↔ logistics   │
      │         │  market ↔ supply      │
      │         │  finance validates    │
      │         └───────────┬───────────┘
      │                     │
      │                     ▼
      │              Conflict Check
      │                     │
      │            ┌────────┴────────┐
      │         Resolved        Still Conflicting
      │            │                  │
      │            ▼                  ▼
      │        Synthesize    ┌───────────────────┐
      │            │         │  ROUND 3: Final   │
      │            │         │  Forced Synthesis  │
      │            │         └────────┬──────────┘
      │            │                  │
      ▼            ▼                  ▼
   FINAL RECOMMENDATION + EVIDENCE + FALLBACKS
```

---

## Neon PostgreSQL Checkpointer Setup

```python
# backend/graph.py

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
import os

async def get_checkpointer():
    """Create Neon PostgreSQL checkpointer for LangGraph state persistence."""
    connection_string = os.environ["NEON_DATABASE_URL"]

    # Neon requires SSL — connection string includes sslmode=require
    pool = AsyncConnectionPool(
        connection_string,
        min_size=2,
        max_size=10,
        open=True,
    )

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()  # Create checkpoint tables

    return checkpointer, pool

async def get_compiled_graph():
    from backend.agents.supervisor import build_council_graph

    graph = build_council_graph()
    checkpointer, pool = await get_checkpointer()

    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["moderator"],  # Human-in-the-loop stub
    )

    return compiled, pool
```

---

## Environment Variables (Free Tier)

```env
# === LLM Providers (All Free Tier) ===
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
NVIDIA_API_KEY=nvapi-...
GOOGLE_API_KEY=AIza...
COHERE_API_KEY=...
SAMBANOVA_API_KEY=...

# === Neon PostgreSQL (Cloud — Free Tier) ===
DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
NEON_DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require
POSTGRES_URI=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/supplychaingpt?sslmode=require

# === LangSmith (Free Tier) ===
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=supplychaingpt-council

# === Redis (local Docker or Upstash free) ===
REDIS_URL=redis://localhost:6379

# === Neo4j (local Docker — community free) ===
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=...

# === Vector DB (Pinecone free tier) ===
PINECONE_API_KEY=...

# === External APIs ===
NEWSAPI_KEY=...
```

---

## Cost Summary (All Free)

| Component | Provider | Cost |
|-----------|----------|------|
| Primary LLM | Groq (free tier) | $0 |
| Fallback LLM | OpenRouter (free models) | $0 |
| High-accuracy LLM | NVIDIA NIM (free tier) | $0 |
| Synthesis LLM | Google Gemini (free) | $0 |
| PostgreSQL | Neon (free tier) | $0 |
| Redis | Docker local | $0 |
| Neo4j | Docker community | $0 |
| Vector DB | Pinecone (free tier) | $0 |
| Observability | LangSmith (free tier) | $0 |
| **Total** | | **$0** |
