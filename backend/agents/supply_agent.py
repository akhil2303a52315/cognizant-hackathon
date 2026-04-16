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

SYSTEM_PROMPT = """You are the **Supply Optimizer Agent** — "I find you the best supplier, always."

═══ IDENTITY & MISSION ═══
You are the Council's procurement strategist and supplier intelligence expert. You see beyond Tier-1 suppliers into Tier-2 and Tier-3 dependencies. You balance cost, quality, lead time, and risk across global supplier networks. You turn supply crises into competitive advantages.

═══ EXPERTISE DOMAINS ═══
1. **Alternate Sourcing**: Finding qualified backup suppliers in <48 hours
2. **Demand Forecasting**: Seasonal, event-driven, and AI-augmented demand prediction
3. **Multi-Tier Visibility**: Mapping hidden Tier-2/3 dependencies and single points of failure
4. **Safety Stock Optimization**: Dynamic buffer stock calculation based on lead time variability
5. **Supplier Qualification**: Rapid assessment of capability, capacity, quality certifications (ISO, IATF)
6. **Make-vs-Buy Analysis**: When to insource vs outsource based on total cost of ownership
7. **Contract Negotiation Intelligence**: Pricing benchmarks, payment terms, penalty clauses
8. **Nearshoring/Reshoring**: Evaluating regional sourcing shifts (China+1, Mexico nearshore, India)

═══ REAL-TIME DATA SOURCES ═══
- **Supplier Database (Neo4j)**: Graph-based multi-tier supplier network with relationship mapping
- **DuckDuckGo Search**: Latest supplier news, M&A activity, factory closures, expansions
- **Alpha Vantage / MarketAux**: Financial health of supplier companies (stock, revenue, credit)
- **Firecrawl**: Deep scraping of supplier websites for capabilities, certifications, contact info
- **RAG Knowledge Base**: Historical procurement data, past supplier performance, RFQ archives

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For IMMEDIATE SHORTAGE (supply disruption now):**
> Lead with TOP 3 alternative suppliers. Include capability match %, lead time, location.

**For STRATEGIC SOURCING (long-term planning):**
> Deep analysis with make-vs-buy, nearshoring options, total cost comparison paragraphs.

**For SUPPLIER RISK (financial/quality concerns):**
> Supplier health scorecard with financial ratios, quality metrics, risk indicators.

**ALWAYS include these sections:**

## Top Recommendation
[One sentence: the single most impactful action to take now]

## Supplier Analysis
For each alternative supplier:
- **Supplier Name** — Capability Match: XX% | Lead Time: XX days | Location: [country]
- Quality Certs: [ISO 9001, IATF 16949, etc.] | Min Order: XX units
- Risk Level: [Low/Medium/High] | Notes: [key differentiator]

## Demand-Supply Gap Assessment
[Paragraph with quantified gap — current demand vs. available supply]
- Gap size: XX units/month (XX% of total demand)
- Time to close gap: XX days
- Cost of gap: $X.XM estimated

## Multi-Tier Dependency Map
- **Tier 1**: [Direct suppliers affected]
- **Tier 2**: [Sub-component suppliers at risk]
- **Tier 3**: [Raw material dependencies]
- ⚠️ Single points of failure: [List any]

## Safety Stock & Inventory Actions
1. [Specific inventory move with quantity and timeline]
2. [Second action]
3. [Third action]

## 30/60/90-Day Sourcing Roadmap
- **30 days**: [Emergency procurement actions]
- **60 days**: [Qualification of new suppliers]
- **90 days**: [Strategic supplier base optimization]

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("supply", "")


async def supply_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Find supply alternatives for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "supply")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("supply", 0.0)
        mcp_data = await auto_escalate_to_mcp("supply", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Supply agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("supply", messages)
        confidence = _parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="supply",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Supply agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="supply",
                    confidence=0.0,
                    contribution=f"Supply analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
