"""Weather & Natural Disaster MCP Tools — Open-Meteo + USGS Earthquake. No API keys needed."""
import httpx
from datetime import datetime, timedelta

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
USGS_BASE = "https://earthquake.usgs.gov/fdsnws/event/1"
GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"


def _mock_weather(lat: float, lon: float) -> dict:
    return {
        "latitude": lat, "longitude": lon,
        "temperature_c": 25.0,
        "windspeed_kmh": 15.0,
        "precipitation_mm": 2.0,
        "weather_code": 3,
        "forecast_days": [],
        "mock": True
    }


def _mock_earthquake(lat: float, lon: float) -> dict:
    return {
        "latitude": lat, "longitude": lon,
        "earthquakes": [
            {"magnitude": 5.2, "place": "Near Taiwan", "time": "2024-01-15T08:30:00", "tsunami": False}
        ],
        "total": 1,
        "mock": True
    }


async def weather_forecast(params: dict) -> dict:
    """Get weather forecast for a location from Open-Meteo. No API key needed.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        days: Number of forecast days (default: 7)
    """
    lat = params.get("latitude", 25.0)
    lon = params.get("longitude", 121.5)
    days = params.get("days", 7)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OPEN_METEO_BASE}/forecast", params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
                "timezone": "auto",
                "forecast_days": days
            })
            data = resp.json()

        daily = data.get("daily", {})
        forecast = []
        dates = daily.get("time", [])
        for i, d in enumerate(dates):
            forecast.append({
                "date": d,
                "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                "windspeed_max": daily.get("windspeed_10m_max", [])[i] if i < len(daily.get("windspeed_10m_max", [])) else None,
                "weather_code": daily.get("weathercode", [])[i] if i < len(daily.get("weathercode", [])) else None,
            })

        return {
            "latitude": lat, "longitude": lon,
            "forecast": forecast,
            "mock": False
        }
    except Exception:
        return _mock_weather(lat, lon)


async def earthquake_check(params: dict) -> dict:
    """Check for recent earthquakes near a location from USGS. No API key needed.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in km (default: 500)
        min_magnitude: Minimum magnitude (default: 4.0)
        days: Look back days (default: 30)
    """
    lat = params.get("latitude", 25.0)
    lon = params.get("longitude", 121.5)
    radius_km = params.get("radius_km", 500)
    min_mag = params.get("min_magnitude", 4.0)
    days = params.get("days", 30)

    try:
        start_time = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{USGS_BASE}/query", params={
                "format": "geojson",
                "latitude": lat,
                "longitude": lon,
                "maxradiuskm": radius_km,
                "minmagnitude": min_mag,
                "starttime": start_time,
                "orderby": "magnitude"
            })
            data = resp.json()

        features = data.get("features", [])
        earthquakes = []
        for f in features[:10]:
            props = f.get("properties", {})
            earthquakes.append({
                "magnitude": props.get("mag", 0),
                "place": props.get("place", ""),
                "time": datetime.fromtimestamp(props.get("time", 0) / 1000).isoformat() if props.get("time") else "",
                "tsunami": props.get("tsunami", 0) > 0,
                "sig": props.get("sig", 0),
            })

        return {
            "latitude": lat, "longitude": lon,
            "earthquakes": earthquakes,
            "total": len(earthquakes),
            "mock": False
        }
    except Exception:
        return _mock_earthquake(lat, lon)


async def disaster_alerts(params: dict) -> dict:
    """Get recent disaster alerts from GDACS RSS feed. No API key needed.
    
    Args:
        limit: Max alerts to return (default: 10)
    """
    limit = params.get("limit", 10)

    try:
        import xml.etree.ElementTree as ET

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GDACS_RSS)
            root = ET.fromstring(resp.text)

        alerts = []
        for item in root.findall(".//item")[:limit]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            alerts.append({
                "title": title,
                "link": link,
                "description": description[:200],
                "date": pub_date,
            })

        return {"alerts": alerts, "total": len(alerts), "mock": False}
    except Exception:
        return {"alerts": [{"title": "No disaster alerts currently", "mock": True}], "total": 0, "mock": True}


TOOLS = [
    {
        "name": "weather_forecast",
        "description": "Get weather forecast for any location. No API key needed. Useful for supply chain weather disruption analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Location latitude (e.g., 25.0 for Taiwan)", "default": 25.0},
                "longitude": {"type": "number", "description": "Location longitude (e.g., 121.5 for Taiwan)", "default": 121.5},
                "days": {"type": "integer", "description": "Forecast days (default: 7)", "default": 7}
            },
            "required": ["latitude", "longitude"]
        },
        "handler": weather_forecast,
        "cache_ttl": 1800,
    },
    {
        "name": "earthquake_check",
        "description": "Check recent earthquakes near a location from USGS. No API key needed. Critical for Taiwan/Japan semiconductor supply risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Center latitude", "default": 25.0},
                "longitude": {"type": "number", "description": "Center longitude", "default": 121.5},
                "radius_km": {"type": "integer", "description": "Search radius in km (default: 500)", "default": 500},
                "min_magnitude": {"type": "number", "description": "Min magnitude (default: 4.0)", "default": 4.0},
                "days": {"type": "integer", "description": "Look back days (default: 30)", "default": 30}
            },
            "required": ["latitude", "longitude"]
        },
        "handler": earthquake_check,
        "cache_ttl": 1800,
    },
    {
        "name": "disaster_alerts",
        "description": "Get global disaster alerts from GDACS. No API key needed. Covers earthquakes, floods, storms, tsunamis, volcanoes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max alerts (default: 10)", "default": 10}
            }
        },
        "handler": disaster_alerts,
        "cache_ttl": 1800,
    },
]
