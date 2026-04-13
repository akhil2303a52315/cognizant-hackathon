"""GraphHopper MCP Tools — Route optimization, distance, ETA for logistics."""
import httpx
import os

GH_BASE = "https://graphhopper.com/api/1"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.graphhopper_api_key or os.getenv("GRAPHHOPPER_API_KEY", "")
    except Exception:
        return os.getenv("GRAPHHOPPER_API_KEY", "")


def _mock_route(origin: str, dest: str) -> dict:
    return {"origin": origin, "destination": dest, "distance_km": 0, "mock": True}


async def route_optimize(params: dict) -> dict:
    """Get optimized route between two points from GraphHopper.

    Args:
        origin: Start point (lat,lng or address)
        destination: End point (lat,lng or address)
        vehicle: Vehicle type (car, truck, bike, foot)
    """
    origin = params.get("origin", "40.7128,-74.0060")  # NYC
    destination = params.get("destination", "34.0522,-118.2437")  # LA
    vehicle = params.get("vehicle", "car")
    key = _get_key()

    if not key:
        return _mock_route(origin, destination)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GH_BASE}/route", params={
                "point": [origin, destination],
                "vehicle": vehicle,
                "key": key,
                "calc_points": "false",
                "instructions": "false",
            })
            data = resp.json()

        if "paths" in data and data["paths"]:
            path = data["paths"][0]
            return {
                "origin": origin,
                "destination": destination,
                "vehicle": vehicle,
                "distance_km": round(path.get("distance", 0) / 1000, 1),
                "duration_hours": round(path.get("time", 0) / 3600000, 1),
                "mock": False,
            }

        if data.get("message"):
            return {**_mock_route(origin, destination), "error": data["message"]}

        return _mock_route(origin, destination)
    except Exception:
        return _mock_route(origin, destination)


async def distance_matrix(params: dict) -> dict:
    """Get distance/duration matrix between multiple points from GraphHopper.

    Args:
        points: List of 'lat,lng' strings (e.g., ['40.7128,-74.0060', '34.0522,-118.2437'])
        vehicle: Vehicle type (car, truck, bike, foot)
    """
    points = params.get("points", ["40.7128,-74.0060", "34.0522,-118.2437"])
    vehicle = params.get("vehicle", "car")
    key = _get_key()

    if not key:
        return {"points": points, "distances": [], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GH_BASE}/matrix", params={
                "point": points,
                "vehicle": vehicle,
                "key": key,
                "out_array": ["distances", "times"],
            })
            data = resp.json()

        if "distances" in data:
            return {
                "points": points,
                "distances_km": [[round(d / 1000, 1) if d >= 0 else -1 for d in row] for row in data["distances"]],
                "durations_hours": [[round(t / 3600000, 2) if t >= 0 else -1 for t in row] for row in data["times"]],
                "mock": False,
            }

        return {"points": points, "distances": [], "mock": True}
    except Exception:
        return {"points": points, "distances": [], "mock": True}


async def geocode(params: dict) -> dict:
    """Geocode an address to coordinates using GraphHopper.

    Args:
        address: Address to geocode (e.g., 'Shanghai Port, China')
    """
    address = params.get("address", "Shanghai Port, China")
    key = _get_key()

    if not key:
        return {"address": address, "lat": 0, "lng": 0, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{GH_BASE}/geocode", params={
                "q": address, "key": key, "limit": 1,
            })
            data = resp.json()

        if "hits" in data and data["hits"]:
            hit = data["hits"][0]
            point = hit.get("point", {})
            return {
                "address": address,
                "name": hit.get("name", ""),
                "lat": point.get("lat", 0),
                "lng": point.get("lng", 0),
                "country": hit.get("country", ""),
                "mock": False,
            }

        return {"address": address, "lat": 0, "lng": 0, "mock": True}
    except Exception:
        return {"address": address, "lat": 0, "lng": 0, "mock": True}


TOOLS = [
    {
        "name": "gh_route_optimize",
        "description": "Get optimized route (distance, ETA). Uses GraphHopper API. Critical for logistics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Start point (lat,lng)"},
                "destination": {"type": "string", "description": "End point (lat,lng)"},
                "vehicle": {"type": "string", "description": "Vehicle: car,truck,bike,foot", "default": "car"}
            },
            "required": ["origin", "destination"]
        },
        "handler": route_optimize,
        "cache_ttl": 3600,
    },
    {
        "name": "gh_distance_matrix",
        "description": "Get distance/duration matrix between multiple points. Uses GraphHopper API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "points": {"type": "array", "items": {"type": "string"}, "description": "List of lat,lng points"},
                "vehicle": {"type": "string", "description": "Vehicle type", "default": "car"}
            },
            "required": ["points"]
        },
        "handler": distance_matrix,
        "cache_ttl": 3600,
    },
    {
        "name": "gh_geocode",
        "description": "Geocode address to coordinates. Uses GraphHopper API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Address to geocode"}
            },
            "required": ["address"]
        },
        "handler": geocode,
        "cache_ttl": 86400,
    },
]
