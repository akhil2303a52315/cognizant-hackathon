from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/suppliers")
async def get_suppliers_with_risk():
    try:
        from backend.db.neo4j_client import run_cypher
        result = await run_cypher(
            "MATCH (s:Supplier) RETURN s.id, s.name, s.capability_match, s.lead_time_days, s.location, s.tier"
        )
        suppliers = []
        for r in result:
            risk_score = 100 - (r.get("s.capability_match", 50))
            suppliers.append({
                "id": r.get("s.id"),
                "name": r.get("s.name"),
                "capability_match": r.get("s.capability_match"),
                "lead_time_days": r.get("s.lead_time_days"),
                "location": r.get("s.location"),
                "tier": r.get("s.tier"),
                "risk_score": risk_score,
            })
        return {"suppliers": suppliers}
    except Exception as e:
        return {"suppliers": _mock_suppliers()}


def _mock_suppliers():
    return [
        {"id": "S1", "name": "Taiwan Semi Corp", "capability_match": 95, "lead_time_days": 14, "location": "Taiwan", "tier": 1, "risk_score": 5},
        {"id": "S2", "name": "India Electronics Ltd", "capability_match": 82, "lead_time_days": 12, "location": "India", "tier": 1, "risk_score": 18},
        {"id": "S3", "name": "Vietnam Components", "capability_match": 75, "lead_time_days": 18, "location": "Vietnam", "tier": 2, "risk_score": 25},
    ]


@router.get("/score/{supplier_id}")
async def get_supplier_risk_score(supplier_id: str):
    try:
        from backend.db.neo4j_client import run_cypher
        result = await run_cypher(
            "MATCH (s:Supplier {id: $sid}) RETURN s", {"sid": supplier_id}
        )
        if result:
            s = result[0].get("s", result[0])
            risk = 100 - s.get("capability_match", 50)
            return {
                "supplier_id": supplier_id,
                "name": s.get("name"),
                "risk_score": risk,
                "factors": {
                    "capability_gap": 100 - s.get("capability_match", 50),
                    "lead_time_risk": s.get("lead_time_days", 14) * 2,
                    "tier_risk": (s.get("tier", 1) - 1) * 15,
                    "location_risk": 10,
                },
                "recommendation": "Monitor" if risk < 30 else "Find alternative" if risk < 60 else "Critical - immediate action",
            }
    except Exception:
        pass
    return {
        "supplier_id": supplier_id,
        "risk_score": 25,
        "factors": {"capability_gap": 25, "lead_time_risk": 36, "tier_risk": 0, "location_risk": 10},
        "recommendation": "Monitor",
        "mock": True,
    }


@router.get("/heatmap")
async def get_risk_heatmap():
    try:
        from backend.db.neo4j_client import run_cypher
        result = await run_cypher("MATCH (s:Supplier) RETURN s.location as location, avg(100 - s.capability_match) as avg_risk")
        regions = {r["location"]: r["avg_risk"] for r in result}
    except Exception:
        regions = {"Taiwan": 5, "India": 18, "Vietnam": 25}

    return {
        "regions": regions,
        "global_avg": sum(regions.values()) / max(len(regions), 1),
        "high_risk_threshold": 40,
    }
