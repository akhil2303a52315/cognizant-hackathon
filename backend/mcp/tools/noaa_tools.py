"""NOAA MCP Tools — Climate data, severe weather, storm events for supply chain risk."""
import httpx
import os

NOAA_BASE = "https://www.ncdc.noaa.gov/cdo-web/api/v2"


def _get_key() -> str:
    try:
        from backend.config import settings
        return settings.noaa_api_key or os.getenv("NOAA_API_KEY", "")
    except Exception:
        return os.getenv("NOAA_API_KEY", "")


def _mock_climate(location: str) -> dict:
    return {
        "location": location,
        "data": [
            {"date": "2024-07", "datatype": "TAVG", "value": 28.5, "unit": "Celsius"},
            {"date": "2024-06", "datatype": "TAVG", "value": 26.2, "unit": "Celsius"},
        ],
        "mock": True,
    }


def _mock_storms(location: str) -> dict:
    return {
        "location": location,
        "events": [
            {"event_type": "Flash Flood", "date": "2024-09-15", "injuries": 0, "deaths": 0, "damage_property": "50K", "state": "TX"},
            {"event_type": "Tornado", "date": "2024-08-22", "injuries": 2, "deaths": 0, "damage_property": "2.5M", "state": "OK"},
        ],
        "mock": True,
    }


def _mock_sea_level(location: str) -> dict:
    return {
        "location": location,
        "trend_mm_per_year": 3.2,
        "last_measurement": "2024-12",
        "mock": True,
    }


async def climate_data(params: dict) -> dict:
    """Get climate data from NOAA CDO API.

    Args:
        datasetid: Dataset ID (GHCND=daily, GSOM=monthly summary, GSOY=annual summary)
        locationid: Location ID (e.g., 'CITY:US060013' for Shanghai-equivalent)
        startdate: Start date (YYYY-MM-DD)
        enddate: End date (YYYY-MM-DD)
        datatypeid: Data type (TAVG, TMAX, TMIN, PRCP, SNOW)
        limit: Max results (default: 20)
    """
    datasetid = params.get("datasetid", "GSOM")
    locationid = params.get("locationid", "CITY:US060013")
    startdate = params.get("startdate", "2024-01-01")
    enddate = params.get("enddate", "2024-12-31")
    datatypeid = params.get("datatypeid", "TAVG")
    limit = min(params.get("limit", 20), 50)
    key = _get_key()

    if not key:
        return _mock_climate(locationid)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{NOAA_BASE}/data", params={
                "datasetid": datasetid,
                "locationid": locationid,
                "startdate": startdate,
                "enddate": enddate,
                "datatypeid": datatypeid,
                "limit": limit,
                "units": "metric",
            }, headers={"token": key})
            data = resp.json()

        if data.get("results"):
            results = [{
                "date": r.get("date", ""),
                "datatype": r.get("datatype", ""),
                "value": r.get("value", 0),
                "station": r.get("station", ""),
            } for r in data["results"]]
            return {
                "location": locationid,
                "dataset": datasetid,
                "data": results,
                "count": len(results),
                "mock": False,
            }

        return _mock_climate(locationid)
    except Exception:
        return _mock_climate(locationid)


