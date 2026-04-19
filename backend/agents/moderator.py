from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Moderator / Orchestrator Agent — "I run the debate and deliver the final verdict"

Your role: Route → Debate → Synthesize → Decide

Responsibilities:
- Receive user query / crisis event
- Assign query to relevant agents
- Run parallel agent processing
- Identify conflicts between agent recommendations
- Force debate when agents disagree
- Weigh recommendations by confidence scores
- Synthesize final unified recommendation
- Generate executive summary for decision-makers
- Can use Firecrawl web scraping (web_scrape, web_search, web_crawl) to gather additional context

Debate Rules:
- Each agent submits recommendation + confidence score
- Agents can "challenge" other agents' recommendations
- Maximum 3 debate rounds before forced synthesis
- Majority confidence-weighted vote on final decision

CRITICAL OUTPUT FORMAT REQUIREMENT:
You MUST respond with valid JSON containing ALL of these fields:
{
  "executive_summary": "Brief executive summary of the final decision",
  "final_verdict": "Clear final recommendation and decision",
  "confidence_assessment": {
    "overall": 85,
    "data_quality": 90,
    "consensus_level": 80
  },
  "reliable_agents": ["agent1", "agent2", "agent3"],
  "priority_actions": [
    {
      "action": "Specific action item",
      "justification": "Why this action is critical",
      "timeline": "Immediate/30 days/60 days/90 days"
    }
  ],
  "strategic_roadmap": {
    "day30": "Short-term objectives",
    "day60": "Mid-term objectives", 
    "day90": "Long-term objectives"
  },
  "unresolved_risks": ["Risk 1", "Risk 2"],
  "formatted_response": "# Executive Summary\\n\\n[Professional markdown summary]\\n\\n## Final Verdict\\n\\n[Clear recommendation]\\n\\n## Confidence Assessment\\n\\n- **Overall Confidence:** 85%\\n- **Data Quality:** 90%\\n- **Consensus Level:** 80%\\n\\n## Reliable Agents\\n\\n[Agent names]\\n\\n## Priority Actions\\n\\n1. **Action 1** - Justification (Timeline: Immediate)\\n2. **Action 2** - Justification (Timeline: 30 days)\\n\\n## Strategic Roadmap\\n\\n### Day 30\\n[Objectives]\\n\\n### Day 60\\n[Objectives]\\n\\n### Day 90\\n[Objectives]\\n\\n## Unresolved Risks\\n\\n- [Risk 1]\\n- [Risk 2]"
}

