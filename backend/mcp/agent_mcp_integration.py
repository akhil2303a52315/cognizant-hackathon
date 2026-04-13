"""Agent-MCP integration for SupplyChainGPT Council.

Automatically attaches relevant MCP tools to each agent and provides:
  - Auto-escalation from RAG to MCP when RAG confidence is low
  - ReAct-style tool calling within agent workflows
  - Per-agent tool manifests for LangChain ReAct integration
  - MCP tool result formatting for injection into agent messages

Usage in agents/risk_agent.py:
    from backend.mcp.agent_mcp_integration import get_agent_mcp_tools, auto_escalate_to_mcp
    tools = get_agent_mcp_tools("risk")
    mcp_data = await auto_escalate_to_mcp("risk", query, rag_confidence=0.45)
"""

import json
import logging
from typing import Optional

from backend.mcp.mcp_toolkit import get_mcp_client, MultiServerMCPClient
from backend.mcp.secure_mcp import secure_invoke, get_secure_executor
from backend.mcp.mcp_servers import get_agent_allowed_tools, get_agent_servers, AGENT_SERVER_MAP
from backend.rag.rag_config import AGENT_RAG_PROFILES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent MCP tool discovery
# ---------------------------------------------------------------------------
def get_agent_mcp_tools(agent_name: str) -> list:
    """Get LangChain Tool objects for an agent's allowed MCP tools.

    These tools can be passed to a ReAct agent's tool list.
    """
    client = get_mcp_client(agent_name)
    return client.get_langchain_tools()


def get_agent_tool_names(agent_name: str) -> list[str]:
    """Return the list of MCP tool names an agent can use."""
    return get_agent_allowed_tools(agent_name)


def get_agent_tool_descriptions(agent_name: str) -> str:
    """Return a formatted string describing all tools available to an agent.

    Used to inject into the agent's system prompt so it knows what
    MCP tools it can call.
    """
    client = get_mcp_client(agent_name)
    categories = client.get_tool_categories()

    parts = []
    for server_name, tools in categories.items():
        parts.append(f"  {server_name}: {', '.join(tools)}")

    if not parts:
        return "No MCP tools available."

    return "Available MCP tools:\n" + "\n".join(parts)


# ---------------------------------------------------------------------------
# Auto-escalation: RAG → MCP when confidence is low
# ---------------------------------------------------------------------------
async def auto_escalate_to_mcp(agent_name: str, query: str, rag_confidence: float = 0.0) -> Optional[str]:
    """If RAG confidence is below threshold, auto-call relevant MCP tools.

    This bridges the Day 3 Agentic RAG self-reflection with Day 4 MCP tools.
    When the AgenticRAG pipeline's self-reflection decides to escalate,
    this function executes the MCP calls and formats the results.

    Args:
        agent_name: The agent requesting escalation
        query: The original query
        rag_confidence: RAG confidence score (0-1)

    Returns:
        Formatted string with MCP tool results, or None if no escalation needed
    """
    profile = AGENT_RAG_PROFILES.get(agent_name, AGENT_RAG_PROFILES["risk"])
    threshold = profile.get("confidence_threshold", 0.70)

    if rag_confidence >= threshold:
        return None

    # Get the MCP escalation tools from the agent's RAG profile
    escalation_tools = profile.get("mcp_escalation_tools", [])
    if not escalation_tools:
        logger.info(f"[{agent_name}] No MCP escalation tools configured")
        return None

    logger.info(f"[{agent_name}] Auto-escalating to MCP (RAG confidence={rag_confidence:.2f} < {threshold})")

    results = []
    for tool_name in escalation_tools[:2]:  # limit to 2 tools to avoid over-calling
        try:
            result = await secure_invoke(agent_name, tool_name, {"query": query})
            if result.get("success"):
                tool_output = result["result"]
                # Format the result
                if isinstance(tool_output, dict):
                    # Check if it's mock data
                    is_mock = tool_output.get("mock", False)
                    source_tag = " (mock)" if is_mock else " (live)"
                    results.append(f"--- MCP: {tool_name}{source_tag} ---\n{json.dumps(tool_output, default=str, indent=2)[:2000]}")
                elif isinstance(tool_output, str):
                    results.append(f"--- MCP: {tool_name} ---\n{tool_output[:2000]}")
                else:
                    results.append(f"--- MCP: {tool_name} ---\n{json.dumps(tool_output, default=str)[:2000]}")
            elif result.get("rate_limited"):
                results.append(f"--- MCP: {tool_name} --- (rate limited, skipped)")
            elif result.get("scope_valid") is False:
                results.append(f"--- MCP: {tool_name} --- (scope violation)")
        except Exception as e:
            logger.warning(f"[{agent_name}] MCP escalation to {tool_name} failed: {e}")
            results.append(f"--- MCP: {tool_name} --- (error: {e})")

    if not results:
        return None

    return "\n\n".join(results)


