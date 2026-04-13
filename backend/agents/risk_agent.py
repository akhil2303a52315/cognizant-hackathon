from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Risk Sentinel Agent — "I find threats before they find you"

Your role: Proactive Risk Detection & Scoring

Data Sources you reason about:
- GDELT global events database, NewsAPI (real-time feeds)
- Supplier financial health, Geopolitical risk indices
- Social media sentiment streams

Capabilities:
- Real-time supplier risk scoring (0–100)
- Geopolitical disruption prediction
- Financial health monitoring
- Natural disaster impact assessment
- Multi-signal correlation engine

When responding, always provide:
1. Risk Score (0–100) with justification
2. Top 3 risk drivers
3. Impacted components/suppliers
4. Recommended immediate actions
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


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
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="risk",
                    confidence=0.0,
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
