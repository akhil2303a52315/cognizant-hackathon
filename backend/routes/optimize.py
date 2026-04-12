from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from backend.tools.or_tools_optimizer import optimize_routes, optimize_allocation, find_expedited_options
from backend.tools.monte_carlo import run_simulation

logger = logging.getLogger(__name__)

router = APIRouter()


class RouteOptimizeRequest(BaseModel):
    locations: list[dict]
    constraints: Optional[dict] = None


class AllocationRequest(BaseModel):
    inventory: list[dict]
    demand: list[dict]
    constraints: Optional[dict] = None


class ExpediteRequest(BaseModel):
    origin: str
    destination: str
    urgency: Optional[str] = "high"


class MonteCarloRequest(BaseModel):
    variables: list[dict]
    num_simulations: Optional[int] = 1000
    target_metric: Optional[str] = "total_cost"


@router.post("/routes")
async def optimize_routes_endpoint(request: RouteOptimizeRequest):
    result = await optimize_routes(request.locations, request.constraints)
    return result


@router.post("/allocation")
async def optimize_allocation_endpoint(request: AllocationRequest):
    result = await optimize_allocation(request.inventory, request.demand, request.constraints)
    return result


@router.post("/expedite")
async def expedite_endpoint(request: ExpediteRequest):
    result = await find_expedited_options(request.origin, request.destination, request.urgency)
    return result


@router.post("/monte-carlo")
async def monte_carlo_endpoint(request: MonteCarloRequest):
    result = await run_simulation(request.variables, request.num_simulations, request.target_metric)
    return result
