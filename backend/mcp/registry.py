from typing import Callable, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict
    handler: Callable | None = None
    category: str = "general"
    cache_ttl: int = 3600
    allowed_agents: list[str] = []  # empty = all agents allowed

    class Config:
        arbitrary_types_allowed = True


_registry: dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    description: str,
    input_schema: dict,
    handler: Callable,
    category: str = "general",
    cache_ttl: int = 3600,
    allowed_agents: list[str] = None,
):
    # Auto-populate allowed_agents from mcp_servers if not specified
    if allowed_agents is None:
        try:
            from backend.mcp.mcp_servers import is_tool_allowed_for_agent, AGENT_SERVER_MAP
            allowed_agents = [a for a in AGENT_SERVER_MAP if is_tool_allowed_for_agent(name, a)]
        except Exception:
            allowed_agents = []

    _registry[name] = ToolDefinition(
        name=name,
        description=description,
        input_schema=input_schema,
        handler=handler,
        category=category,
        cache_ttl=cache_ttl,
        allowed_agents=allowed_agents,
    )
    logger.info(f"Registered MCP tool: {name} [{category}] (agents: {allowed_agents})")


def list_tools() -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "category": t.category,
            "allowed_agents": t.allowed_agents,
        }
        for t in _registry.values()
    ]


def get_tool(name: str) -> dict | None:
    t = _registry.get(name)
    if not t:
        return None
    return {
        "name": t.name,
        "description": t.description,
        "input_schema": t.input_schema,
        "category": t.category,
        "cache_ttl": t.cache_ttl,
        "allowed_agents": t.allowed_agents,
    }


async def invoke_tool(name: str, params: dict) -> Any:
    t = _registry.get(name)
    if not t:
        raise ValueError(f"Tool '{name}' not found")
    if not t.handler:
        raise ValueError(f"Tool '{name}' has no handler")

    from backend.mcp.sandbox import validate_inputs
    violations = validate_inputs(name, params)
    if violations:
        raise PermissionError(f"Sandbox violation: {', '.join(violations)}")

    return await t.handler(params)


