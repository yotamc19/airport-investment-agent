import json
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.config import settings
from app.data.airports import (
    get_airport_by_iata,
    get_airport_stats,
    get_latest_stats,
    search_airports,
)
from app.scoring.engine import compare_airports, score_airport

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_airports",
        "description": (
            "Search for airports by name, city, state, IATA code, or region. "
            "Regions: New England, Mid-Atlantic, Southeast, Midwest, Southwest, Mountain, West, Pacific."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term: airport name, city, state, IATA code, or region name",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_airport_stats",
        "description": (
            "Get detailed statistics for a specific airport including passenger counts, "
            "flight volumes, delays, load factors, and distance-based flight distribution. "
            "Returns data for all available years (2019, 2022-2024)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "iata_code": {
                    "type": "string",
                    "description": "IATA airport code (e.g., 'LAX', 'BOS', 'SFO')",
                },
                "year": {
                    "type": "integer",
                    "description": "Specific year to get stats for. Omit for all years.",
                },
            },
            "required": ["iata_code"],
        },
    },
    {
        "name": "score_airport",
        "description": (
            "Compute investment opportunity scores for a specific airport. "
            "Returns congestion index, growth score, capacity gap, long-haul ratio, "
            "and composite investment score (all 0-100). Scores are deterministic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "iata_code": {
                    "type": "string",
                    "description": "IATA airport code",
                },
            },
            "required": ["iata_code"],
        },
    },
    {
        "name": "compare_airports",
        "description": (
            "Compare investment metrics across multiple airports side by side. "
            "Returns scores for each airport and identifies which leads in each metric."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "iata_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of IATA codes to compare (e.g., ['LAX', 'SNA'])",
                },
            },
            "required": ["iata_codes"],
        },
    },
    {
        "name": "get_flight_distribution",
        "description": (
            "Get the distance-based flight distribution for an airport: "
            "short-haul (<500mi), medium (500-1500mi), long-haul (>1500mi). "
            "Useful for understanding route profile and revenue potential."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "iata_code": {
                    "type": "string",
                    "description": "IATA airport code",
                },
            },
            "required": ["iata_code"],
        },
    },
    {
        "name": "get_airport_status",
        "description": (
            "Get LIVE current status for an airport from the FAA: "
            "delays, ground stops, weather conditions. This is real-time data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "iata_code": {
                    "type": "string",
                    "description": "IATA airport code",
                },
            },
            "required": ["iata_code"],
        },
    },
]


async def handle_search_airports(query: str, limit: int = 10) -> dict[str, Any]:
    results = search_airports(query, limit)
    return {
        "airports": [a.model_dump() for a in results],
        "count": len(results),
        "query": query,
    }


async def handle_get_airport_stats(iata_code: str, year: int | None = None) -> dict[str, Any]:
    airport = get_airport_by_iata(iata_code)
    if airport is None:
        return {"error": f"Airport '{iata_code}' not found in database"}

    stats = get_airport_stats(iata_code, year)
    if not stats:
        return {"error": f"No statistics available for {iata_code}"}

    return {
        "airport": airport.model_dump(),
        "stats": [s.model_dump() for s in stats],
        "years_available": [s.year for s in stats],
    }


async def handle_score_airport(iata_code: str) -> dict[str, Any]:
    result = score_airport(iata_code)
    if result is None:
        return {"error": f"Cannot score airport '{iata_code}': not found or no data available"}
    return result.model_dump()


async def handle_compare_airports(iata_codes: list[str]) -> dict[str, Any]:
    result = compare_airports(iata_codes)
    if result is None:
        return {"error": "No valid airports found for comparison"}
    return result.model_dump()


async def handle_get_flight_distribution(iata_code: str) -> dict[str, Any]:
    stats = get_latest_stats(iata_code)
    if stats is None:
        return {"error": f"No statistics available for {iata_code}"}

    total = (
        stats.flights_under_500mi
        + stats.flights_500_to_1000mi
        + stats.flights_1000_to_1500mi
        + stats.flights_over_1500mi
    )
    if total == 0:
        return {"error": f"No flight data available for {iata_code}"}

    return {
        "iata": iata_code.upper(),
        "year": stats.year,
        "total_flights": total,
        "distribution": {
            "short_haul_under_500mi": {
                "count": stats.flights_under_500mi,
                "percentage": round(stats.flights_under_500mi / total * 100, 1),
            },
            "medium_500_to_1000mi": {
                "count": stats.flights_500_to_1000mi,
                "percentage": round(stats.flights_500_to_1000mi / total * 100, 1),
            },
            "medium_1000_to_1500mi": {
                "count": stats.flights_1000_to_1500mi,
                "percentage": round(stats.flights_1000_to_1500mi / total * 100, 1),
            },
            "long_haul_over_1500mi": {
                "count": stats.flights_over_1500mi,
                "percentage": round(stats.flights_over_1500mi / total * 100, 1),
            },
        },
        "long_haul_ratio": round(stats.flights_over_1500mi / total * 100, 1),
        "definition": "Long-haul is defined as flights over 1,500 miles great-circle distance",
    }


async def handle_get_airport_status(iata_code: str) -> dict[str, Any]:
    iata = iata_code.upper().strip()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.faa_api_base_url)
            if response.status_code != 200:
                return {
                    "error": f"FAA API returned status {response.status_code}",
                    "note": "Live status unavailable; historical data from other tools is still valid",
                }

        root = ET.fromstring(response.text)
        update_time = root.findtext("Update_Time", "")

        delays: list[dict[str, Any]] = []
        closures: list[dict[str, Any]] = []
        ground_stops: list[dict[str, Any]] = []

        for delay_type in root.findall("Delay_type"):
            category = delay_type.findtext("Name", "")

            for airport_el in delay_type.iter("Airport"):
                arpt = airport_el.findtext("ARPT", "")
                if arpt != iata:
                    continue

                entry = {sub.tag: sub.text for sub in airport_el if sub.text}

                if "Closure" in category:
                    closures.append(entry)
                elif "Ground Stop" in category:
                    ground_stops.append(entry)
                else:
                    delays.append(entry)

        has_issues = bool(delays or closures or ground_stops)

        result: dict[str, Any] = {
            "source": "FAA NAS Status (live)",
            "iata": iata,
            "update_time": update_time,
            "status": "delays/closures reported" if has_issues else "no delays reported",
        }

        if delays:
            result["delays"] = delays
        if closures:
            result["closures"] = closures
        if ground_stops:
            result["ground_stops"] = ground_stops

        return result

    except httpx.TimeoutException:
        return {
            "error": "FAA API timed out",
            "note": "Live status unavailable; historical data from other tools is still valid",
        }
    except httpx.RequestError as e:
        return {
            "error": f"FAA API request failed: {str(e)}",
            "note": "Live status unavailable; historical data from other tools is still valid",
        }


TOOL_HANDLERS = {
    "search_airports": handle_search_airports,
    "get_airport_stats": handle_get_airport_stats,
    "score_airport": handle_score_airport,
    "compare_airports": handle_compare_airports,
    "get_flight_distribution": handle_get_flight_distribution,
    "get_airport_status": handle_get_airport_status,
}


async def dispatch_tool(name: str, arguments: dict[str, Any]) -> str:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    result = await handler(**arguments)
    return json.dumps(result, default=str)
