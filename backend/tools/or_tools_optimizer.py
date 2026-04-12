import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def optimize_routes(
    locations: list[dict],
    constraints: dict = None,
) -> dict:
    constraints = constraints or {}
    num_vehicles = constraints.get("num_vehicles", 3)
    max_capacity = constraints.get("max_capacity", 100)
    max_time_minutes = constraints.get("max_time_minutes", 480)

    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp

        locations_coords = [(l.get("lat", 0), l.get("lng", 0)) for l in locations]
        distance_matrix = _compute_distance_matrix(locations_coords)

        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix), num_vehicles, 0
        )
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        dimension_name = "Time"
        routing.AddDimension(
            transit_callback_index,
            30,
            max_time_minutes,
            False,
            dimension_name,
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 10

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            routes = []
            for vehicle_id in range(num_vehicles):
                route = []
                index = routing.Start(vehicle_id)
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    route.append(locations[node] if node < len(locations) else {"stop": node})
                    index = solution.Value(routing.NextVar(index))
                routes.append({"vehicle": vehicle_id, "stops": route, "cost": solution.ObjectiveValue()})
            return {"routes": routes, "total_cost": solution.ObjectiveValue(), "solver": "or-tools"}
    except ImportError:
        logger.info("OR-Tools not available, using heuristic optimizer")
    except Exception as e:
        logger.warning(f"OR-Tools optimization failed: {e}")

    return _heuristic_route(locations, num_vehicles)


def _compute_distance_matrix(locations):
    import math
    n = len(locations)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            lat1, lng1 = locations[i]
            lat2, lng2 = locations[j]
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            matrix[i][j] = int(R * c * 1000)
    return matrix


def _heuristic_route(locations: list[dict], num_vehicles: int) -> dict:
    chunk_size = max(len(locations) // num_vehicles, 1)
    routes = []
    for i in range(num_vehicles):
        start = i * chunk_size
        end = min(start + chunk_size, len(locations))
        stops = locations[start:end]
        routes.append({"vehicle": i, "stops": stops, "cost": len(stops) * 100})
    return {"routes": routes, "total_cost": sum(r["cost"] for r in routes), "solver": "heuristic"}


async def optimize_allocation(
    inventory: list[dict],
    demand: list[dict],
    constraints: dict = None,
) -> dict:
    allocations = []
    for d in demand:
        best = None
        for inv in inventory:
            if inv.get("product") == d.get("product") and inv.get("quantity", 0) >= d.get("quantity", 0):
                if best is None or inv.get("cost", 0) < best.get("cost", 0):
                    best = inv
        if best:
            allocations.append({
                "product": d.get("product"),
                "source": best.get("warehouse", "unknown"),
                "destination": d.get("destination", "unknown"),
                "quantity": d.get("quantity"),
                "cost": best.get("cost", 0) * d.get("quantity", 1),
            })
    return {"allocations": allocations, "total_cost": sum(a.get("cost", 0) for a in allocations)}


async def find_expedited_options(
    origin: str,
    destination: str,
    urgency: str = "high",
) -> dict:
    options = [
        {"mode": "air_freight", "transit_days": 2, "cost_multiplier": 4.5, "availability": "immediate"},
        {"mode": "express_sea", "transit_days": 10, "cost_multiplier": 1.8, "availability": "immediate"},
        {"mode": "charter_flight", "transit_days": 1, "cost_multiplier": 8.0, "availability": "limited"},
    ]
    if urgency == "critical":
        options = [o for o in options if o["transit_days"] <= 2]
    return {"origin": origin, "destination": destination, "options": options}