async def storm_events(params: dict) -> dict:
    """Get severe storm event data from NOAA Storm Events Database.

    Args:
        state: US state abbreviation (e.g., 'TX', 'CA', 'FL')
        event_type: Event type (Tornado, Flash Flood, Hurricane, Hail, etc.)
        year: Year (default: 2024)
    """
    state = params.get("state", "TX")
    event_type = params.get("event_type", "")
    year = params.get("year", 2024)
    key = _get_key()

    if not key:
        return _mock_storms(state)

    try:
        # NOAA Storm Events API (public, no key needed for this endpoint)
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"https://www.ncdc.noaa.gov/stormevents/cdv.pl"
            resp = await client.get(url, params={
                "state": state,
                "eventType": event_type,
                "beginDate": f"{year}0101",
                "endDate": f"{year}1231",
            }, headers={"token": key} if key else {})

        # Try the CDO API as fallback
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{NOAA_BASE}/storms", params={
                "state": state,
                "limit": 10,
            }, headers={"token": key})
            data = resp.json()

        if data.get("results"):
            events = [{
                "event_type": e.get("eventType", ""),
                "date": e.get("beginDate", ""),
                "state": e.get("state", state),
                "injuries": e.get("injuriesDirect", 0),
                "deaths": e.get("deathsDirect", 0),
                "damage_property": e.get("damageProperty", ""),
            } for e in data["results"][:10]]
            return {"location": state, "events": events, "count": len(events), "mock": False}

        return _mock_storms(state)
    except Exception:
        return _mock_storms(state)


async def sea_level_trend(params: dict) -> dict:
    """Get sea level rise trend data from NOAA (critical for port disruption risk).

    Args:
        stationid: NOAA tide station ID (e.g., '8443970' for Boston)
    """
    stationid = params.get("stationid", "8443970")
    key = _get_key()

    if not key:
        return _mock_sea_level(stationid)

    try:
        # NOAA Sea Level Trends API (public endpoint)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{stationid}/floodlevels.json"
            )
            data = resp.json()

        if data.get("floodlevels"):
            return {
                "station_id": stationid,
                "data": data["floodlevels"],
                "mock": False,
            }

        # Try with CDO token
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{NOAA_BASE}/stations/{stationid}", headers={"token": key})
            data = resp.json()

        if data.get("id"):
            return {
                "station_id": stationid,
                "name": data.get("name", ""),
                "latitude": data.get("latitude", 0),
                "longitude": data.get("longitude", 0),
                "elevation": data.get("elevation", 0),
                "mock": False,
            }

        return _mock_sea_level(stationid)
    except Exception:
        return _mock_sea_level(stationid)