def _register_all_tools():
    from backend.mcp.tools.news_tools import register as reg_news
    from backend.mcp.tools.supplier_tools import register as reg_supplier
    from backend.mcp.tools.shipping_tools import register as reg_shipping
    from backend.mcp.tools.commodity_tools import register as reg_commodity
    from backend.mcp.tools.finance_tools import register as reg_finance
    from backend.mcp.tools.social_tools import register as reg_social
    from backend.mcp.tools.firecrawl_tools import register as reg_firecrawl
    from backend.mcp.tools.gdelt_tools import TOOLS as gdelt_tools
    from backend.mcp.tools.yahoo_finance_tools import TOOLS as yahoo_finance_tools, register as reg_yahoo_finance
    from backend.mcp.tools.fred_tools import TOOLS as fred_tools
    from backend.mcp.tools.frankfurter_tools import TOOLS as frankfurter_tools
    from backend.mcp.tools.weather_tools import TOOLS as weather_tools
    from backend.mcp.tools.knowledge_tools import TOOLS as knowledge_tools
    from backend.mcp.tools.trade_tools import TOOLS as trade_tools
    from backend.mcp.tools.alpha_vantage_tools import TOOLS as alpha_vantage_tools
    from backend.mcp.tools.polygon_tools import TOOLS as polygon_tools
    from backend.mcp.tools.openweather_tools import TOOLS as openweather_tools
    from backend.mcp.tools.mediastack_tools import TOOLS as mediastack_tools
    from backend.mcp.tools.noaa_tools import TOOLS as noaa_tools
    from backend.mcp.tools.nvd_tools import TOOLS as nvd_tools
    from backend.mcp.tools.currents_tools import TOOLS as currents_tools
    from backend.mcp.tools.twelvedata_tools import TOOLS as twelvedata_tools
    from backend.mcp.tools.fmp_tools import TOOLS as fmp_tools
    from backend.mcp.tools.shodan_tools import TOOLS as shodan_tools
    from backend.mcp.tools.exchangerate_tools import TOOLS as exchangerate_tools
    from backend.mcp.tools.gnews_tools import TOOLS as gnews_tools
    from backend.mcp.tools.marketaux_tools import TOOLS as marketaux_tools
    from backend.mcp.tools.graphhopper_tools import TOOLS as graphhopper_tools

    for reg in [reg_news, reg_supplier, reg_shipping, reg_commodity, reg_finance, reg_social, reg_firecrawl, reg_yahoo_finance]:
        reg()

    # Register new real-data MCP tools
    for tool_list, category in [
        (gdelt_tools, "geopolitical"),
        (yahoo_finance_tools, "financial"),
        (fred_tools, "economic"),
        (frankfurter_tools, "forex"),
        (weather_tools, "disaster"),
        (knowledge_tools, "knowledge"),
        (trade_tools, "trade"),
        (alpha_vantage_tools, "commodity"),
        (polygon_tools, "financial"),
        (openweather_tools, "weather"),
        (mediastack_tools, "news"),
        (noaa_tools, "climate"),
        (nvd_tools, "cyber"),
        (currents_tools, "news"),
        (twelvedata_tools, "financial"),
        (fmp_tools, "financial"),
        (shodan_tools, "cyber"),
        (exchangerate_tools, "forex"),
        (gnews_tools, "news"),
        (marketaux_tools, "financial"),
        (graphhopper_tools, "logistics"),
    ]:
        for t in tool_list:
            register_tool(
                name=t["name"],
                description=t["description"],
                input_schema=t["input_schema"],
                handler=t["handler"],
                category=category,
                cache_ttl=t.get("cache_ttl", 3600),
            )

    register_tool(
        name="rag_query",
        description="Query the RAG pipeline for relevant document chunks",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        },
        handler=_rag_query_handler,
        category="rag",
        cache_ttl=300,
    )

    register_tool(
        name="agentic_rag_query",
        description="Run the full Agentic (Corrective) RAG pipeline: retrieve, critique, self-reflect, and optionally escalate to MCP. Returns context, sources, and confidence score.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "agent": {"type": "string", "description": "Agent domain (risk/supply/logistics/market/finance/brand)", "default": "risk"},
                "top_k": {"type": "integer", "description": "Number of results to retrieve", "default": 6},
            },
            "required": ["query"],
        },
        handler=_agentic_rag_handler,
        category="rag",
        cache_ttl=300,
    )

    register_tool(
        name="graph_rag_v2",
        description="Run HybridCypherRetriever for multi-tier supplier graph traversal (Tier-1/2/3) combined with vector search. Returns structured supplier data, component dependencies, and risk propagation paths.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for supplier graph"},
                "use_llm_extraction": {"type": "boolean", "description": "Use LLM for entity extraction", "default": True},
                "combine_with_vector": {"type": "boolean", "description": "Combine with vector search", "default": True},
                "top_k": {"type": "integer", "description": "Number of results", "default": 10},
            },
            "required": ["query"],
        },
        handler=_graph_rag_v2_handler,
        category="rag",
        cache_ttl=300,
    )


async def _rag_query_handler(params: dict):
    try:
        from backend.rag.retriever import hybrid_retrieve
        results = await hybrid_retrieve(params["query"], top_k=params.get("top_k", 5))
        return {"chunks": results}
    except Exception as e:
        return {"chunks": [], "error": str(e)}


async def _agentic_rag_handler(params: dict):
    try:
        from backend.rag.agent_rag_integration import get_agent_rag
        agent = params.get("agent", "risk")
        rag = get_agent_rag(agent)
        result = await rag.run(params["query"], top_k=params.get("top_k", 6))
        return result
    except Exception as e:
        return {"context": "", "sources": [], "confidence": 0.0, "error": str(e)}


async def _graph_rag_v2_handler(params: dict):
    try:
        from backend.rag.graph_rag import get_graph_retriever
        retriever = get_graph_retriever(
            use_llm=params.get("use_llm_extraction", True),
            combine_vector=params.get("combine_with_vector", True),
        )
        result = await retriever.retrieve(params["query"], top_k=params.get("top_k", 10))
        formatted = retriever.format_graph_context(result)
        return {
            "graph_results": result["graph_results"],
            "component_deps": result.get("component_deps", []),
            "risk_propagation": result.get("risk_propagation", []),
            "entities_found": result.get("entities_found", []),
            "formatted_context": formatted,
        }
    except Exception as e:
        return {"graph_results": {}, "entities_found": [], "error": str(e)}


register_all_tools = _register_all_tools
