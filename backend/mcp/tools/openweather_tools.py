"""OpenWeatherMap MCP Tools — Weather alerts, forecasts, historical data for supply chain risk."""
import httpx
import os

OWM_BASE = "https://api.openweathermap.org"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.openweathermap_api_key or os.getenv("OPENWEATHERMAP_API_KEY", "")
    except Exception:
        return os.getenv("OPENWEATHERMAP_API_KEY", "")


def _mock_weather(location: str) -> dict:
    return {
        "location": location,
        "temp_c": 22.5,
        "feels_like_c": 21.0,
        "humidity": 65,
        "wind_speed_ms": 4.2,
        "weather": "Partly Cloudy",
        "mock": True,
    }


def _mock_forecast(location: str) -> dict:
    return {
        "location": location,
        "forecast": [
            {"date": "2025-01-16", "temp_max_c": 25, "temp_min_c": 18, "weather": "Clear", "precipitation_mm": 0},
            {"date": "2025-01-17", "temp_max_c": 23, "temp_min_c": 16, "weather": "Cloudy", "precipitation_mm": 2.5},
            {"date": "2025-01-18", "temp_max_c": 20, "temp_min_c": 14, "weather": "Rain", "precipitation_mm": 15.0},
        ],
        "mock": True,
    }


def _mock_alerts(location: str) -> dict:
    return {
        "location": location,
        "alerts": [
            {"event": "Severe Thunderstorm Warning", "severity": "moderate", "start": "2025-01-16T12:00:00Z", "end": "2025-01-16T18:00:00Z", "description": "Potential supply chain disruption due to severe weather"},
        ],
        "mock": True,
    }


async def current_weather(params: dict) -> dict:
    """Get current weather for a location from OpenWeatherMap.

    Args:
        location: City name or lat,lon (e.g., 'Shanghai' or '31.23,121.47')
        units: 'metric' (Celsius), 'imperial' (Fahrenheit), 'standard' (Kelvin)
    """
    location = params.get("location", "Shanghai")
    units = params.get("units", "metric")
    key = _get_key()

    if not key:
        return _mock_weather(location)

    try:
        # Check if location is lat,lon
        params_dict = {"appid": key, "units": units}
        if "," in location and len(location.split(",")) == 2:
            parts = location.split(",")
            params_dict["lat"] = parts[0].strip()
            params_dict["lon"] = parts[1].strip()
            url = f"{OWM_BASE}/data/2.5/weather"
        else:
            params_dict["q"] = location
            url = f"{OWM_BASE}/data/2.5/weather"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params_dict)
            data = resp.json()

        if data.get("cod") == 200:
            weather = data.get("weather", [{}])[0]
            main = data.get("main", {})
            wind = data.get("wind", {})
            return {
                "location": data.get("name", location),
                "country": data.get("sys", {}).get("country", ""),
                "temp_c": main.get("temp", 0),
                "feels_like_c": main.get("feels_like", 0),
                "temp_min_c": main.get("temp_min", 0),
                "temp_max_c": main.get("temp_max", 0),
                "humidity": main.get("humidity", 0),
                "pressure_hpa": main.get("pressure", 0),
                "wind_speed_ms": wind.get("speed", 0),
                "wind_deg": wind.get("deg", 0),
                "weather": weather.get("main", ""),
                "description": weather.get("description", ""),
                "visibility_m": data.get("visibility", 0),
                "clouds_pct": data.get("clouds", {}).get("all", 0),
                "mock": False,
            }

        return _mock_weather(location)
    except Exception:
        return _mock_weather(location)


async def weather_forecast(params: dict) -> dict:
    """Get 5-day weather forecast from OpenWeatherMap.

    Args:
        location: City name or lat,lon
        units: 'metric' or 'imperial'
    """
    location = params.get("location", "Shanghai")
    units = params.get("units", "metric")
    key = _get_key()

    if not key:
        return _mock_forecast(location)

    try:
        params_dict = {"appid": key, "units": units}
        if "," in location and len(location.split(",")) == 2:
            parts = location.split(",")
            params_dict["lat"] = parts[0].strip()
            params_dict["lon"] = parts[1].strip()
            url = f"{OWM_BASE}/data/2.5/forecast"
        else:
            params_dict["q"] = location
            url = f"{OWM_BASE}/data/2.5/forecast"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params_dict)
            data = resp.json()

        if data.get("cod") == "200":
            forecast = []
            for item in data.get("list", [])[:8]:  # Next 24h (3h intervals)
                weather = item.get("weather", [{}])[0]
                main = item.get("main", {})
                rain = item.get("rain", {})
                forecast.append({
                    "datetime": item.get("dt_txt", ""),
                    "temp_c": main.get("temp", 0),
                    "temp_min_c": main.get("temp_min", 0),
                    "temp_max_c": main.get("temp_max", 0),
                    "humidity": main.get("humidity", 0),
                    "weather": weather.get("main", ""),
                    "description": weather.get("description", ""),
                    "precipitation_mm": rain.get("3h", 0),
                    "wind_speed_ms": item.get("wind", {}).get("speed", 0),
                })
            return {
                "location": data.get("city", {}).get("name", location),
                "country": data.get("city", {}).get("country", ""),
                "forecast": forecast,
                "count": len(forecast),
                "mock": False,
            }

        return _mock_forecast(location)
    except Exception:
        return _mock_forecast(location)


