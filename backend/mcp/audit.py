import uuid
import logging

logger = logging.getLogger(__name__)


async def audit_log(
    tool: str,
    agent: str,
    input_hash: str,
    latency_ms: int,
    was_cached: bool = False,
    sandbox_violations: list[str] | None = None,
):
    try:
        from backend.db.neon import execute_query
        await execute_query(
            """INSERT INTO mcp_audit_log (id, agent, tool, params, result_summary, latency_ms, was_cached, sandbox_violations)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            str(uuid.uuid4()),
            agent,
            tool,
            {"input_hash": input_hash},
            f"tool={tool} agent={agent} cached={was_cached}",
            latency_ms,
            was_cached,
            sandbox_violations or [],
        )
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")
