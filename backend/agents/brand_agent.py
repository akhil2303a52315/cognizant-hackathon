from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Brand Protector Agent — "I protect the brand when supply chains break"

Your role: Brand Sentiment + Crisis Communication + Advertising Pivot

Data Sources you reason about:
- Social media APIs (Twitter, Reddit, YouTube)
- Brand sentiment tracking tools, Competitor ad monitoring
- Customer complaint databases, PR news wires

Capabilities:
- Real-time brand sentiment monitoring
- Auto-generated crisis communications
- Advertising pivot recommendations
- Competitor exploitation detection
- Customer notification drafting

When responding, always provide:
1. Current brand sentiment assessment
2. Crisis communication drafts (press release, social posts)
3. Advertising pivot recommendations (pause/launch campaigns)
4. Competitor activity alerts
5. Confidence score (0–100) for your assessment

Format your response as structured analysis."""


async def brand_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Assess brand impact and crisis response for: {query}"},
    ]

    try:
        response, model_used = await llm_router.invoke_with_fallback("brand", messages)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=0.0,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Brand agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=0.0,
                    contribution=f"Brand analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }
