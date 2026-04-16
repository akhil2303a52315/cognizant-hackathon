"""Fallback Engine for SupplyChainGPT Council.

Tiered fallback system with cost/ROI analysis:
  - Tier 1: Immediate (near-shoring, emergency inventory, air freight)
  - Tier 2: Short-term (safety stock, dual-sourcing, route diversification)
  - Tier 3: Strategic (regional hubs, vertical integration, long-term contracts)

Each fallback has:
  - Cost estimate, risk reduction %, time to implement, ROI calculation
  - One-click execution via MCP ERP tool
  - Dynamic optimization based on debate output and predictions
"""

import logging
import time as _time
from typing import Optional
from datetime import datetime, timezone

from backend.state import CouncilState, FallbackOption, AgentOutput
from backend.observability.langsmith_config import CouncilTracer, record_mcp_call

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fallback templates — pre-defined strategies with parameterized costs
# ---------------------------------------------------------------------------
FALLBACK_TEMPLATES = {
    "tier1_nearshoring": FallbackOption(
        tier=1,
        name="Near-Shoring Emergency Activation",
        description="Activate pre-vetted near-shore backup suppliers within 500km radius. Emergency inventory release from regional warehouses.",
        cost_estimate_usd=150000,
        time_to_implement_days=3,
        risk_reduction_pct=25.0,
        roi_pct=180.0,
        confidence=0.85,
        mcp_tool="supplier_search",
        mcp_params={"product": "", "region": "nearshore"},
    ),
    "tier1_air_freight": FallbackOption(
        tier=1,
        name="Air Freight Emergency Logistics",
        description="Switch from sea/rail to air freight for critical components. 3-day delivery vs 21-day sea route.",
        cost_estimate_usd=380000,
        time_to_implement_days=1,
        risk_reduction_pct=35.0,
        roi_pct=120.0,
        confidence=0.90,
        mcp_tool="route_optimize",
        mcp_params={"origin": "", "destination": "", "constraints": {"mode": "air"}},
    ),
    "tier1_inventory_release": FallbackOption(
        tier=1,
        name="Strategic Inventory Release",
        description="Release safety stock from strategic reserves. 2-week buffer coverage for critical components.",
        cost_estimate_usd=50000,
        time_to_implement_days=1,
        risk_reduction_pct=15.0,
        roi_pct=250.0,
        confidence=0.95,
        mcp_tool="erp_query",
        mcp_params={"module": "inventory", "sql_query": "SELECT * FROM inventory WHERE category = 'strategic_reserve'"},
    ),
    "tier2_safety_stock": FallbackOption(
        tier=2,
        name="Safety Stock Buffer Expansion",
        description="Increase safety stock levels by 50% across top-10 critical components. 14-day implementation via ERP purchase orders.",
        cost_estimate_usd=500000,
        time_to_implement_days=14,
        risk_reduction_pct=30.0,
        roi_pct=160.0,
        confidence=0.80,
        mcp_tool="erp_query",
        mcp_params={"module": "procurement"},
    ),
    "tier2_dual_source": FallbackOption(
        tier=2,
        name="Dual-Sourcing Qualification",
        description="Qualify 2+ alternative suppliers per critical component. Reduce single-source dependency from 70% to 30%.",
        cost_estimate_usd=350000,
        time_to_implement_days=21,
        risk_reduction_pct=40.0,
        roi_pct=200.0,
        confidence=0.75,
        mcp_tool="supplier_search",
        mcp_params={"product": "", "region": ""},
    ),
    "tier2_route_diversification": FallbackOption(
        tier=2,
        name="Route Diversification",
        description="Establish 3+ alternative shipping routes per critical lane. Reduce port dependency and transit risk.",
        cost_estimate_usd=200000,
        time_to_implement_days=14,
        risk_reduction_pct=20.0,
        roi_pct=140.0,
        confidence=0.80,
        mcp_tool="route_optimize",
        mcp_params={"origin": "", "destination": ""},
    ),
    "tier3_regional_hubs": FallbackOption(
        tier=3,
        name="Regional Distribution Hub Network",
        description="Build 3 regional distribution hubs (APAC, EMEA, Americas) with 90-day inventory buffers. Eliminate single-point-of-failure.",
        cost_estimate_usd=5000000,
        time_to_implement_days=180,
        risk_reduction_pct=60.0,
        roi_pct=300.0,
        confidence=0.60,
        mcp_tool=None,
        mcp_params=None,
    ),
    "tier3_vertical_integration": FallbackOption(
        tier=3,
        name="Vertical Integration Investment",
        description="Acquire or partner with Tier-2/3 suppliers for critical components. Secure supply chain from raw material to finished product.",
        cost_estimate_usd=15000000,
        time_to_implement_days=365,
        risk_reduction_pct=70.0,
        roi_pct=250.0,
        confidence=0.45,
        mcp_tool=None,
        mcp_params=None,
    ),
    "tier3_longterm_contracts": FallbackOption(
        tier=3,
        name="Long-Term Supply Contracts",
        description="Negotiate 3-5 year fixed-price contracts with primary and backup suppliers. Lock in pricing and capacity guarantees.",
        cost_estimate_usd=2000000,
        time_to_implement_days=90,
        risk_reduction_pct=45.0,
        roi_pct=180.0,
        confidence=0.70,
        mcp_tool="contract_lookup",
        mcp_params={"supplier_id": ""},
    ),
}