async def weather_alerts(params: dict) -> dict:
    """Get weather alerts for a location from OpenWeatherMap One Call API.

    Args:
        lat: Latitude
        lon: Longitude
    """
    lat = params.get("lat", "31.23")
    lon = params.get("lon", "121.47")
    key = _get_key()

    if not key:
        return _mock_alerts(f"{lat},{lon}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OWM_BASE}/data/3.0/onecall", params={
                "lat": lat, "lon": lon, "appid": key, "units": "metric",
                "exclude": "minutely,hourly,daily",
            })
            data = resp.json()

        alerts = []
        for alert in data.get("alerts", []):
            alerts.append({
                "event": alert.get("event", ""),
                "severity": alert.get("tags", ["unknown"])[0] if alert.get("tags") else "unknown",
                "start": alert.get("start", ""),
                "end": alert.get("end", ""),
                "description": alert.get("description", "")[:500],
                "sender": alert.get("sender_name", ""),
            })

        current = data.get("current", {})
        return {
            "location": f"{lat},{lon}",
            "current_temp_c": current.get("temp", 0),
            "current_weather": current.get("weather", [{}])[0].get("main", "") if current.get("weather") else "",
            "alerts": alerts,
            "alert_count": len(alerts),
            "mock": False,
        }
    except Exception:
        return _mock_alerts(f"{lat},{lon}")


async def air_quality(params: dict) -> dict:
    """Get air quality index for a location from OpenWeatherMap.

    Args:
        lat: Latitude
        lon: Longitude
    """
    lat = params.get("lat", "31.23")
    lon = params.get("lon", "121.47")
    key = _get_key()

    if not key:
        return {"lat": lat, "lon": lon, "aqi": 2, "pm2_5": 12.5, "pm10": 25.0, "mock": True}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OWM_BASE}/data/2.5/air_pollution", params={
                "lat": lat, "lon": lon, "appid": key,
            })
            data = resp.json()

        if data.get("list"):
            item = data["list"][0]
            main = item.get("main", {})
            components = item.get("components", {})
            return {
                "lat": lat,
                "lon": lon,
                "aqi": main.get("aqi", 0),
                "co": components.get("co", 0),
                "no2": components.get("no2", 0),
                "o3": components.get("o3", 0),
                "pm2_5": components.get("pm2_5", 0),
                "pm10": components.get("pm10", 0),
                "so2": components.get("so2", 0),
                "nh3": components.get("nh3", 0),
                "mock": False,
            }

        return {"lat": lat, "lon": lon, "aqi": 2, "pm2_5": 12.5, "pm10": 25.0, "mock": True}
    except Exception:
        return {"lat": lat, "lon": lon, "aqi": 2, "pm2_5": 12.5, "pm10": 25.0, "mock": True}


TOOLS = [
    {
        "name": "owm_current_weather",
        "description": "Get current weather conditions for a location. Uses OpenWeatherMap API. Best for Risk and Logistics agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or 'lat,lon' (e.g., 'Shanghai', '31.23,121.47')"},
                "units": {"type": "string", "description": "'metric' (C) or 'imperial' (F)", "default": "metric"}
            },
            "required": ["location"]
        },
        "handler": current_weather,
        "cache_ttl": 600,
    },
    {
        "name": "owm_weather_forecast",
        "description": "Get 24-hour weather forecast (3h intervals). Uses OpenWeatherMap API. Best for Logistics planning.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or 'lat,lon'"},
                "units": {"type": "string", "description": "'metric' or 'imperial'", "default": "metric"}
            },
            "required": ["location"]
        },
        "handler": weather_forecast,
        "cache_ttl": 1800,
    },
    {
        "name": "owm_weather_alerts",
        "description": "Get severe weather alerts for a location. Uses OpenWeatherMap One Call API. Critical for Risk Sentinel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "string", "description": "Latitude", "default": "31.23"},
                "lon": {"type": "string", "description": "Longitude", "default": "121.47"}
            },
            "required": ["lat", "lon"]
        },
        "handler": weather_alerts,
        "cache_ttl": 300,
    },
    {
        "name": "owm_air_quality",
        "description": "Get air quality index (AQI, PM2.5, PM10). Uses OpenWeatherMap API. Useful for factory/port disruption risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "string", "description": "Latitude", "default": "31.23"},
                "lon": {"type": "string", "description": "Longitude", "default": "121.47"}
            },
            "required": ["lat", "lon"]
        },
        "handler": air_quality,
        "cache_ttl": 3600,
    },
]