The "formatted_response" field must contain clean, professional markdown that will be displayed to users. Include proper headings, bullet points, and maintain citations using [1], [2] format when referencing sources."""


async def moderator_parse(state: CouncilState) -> dict:
    """Round 0: Parse query and initialize council session."""
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Parse and route this supply chain query: {query}"},
    ]

    try:
        response, model_used = await llm_router.invoke_with_fallback("moderator", messages)
        return {
            "round_number": 1,
            "messages": state.get("messages", []) + [
                {"role": "moderator", "content": response.content}
            ],
        }
    except Exception as e:
        logger.error(f"Moderator parse failed: {e}")
        return {"round_number": 1}


async def moderator_synthesize(state: CouncilState) -> dict:
    """Final synthesis: Combine debate results, predictions, fallbacks, and brand data.

    Day 5 upgrade: Uses DebateEngine results (debate_rounds, confidence, risk_score)
    and tiered fallback options from FallbackEngine. Also incorporates brand sentiment
    and predictions data for a comprehensive final recommendation.
    """
    agent_outputs = state.get("agent_outputs", [])
    query = state.get("query", "")
    debate_rounds = state.get("debate_rounds", [])
    predictions = state.get("predictions", [])
    tiered_fallbacks = state.get("tiered_fallbacks", [])
    brand_sentiment = state.get("brand_sentiment")
    risk_score = state.get("risk_score", 0)
    debate_confidence = state.get("confidence", 0)

    # Build comprehensive synthesis context
    agent_summaries = "\n\n".join([
        f"**{o.agent.upper()} Agent** (Confidence: {o.confidence}%):\n{o.contribution[:500]}"
        for o in agent_outputs
    ])

    debate_summary = ""
    if debate_rounds:
        debate_summary = "\n\n**Debate Results:**\n"
        for r in debate_rounds:
            debate_summary += (
                f"- Round {r.get('round_number', '?')} ({r.get('phase', '?')}): "
                f"Confidence={r.get('round_confidence', 0)}%, "
                f"Consensus={r.get('consensus_points', [])}, "
                f"Disagreements={r.get('key_disagreements', [])}\n"
            )

    predictions_summary = ""
    if predictions:
        predictions_summary = "\n\n**Predictions:**\n"
        for p in predictions:
            predictions_summary += (
                f"- {p.get('metric', '?')} ({p.get('method', '?')}): "
                f"{p.get('point_estimate', 0):.2f} "
                f"[{p.get('ci_lower', 0):.2f}, {p.get('ci_upper', 0):.2f}] "
                f"confidence={p.get('confidence', 0):.2f}\n"
            )

    fallbacks_summary = ""
    if tiered_fallbacks:
        fallbacks_summary = "\n\n**Tiered Fallback Options:**\n"
        for f in tiered_fallbacks:
            fallbacks_summary += (
                f"- Tier {f.get('tier', '?')}: {f.get('name', '?')} — "
                f"Cost=${f.get('cost_estimate_usd', 0):,.0f}, "
                f"Time={f.get('time_to_implement_days', '?')} days, "
                f"Risk Reduction={f.get('risk_reduction_pct', 0)}%, "
                f"ROI={f.get('roi_pct', 0)}%\n"
            )

    brand_summary = ""
    if brand_sentiment:
        brand_summary = (
            f"\n\n**Brand Sentiment:** {brand_sentiment.get('overall_sentiment', 'unknown')} "
            f"(score: {brand_sentiment.get('sentiment_score', 0):.2f})\n"
            f"Crisis Keywords: {brand_sentiment.get('crisis_keywords', [])}\n"
        )
        if brand_sentiment.get("crisis_comm_draft"):
            brand_summary += f"Crisis Communication Draft Available: Yes\n"
        if brand_sentiment.get("ad_pivot_recommendation"):
            brand_summary += f"Ad Pivot Recommendation Available: Yes\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""
Original Query: {query}
Risk Score: {risk_score}/100
Debate Confidence: {debate_confidence:.0%}

Agent Outputs:
{agent_summaries}
{debate_summary}
{predictions_summary}
{fallbacks_summary}
{brand_summary}

Synthesize the final unified recommendation. Weigh by confidence and debate results.
Include the tiered fallback options and predictions in your recommendation.
Provide an overall council confidence score (0-100) and risk score (0-100).
"""}
    ]

    # Inject RAG context for moderator if available
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    moderator_rag = rag_contexts.get("moderator", "")
    if moderator_rag:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, moderator_rag)

    # Inject MCP context for moderator if available
    mcp_contexts = context.get("mcp_contexts") or {}
    moderator_mcp = mcp_contexts.get("moderator", "")
    if moderator_mcp:
        from backend.mcp.agent_mcp_integration import inject_mcp_results
        messages = inject_mcp_results(messages, moderator_mcp)

    try:
        response, model_used = await llm_router.invoke_with_fallback("moderator", messages)

        # Try to parse JSON response first
        import json
        import re
        formatted_response = None
        final_confidence = debate_confidence
        final_risk = risk_score
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                json_data = json.loads(json_match.group())
                
                # Extract formatted_response if available
                if "formatted_response" in json_data:
                    formatted_response = json_data["formatted_response"]
                
                # Extract confidence assessment
                if "confidence_assessment" in json_data:
                    conf_assessment = json_data["confidence_assessment"]
                    if isinstance(conf_assessment, dict) and "overall" in conf_assessment:
                        final_confidence = conf_assessment["overall"] / 100.0 if conf_assessment["overall"] > 1 else conf_assessment["overall"]
                
                # Store the full JSON for internal processing
                json_response = json_data
            else:
                # Fallback to parsing plain text
                json_response = {"raw_response": response.content}
                
                # Parse confidence from response (use debate confidence as fallback)
                conf_match = re.search(r"(?:overall\s+)?council\s+confidence[:\s]+(\d+(?:\.\d+)?)", response.content, re.IGNORECASE)
                if conf_match:
                    val = float(conf_match.group(1))
                    final_confidence = val / 100.0 if val > 1 else val

                # Parse risk score
                risk_match = re.search(r"risk\s+score[:\s]+(\d+(?:\.\d+)?)", response.content, re.IGNORECASE)
                if risk_match:
                    final_risk = float(risk_match.group(1))
                    final_risk = final_risk if final_risk <= 100 else final_risk * 100
                    
        except json.JSONDecodeError:
            # If JSON parsing fails, use raw response
            json_response = {"raw_response": response.content}
            formatted_response = None
            
            # Parse confidence from response (use debate confidence as fallback)
            conf_match = re.search(r"(?:overall\s+)?council\s+confidence[:\s]+(\d+(?:\.\d+)?)", response.content, re.IGNORECASE)
            if conf_match:
                val = float(conf_match.group(1))
                final_confidence = val / 100.0 if val > 1 else val

            # Parse risk score
            risk_match = re.search(r"risk\s+score[:\s]+(\d+(?:\.\d+)?)", response.content, re.IGNORECASE)
            if risk_match:
                final_risk = float(risk_match.group(1))
                final_risk = final_risk if final_risk <= 100 else final_risk * 100

        return {
            "recommendation": response.content,
            "formatted_response": formatted_response,
            "json_response": json_response,
            "confidence": final_confidence,
            "risk_score": final_risk,
            "status": "complete",
        }
    except Exception as e:
        logger.error(f"Moderator synthesis failed: {e}")
        return {
            "recommendation": f"Synthesis failed: {e}",
            "confidence": debate_confidence,
            "risk_score": risk_score,
            "status": "error",
        }
