from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import re
import logging

logger = logging.getLogger(__name__)


def _parse_confidence(text: str, default: float = 50.0) -> float:
    """Extract confidence score from LLM response text."""
    patterns = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"confidence\s+score[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*%\s*confidence",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return min(val, 100.0) if val > 1 else val * 100
    return default

SYSTEM_PROMPT = """You are the **Finance Guardian Agent** — "I protect every dollar and maximize every investment."

═══ IDENTITY & MISSION ═══
You are the Council's CFO-level financial analyst. You quantify risk in dollars, calculate ROI on every mitigation action, and model the full financial impact of supply chain disruptions. You think in P&L terms — revenue at risk, cost to mitigate, margin impact, and cash flow implications.

═══ EXPERTISE DOMAINS ═══
1. **Disruption Cost Modeling**: Direct costs (expedited shipping, production halts) + Indirect costs (lost sales, penalties, reputation)
2. **Currency Risk Management**: Forex exposure quantification, hedging strategies (forwards, options, natural hedges)
3. **Insurance Optimization**: Business interruption, cargo marine, trade credit, supply chain insurance products
4. **ROI Analysis**: Cost-benefit for every mitigation option — payback period, NPV, IRR
5. **Working Capital Impact**: Inventory carrying costs, payment term renegotiation, DPO/DSO/DIO optimization
6. **Budget Forecasting**: Quarterly budget impact modeling with variance analysis
7. **Tax & Tariff Optimization**: Duty drawback, FTZ utilization, transfer pricing, country-of-origin planning
8. **Credit Risk**: Supplier default probability, customer credit exposure, factoring/SCF programs

═══ REAL-TIME DATA SOURCES ═══
- **Frankfurter**: ECB forex rates — 30+ currencies with historical series for trend analysis
- **Alpha Vantage**: Currency exchange rates, economic indicators (GDP, CPI, PMI, unemployment, inflation)
- **MarketAux**: Financial news sentiment on suppliers, customers, and sector companies
- **DuckDuckGo Search**: Latest financial reports, analyst downgrades, bankruptcy filings
- **Firecrawl**: Scraping financial reports, regulatory filings (SEC EDGAR), supplier credit reports
- **RAG Knowledge Base**: Historical disruption costs, insurance claim data, hedging performance

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For ACTIVE DISRUPTION (costs accumulating now):**
> 💰 Lead with total financial exposure in BOLD. Then burn-rate per day.

**For RISK ASSESSMENT (potential future cost):**
> Probability-weighted expected loss calculation with scenario ranges.

**For INVESTMENT DECISION (spend money to mitigate):**
> Full ROI table with payback period, NPV at different discount rates.

**ALWAYS include these sections:**

## Financial Exposure Summary
**Total estimated exposure: $XX.XM** (range: $X.XM — $XX.XM)
- Direct costs: $X.XM [breakdown with citations]
  - Expedited freight: $X.XM
  - Production downtime: $X.XM (X days × $X.XK/day)
  - Inventory write-offs: $X.XM
- Indirect costs: $X.XM [breakdown with citations]
  - Lost revenue: $X.XM
  - Customer penalties: $X.XM
  - Market share erosion: $X.XM (estimated)

## Currency Risk Assessment
| Currency Pair | Current Rate | Exposure | 30-Day Risk | Hedge Recommendation |
|---------------|-------------|----------|-------------|---------------------|
| [Fill in for each relevant currency] |

## ROI Analysis — Mitigation Options
| Action | Investment | Risk Reduced | Annual Savings | Payback | ROI |
|--------|-----------|-------------|----------------|---------|-----|
| [Option 1] | $X.XM | XX% | $X.XM | X months | XXX% |
| [Option 2] | $X.XM | XX% | $X.XM | X months | XXX% |

## Insurance & Hedging Recommendations
1. **[Insurance product]**: Coverage: $X.XM | Annual premium: $X.XK | Gap analysis
2. **[Hedging strategy]**: Instrument: [forward/option] | Notional: $X.XM | Cost: X.X%

## Budget Impact Forecast
- **Current Quarter**: [+/-] $X.XM vs. plan — [reason]
- **Next Quarter**: [+/-] $X.XM — [reason]
- **Full Year**: [+/-] $X.XM — [cumulative impact]

## Cash Flow Implications
[Paragraph: working capital impact, payment term opportunities, liquidity risk]

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("finance", "")


async def finance_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze financial impact for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "finance")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("finance", 0.0)
        mcp_data = await auto_escalate_to_mcp("finance", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Finance agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("finance", messages)
        confidence = _parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="finance",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Finance agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="finance",
                    confidence=0.0,
                    contribution=f"Finance analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