class FallbackEngine:
    """Generates and optimizes tiered fallback options based on debate output.

    Selects relevant fallbacks from templates, adjusts costs based on
    predictions and debate confidence, and provides one-click execution
    via MCP tools.
    """

    def __init__(self):
        self.templates = FALLBACK_TEMPLATES

    async def generate_fallbacks(self, state: CouncilState) -> dict:
        """Generate tiered fallback options based on debate and prediction results.

        Returns state update with 'tiered_fallbacks' list.
        """
        agent_outputs = state.get("agent_outputs", [])
        predictions = state.get("predictions", [])
        risk_score = state.get("risk_score", 50)
        query = state.get("query", "")
        debate_rounds = state.get("debate_rounds", [])
        session_id = state.get("session_id", "unknown")

        tracer = CouncilTracer(session_id)
        t0 = _time.monotonic()

        # Determine which tiers are needed based on risk
        selected = []

        if risk_score >= 60:
            # High risk: all 3 tiers
            selected.extend(self._select_tier(1, query, agent_outputs, predictions))
            selected.extend(self._select_tier(2, query, agent_outputs, predictions))
            selected.extend(self._select_tier(3, query, agent_outputs, predictions))
        elif risk_score >= 30:
            # Medium risk: Tiers 1 + 2
            selected.extend(self._select_tier(1, query, agent_outputs, predictions))
            selected.extend(self._select_tier(2, query, agent_outputs, predictions))
        else:
            # Low risk: Tier 2 only (preventive)
            selected.extend(self._select_tier(2, query, agent_outputs, predictions))

        # Adjust costs and confidence based on predictions
        selected = self._adjust_with_predictions(selected, predictions)

        # Sort by tier, then by ROI descending
        selected.sort(key=lambda f: (f["tier"], -f["roi_pct"]))

        latency_ms = (_time.monotonic() - t0) * 1000
        with tracer.trace_debate_round(0, phase="fallback_generation", num_fallbacks=len(selected)):
            pass
        logger.info(f"Fallback generation: {len(selected)} options in {latency_ms:.0f}ms")

        return {"tiered_fallbacks": selected}

    def _select_tier(self, tier: int, query: str, agent_outputs: list, predictions: list) -> list[dict]:
        """Select fallback options for a specific tier."""
        results = []
        for key, template in self.templates.items():
            if template.tier != tier:
                continue

            # Customize template with query context
            customized = template.model_dump()
            customized["name"] = template.name

            # Adjust MCP params with query context
            if customized.get("mcp_params"):
                for param_key in customized["mcp_params"]:
                    if customized["mcp_params"][param_key] == "":
                        customized["mcp_params"][param_key] = query[:100]

            # Scale cost by number of affected components (from agent outputs)
            supply_agents = [o for o in agent_outputs if o.agent == "supply"]
            if supply_agents:
                # Higher supply agent confidence → lower cost (better alternatives available)
                conf_factor = 1.0 - (supply_agents[0].confidence / 100.0)
                customized["cost_estimate_usd"] = round(template.cost_estimate_usd * conf_factor)

            results.append(customized)

        return results

    def _adjust_with_predictions(self, fallbacks: list[dict], predictions: list[dict]) -> list[dict]:
        """Adjust fallback costs and confidence based on ensemble predictions."""
        if not predictions:
            return fallbacks

        # Find ensemble predictions
        ensemble_preds = [p for p in predictions if p.get("method") == "ensemble"]
        disruption_pred = None
        price_pred = None

        for p in ensemble_preds:
            if p.get("metric") == "disruption_probability":
                disruption_pred = p
            elif p.get("metric") == "price":
                price_pred = p

        for f in fallbacks:
            # If disruption probability is high, increase ROI (more value in mitigation)
            if disruption_pred and disruption_pred["point_estimate"] > 0.5:
                f["roi_pct"] = round(f["roi_pct"] * (1.0 + disruption_pred["point_estimate"]))

            # If price forecast is rising, increase cost estimates
            if price_pred and price_pred["point_estimate"] > price_pred.get("ci_lower", 0):
                cost_factor = 1.0 + (price_pred["point_estimate"] - price_pred.get("ci_lower", 0)) / max(abs(price_pred["point_estimate"]), 1) * 0.1
                f["cost_estimate_usd"] = round(f["cost_estimate_usd"] * cost_factor)

            # Reduce confidence for longer implementation times
            if f["time_to_implement_days"] > 90:
                f["confidence"] = round(f["confidence"] * 0.7, 2)

        return fallbacks

    async def execute_fallback(self, fallback: dict, agent_name: str = "supply") -> dict:
        """One-click execution of a fallback option via MCP ERP tool.

        Args:
            fallback: FallbackOption dict with mcp_tool and mcp_params
            agent_name: Agent executing the fallback

        Returns:
            Execution result from MCP tool
        """
        tool_name = fallback.get("mcp_tool")
        params = fallback.get("mcp_params", {})

        if not tool_name:
            return {
                "success": False,
                "error": "No MCP tool configured for this fallback (manual execution required)",
                "fallback": fallback["name"],
            }

        try:
            from backend.mcp.secure_mcp import secure_invoke
            t0 = _time.monotonic()
            with CouncilTracer(f"{agent_name}_fallback").trace_mcp_call(tool_name, agent=agent_name):
                result = await secure_invoke(agent_name, tool_name, params)
            latency_ms = (_time.monotonic() - t0) * 1000
            record_mcp_call(tool_name, agent_name, latency_ms, success=result.get("success", False))

            if result.get("success"):
                logger.info(f"Fallback '{fallback['name']}' executed via {tool_name}")
                return {
                    "success": True,
                    "fallback": fallback["name"],
                    "tier": fallback["tier"],
                    "tool": tool_name,
                    "result": result.get("result"),
                    "cost_usd": fallback["cost_estimate_usd"],
                }
            else:
                return {
                    "success": False,
                    "fallback": fallback["name"],
                    "error": result.get("warnings", ["Execution failed"]),
                }

        except Exception as e:
            logger.error(f"Fallback execution failed: {e}")
            return {
                "success": False,
                "fallback": fallback["name"],
                "error": str(e),
            }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
fallback_engine = FallbackEngine()
