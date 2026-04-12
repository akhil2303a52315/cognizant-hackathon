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
):
    _registry[name] = ToolDefinition(
        name=name,
        description=description,
        input_schema=input_schema,
        handler=handler,
        category=category,
        cache_ttl=cache_ttl,
    )
    logger.info(f"Registered MCP tool: {name} [{category}]")


def list_tools() -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "category": t.category,
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

    for reg in [reg_news, reg_supplier, reg_shipping, reg_commodity, reg_finance, reg_social, reg_firecrawl]:
        reg()

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


async def _rag_query_handler(params: dict):
    try:
        from backend.rag.retriever import hybrid_retrieve
        results = await hybrid_retrieve(params["query"], top_k=params.get("top_k", 5))
        return {"chunks": results}
    except Exception as e:
        return {"chunks": [], "error": str(e)}


register_all_tools = _register_all_tools
