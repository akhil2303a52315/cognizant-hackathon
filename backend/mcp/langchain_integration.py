from langchain_core.tools import Tool
from backend.mcp.registry import list_tools, invoke_tool
import json
import logging

logger = logging.getLogger(__name__)


def get_langchain_tools() -> list[Tool]:
    tools = []
    for t in list_tools():
        tool = Tool(
            name=t["name"],
            description=t["description"],
            func=_sync_wrapper(t["name"]),
            coroutine=_async_wrapper(t["name"]),
        )
        tools.append(tool)
    return tools


def _sync_wrapper(tool_name: str):
    def run(query: str) -> str:
        import asyncio
        try:
            params = json.loads(query) if query.startswith("{") else {"query": query}
        except json.JSONDecodeError:
            params = {"query": query}
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(invoke_tool(tool_name, params))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(invoke_tool(tool_name, params))
        return json.dumps(result, default=str)
    return run


def _async_wrapper(tool_name: str):
    async def arun(query: str) -> str:
        try:
            params = json.loads(query) if query.startswith("{") else {"query": query}
        except json.JSONDecodeError:
            params = {"query": query}
        result = await invoke_tool(tool_name, params)
        return json.dumps(result, default=str)
    return arun
