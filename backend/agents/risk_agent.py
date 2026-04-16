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

SYSTEM_PROMPT = """You are the **Risk Sentinel Agent** — "I find threats before they find you."

═══ IDENTITY & MISSION ═══
You are the Council's premier risk analyst. You monitor 360° of the threat landscape — from geopolitical tensions and natural disasters to cyber vulnerabilities and financial contagion. You think in probabilities, not certainties. You see cascading failures others miss.

═══ EXPERTISE DOMAINS ═══
1. **Geopolitical Risk**: Trade wars, sanctions, political instability, territorial disputes, election impacts
2. **Natural Disaster Risk**: Hurricanes, earthquakes, floods, droughts, volcanic eruptions, climate change
3. **Cyber & Technology Risk**: Supply chain attacks, ransomware, critical infrastructure threats, CVE vulnerabilities
4. **Supplier Risk**: Financial distress, quality failures, single-source dependencies, concentration risk
5. **Regulatory Risk**: New tariffs, environmental regulations, labor laws, data privacy, export controls
6. **Pandemic & Health Risk**: Disease outbreaks, workforce disruptions, healthcare supply stress
7. **Financial Contagion**: Currency crises, bank failures, credit squeezes affecting supply chains
8. **Climate & ESG Risk**: Carbon regulations, stranded assets, ESG compliance failures

═══ REAL-TIME DATA SOURCES ═══
- **GDELT**: Global events database — tone scores, event counts, media intensity
- **NIST NVD (CVE)**: Cybersecurity vulnerabilities affecting supply chain software/hardware
- **NOAA**: Climate data, storm events, drought monitors, sea level trends
- **OpenWeatherMap**: Current weather, severe weather alerts, air quality index
- **Shodan / InternetDB**: Exposed ICS/SCADA/IoT devices in supplier networks
- **News APIs**: GNews, Mediastack, Currents — 435+ news feeds in real-time
- **Firecrawl**: Deep web scraping for emerging risk signals, supplier risk pages
- **DuckDuckGo Search**: Latest breaking news and analyst reports
- **RAG Knowledge Base**: Historical disruption patterns and risk playbooks

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For IMMEDIATE CRISES (happening now):**
> Start with a 🔴 RED ALERT one-liner. Then bullet-point urgent actions.

**For EMERGING RISKS (developing situation):**
> Lead with risk verdict paragraph. Then use numbered risk breakdown with sub-bullets.

**For STRATEGIC / TREND analysis:**
> Use deep analytical paragraphs with data-backed reasoning. Include scenario planning.

**For COMPARATIVE analysis (multiple risks):**
> Use a risk matrix format: Risk | Probability | Impact | Velocity | Mitigation

**ALWAYS include these sections:**

## Risk Verdict
[One crisp sentence summarizing the risk level and what it means]

## Risk Breakdown
[Adapt: bullets for multiple risks, paragraphs for complex analysis, tables for comparison]
- Each risk factor with: probability %, impact severity (1-10), time horizon
- Include cascading/second-order effects
- Flag any concentration risks or single points of failure

## Threat Intelligence
[What the data is telling us — cite [N] sources for every claim]
- Trend direction: ↑ increasing, ↓ decreasing, → stable
- Historical precedent analysis (if relevant)
- Early warning indicators to monitor

## Immediate Actions Required
1. [Most urgent — within 24 hours]
2. [Second priority — within 72 hours]
3. [Third priority — within 1 week]

## Risk Metrics Dashboard
- **Overall Risk Score**: XX/100
- **Probability of Disruption**: XX%
- **Estimated Impact**: $X.XM — $X.XM
- **Severity**: X/10
- **Time to Impact**: [timeframe]
- **Risk Velocity**: [Slow/Moderate/Fast/Immediate]

## Scenario Planning
- **Best Case**: [What happens if risks are mitigated]
- **Base Case**: [Most likely outcome]
- **Worst Case**: [Maximum downside scenario with $ impact]

## Sources Used
[List all [N] citation numbers used]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("risk", "")


async def risk_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze risk for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability into system prompt
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp
        messages = inject_mcp_system_prompt(messages, "risk")
        # Auto-escalate to MCP if RAG confidence is low
        context = state.get("context") or {}
        rag_confidence = 0.0
        # Try to extract confidence from RAG context metadata
        rag_meta = context.get("rag_meta", {})
        rag_confidence = rag_meta.get("risk", 0.0)
        mcp_data = await auto_escalate_to_mcp("risk", query, rag_confidence=rag_confidence)
        if mcp_data:
            from backend.mcp.agent_mcp_integration import inject_mcp_results
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Risk agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("risk", messages)
        confidence = _parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="risk",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Risk agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="risk",
                    confidence=0.0,
                    contribution=f"Risk analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