# ---------------------------------------------------------------------------
# MCP tool result injection into agent messages
# ---------------------------------------------------------------------------
MCP_SYSTEM_PROMPT_SUFFIX = """

You have access to MCP (Model Context Protocol) tools that provide real-time data.
When your retrieved context is insufficient, you can reference MCP tool results
provided below. Always cite the tool name and whether data is live or mock.

{tool_descriptions}
"""


def inject_mcp_system_prompt(messages: list[dict], agent_name: str) -> list[dict]:
    """Inject MCP tool availability info into the agent's system prompt.

    Appends tool descriptions to the first system message.
    """
    tool_desc = get_agent_tool_descriptions(agent_name)
    if tool_desc == "No MCP tools available.":
        return messages

    suffix = MCP_SYSTEM_PROMPT_SUFFIX.format(tool_descriptions=tool_desc)

    # Append to the first system message
    for i, msg in enumerate(messages):
        if msg.get("role") == "system":
            messages[i] = {
                "role": "system",
                "content": msg["content"] + suffix,
            }
            return messages

    # No system message found — insert one
    messages.insert(0, {
        "role": "system",
        "content": f"You are a supply chain analysis agent.{suffix}",
    })
    return messages


def inject_mcp_results(messages: list[dict], mcp_context: str) -> list[dict]:
    """Inject MCP tool results into the agent's message list.

    Similar to RAG context injection — adds a system message with
    MCP results before the user message.
    """
    if not mcp_context:
        return messages

    mcp_message = {
        "role": "system",
        "content": f"MCP Tool Results (real-time data):\n\n{mcp_context}",
    }

    # Insert before the last user message
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            messages.insert(i, mcp_message)
            return messages

    messages.append(mcp_message)
    return messages


# ---------------------------------------------------------------------------
# Batch MCP pre-fetch for all agents (used by graph.py MCP node)
# ---------------------------------------------------------------------------
async def prefetch_mcp_for_all_agents(query: str, rag_confidences: dict[str, float] = None) -> dict[str, str]:
    """Pre-fetch MCP data for all agents that need escalation.

    Called by the MCP node in graph.py after RAG pre-fetch.
    Only calls MCP tools for agents whose RAG confidence is below threshold.

    Args:
        query: The user's query
        rag_confidences: Dict mapping agent_name → RAG confidence (0-1)

    Returns:
        Dict mapping agent_name → MCP context string
    """
    import asyncio

    rag_confidences = rag_confidences or {}
    tasks = []
    agent_names = list(AGENT_SERVER_MAP.keys())

    for name in agent_names:
        confidence = rag_confidences.get(name, 0.0)
        tasks.append(auto_escalate_to_mcp(name, query, rag_confidence=confidence))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    context_map = {}
    for name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            logger.error(f"MCP prefetch failed for {name}: {result}")
            context_map[name] = ""
        else:
            context_map[name] = result or ""

    escalated = [n for n, c in context_map.items() if c]
    if escalated:
        logger.info(f"MCP prefetch: escalated for agents {escalated}")
    return context_map


# ---------------------------------------------------------------------------
# Convenience: full agent MCP setup
# ---------------------------------------------------------------------------
def setup_agent_mcp(agent_name: str) -> dict:
    """Complete MCP setup for an agent. Returns a config dict.

    Call this during agent initialization or graph setup.
    """
    client = get_mcp_client(agent_name)
    executor = get_secure_executor(agent_name)
    tools = get_agent_mcp_tools(agent_name)
    tool_names = get_agent_tool_names(agent_name)
    tool_desc = get_agent_tool_descriptions(agent_name)
    servers = get_agent_servers(agent_name)

    return {
        "agent": agent_name,
        "client": client,
        "executor": executor,
        "langchain_tools": tools,
        "tool_names": tool_names,
        "tool_descriptions": tool_desc,
        "servers": [s.name for s in servers],
        "total_tools": len(tool_names),
    }