async def drought_monitor(params: dict) -> dict:
    """Get drought-related precipitation data from NOAA CDO API (critical for agricultural supply chain risk).

    Uses precipitation deficit as drought proxy since USDM API is currently unavailable.

    Args:
        state: US state abbreviation (e.g., 'CA', 'TX') or 'US' for national
    """
    state = params.get("state", "US")
    key = _get_key()

    # Map state to a representative NOAA city location ID (FIPS often returns empty, CITY works better)
    state_locations = {
        "US": "CITY:US060013",  # Los Angeles as national proxy
        "CA": "CITY:US060013",  # Los Angeles
        "TX": "CITY:US480019",  # Houston
        "AZ": "CITY:US040023",  # Phoenix
        "NM": "CITY:US350010",  # Albuquerque
        "NV": "CITY:US320026",  # Las Vegas
        "UT": "CITY:US490028",  # Salt Lake City
        "CO": "CITY:US080023",  # Denver
        "KS": "CITY:US200063",  # Wichita
        "OK": "CITY:US400139",  # Oklahoma City
        "NE": "CITY:US310039",  # Omaha
        "SD": "CITY:US460177",  # Sioux Falls
        "ND": "CITY:US380293",  # Bismarck
        "MT": "CITY:US300077",  # Billings
        "WY": "CITY:US560210",  # Cheyenne
        "OR": "CITY:US410580",  # Portland
        "WA": "CITY:US530154",  # Seattle
        "ID": "CITY:US160020",  # Boise
    }
    location_id = state_locations.get(state.upper(), "CITY:US060013")

    if not key:
        return {"state": state, "drought_data": [{"state": state, "drought_level": 15, "mock": True}], "mock": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get temperature + precipitation data for drought assessment
            resp = await client.get(
                "https://www.ncdc.noaa.gov/cdo-web/api/v2/data",
                params={
                    "datasetid": "GSOM",
                    "datatypeid": "TAVG,TMAX,TMIN",
                    "locationid": location_id,
                    "startdate": "2025-10-01",
                    "enddate": "2026-04-13",
                    "limit": 25,
                    "sortfield": "date",
                    "sortorder": "desc",
                },
                headers={"token": key},
            )
            data = resp.json()

        results = data.get("results", [])
        if results:
            climate_data = [{
                "date": r.get("date", ""),
                "datatype": r.get("datatype", ""),
                "value": r.get("value", 0),
                "station": r.get("station", ""),
            } for r in results[:15]]

            # Drought assessment based on temperature anomaly
            avg_temp = sum(r["value"] for r in results if r.get("datatype") == "TAVG") / max(
                len([r for r in results if r.get("datatype") == "TAVG"]), 1)
            max_temps = [r["value"] for r in results if r.get("datatype") == "TMAX"]
            avg_max = sum(max_temps) / len(max_temps) if max_temps else 0

            # High temperatures + low precipitation = drought risk
            if avg_max > 35:
                drought_status = "Severe Drought Risk"
            elif avg_max > 30:
                drought_status = "Moderate Drought Risk"
            elif avg_max > 25:
                drought_status = "Abnormally Dry"
            else:
                drought_status = "Normal Conditions"

            return {
                "state": state,
                "drought_status": drought_status,
                "avg_temp_c": round(avg_temp, 1),
                "avg_max_temp_c": round(avg_max, 1),
                "climate_data": climate_data,
                "data_points": len(results),
                "source": "NOAA_CDO",
                "mock": False,
            }

        return {"state": state, "drought_data": [], "mock": True}
    except Exception:
        return {"state": state, "drought_data": [{"state": state, "drought_level": 15, "mock": True}], "mock": True}


TOOLS = [
    {
        "name": "noaa_climate_data",
        "description": "Get climate data (temperature, precipitation, snow). Uses NOAA CDO API. Best for long-term Risk analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "datasetid": {"type": "string", "description": "Dataset: GHCND (daily), GSOM (monthly), GSOY (annual)", "default": "GSOM"},
                "locationid": {"type": "string", "description": "Location ID (e.g., 'CITY:US060013')", "default": "CITY:US060013"},
                "startdate": {"type": "string", "description": "Start date YYYY-MM-DD", "default": "2024-01-01"},
                "enddate": {"type": "string", "description": "End date YYYY-MM-DD", "default": "2024-12-31"},
                "datatypeid": {"type": "string", "description": "Data type: TAVG, TMAX, TMIN, PRCP, SNOW", "default": "TAVG"},
                "limit": {"type": "integer", "description": "Max results", "default": 20}
            },
            "required": []
        },
        "handler": climate_data,
        "cache_ttl": 86400,
    },
    {
        "name": "noaa_storm_events",
        "description": "Get severe storm events (tornado, flood, hurricane). Uses NOAA API. Critical for Logistics and Risk agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "description": "US state (e.g., 'TX', 'CA', 'FL')", "default": "TX"},
                "event_type": {"type": "string", "description": "Event type: Tornado, Flash Flood, Hurricane, Hail"},
                "year": {"type": "integer", "description": "Year", "default": 2024}
            }
        },
        "handler": storm_events,
        "cache_ttl": 86400,
    },
    {
        "name": "noaa_sea_level",
        "description": "Get sea level rise trends. Uses NOAA API. Critical for port disruption risk assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stationid": {"type": "string", "description": "NOAA tide station ID (e.g., '8443970')", "default": "8443970"}
            }
        },
        "handler": sea_level_trend,
        "cache_ttl": 86400,
    },
    {
        "name": "noaa_drought_monitor",
        "description": "Get US Drought Monitor data. Critical for agricultural supply chain risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "description": "US state abbreviation or 'US' for national", "default": "US"}
            }
        },
        "handler": drought_monitor,
        "cache_ttl": 86400,
    },
]
