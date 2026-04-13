# MCP package

from backend.mcp.mcp_servers import (
    MCPServerDef,
    MCP_SERVERS,
    AGENT_SERVER_MAP,
    get_agent_allowed_tools,
    get_agent_servers,
    get_server_for_tool,
    is_tool_allowed_for_agent,
    get_all_server_definitions,
    get_tool_manifest,
)
from backend.mcp.mcp_toolkit import (
    MultiServerMCPClient,
    get_mcp_client,
    get_all_mcp_clients,
    init_all_mcp_clients,
    get_tool_health,
    get_tool_schema_with_fallback,
)
from backend.mcp.secure_mcp import (
    SecureMCPExecutor,
    get_secure_executor,
    secure_invoke,
    get_rate_limit_status,
    sanitize_input,
    sanitize_output,
)
from backend.mcp.agent_mcp_integration import (
    get_agent_mcp_tools,
    get_agent_tool_names,
    get_agent_tool_descriptions,
    auto_escalate_to_mcp,
    inject_mcp_system_prompt,
    inject_mcp_results,
    prefetch_mcp_for_all_agents,
    setup_agent_mcp,
)
