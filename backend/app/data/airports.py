import json
from pathlib import Path

from app.data.regions import REGION_STATES
from app.scoring.models import Airport, AirportStats

_DATA_DIR = Path(__file__).parent / "static"
_airports_cache: list[Airport] | None = None
_stats_cache: dict[str, list[AirportStats]] | None = None


def _load_airports() -> list[Airport]:
    global _airports_cache
    if _airports_cache is None:
        with open(_DATA_DIR / "airports.json") as f:
            _airports_cache = [Airport(**a) for a in json.load(f)]
    return _airports_cache


def _load_stats() -> dict[str, list[AirportStats]]:
    global _stats_cache
    if _stats_cache is None:
        with open(_DATA_DIR / "airport_stats.json") as f:
            raw = json.load(f)
        _stats_cache = {
            iata: [AirportStats(**s) for s in years]
            for iata, years in raw.items()
        }
    return _stats_cache


def get_airport_by_iata(iata: str) -> Airport | None:
    iata = iata.upper().strip()
    for airport in _load_airports():
        if airport.iata == iata:
            return airport
    return None


def search_airports(query: str, limit: int = 10) -> list[Airport]:
    query_lower = query.lower().strip()
    airports = _load_airports()

    region_states = REGION_STATES.get(
        next((r for r in REGION_STATES if r.lower() == query_lower), ""), []
    )
    if region_states:
        return [a for a in airports if a.state in region_states][:limit]

    if len(query_lower) == 2:
        state_matches = [a for a in airports if a.state.lower() == query_lower]
        if state_matches:
            return state_matches[:limit]

    scored: list[tuple[int, Airport]] = []
    for airport in airports:
        score = 0
        if airport.iata.lower() == query_lower:
            score = 100
        elif query_lower in airport.name.lower():
            score = 80
        elif query_lower in airport.city.lower():
            score = 70
        elif query_lower in airport.state.lower():
            score = 60
        if score > 0:
            scored.append((score, airport))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored][:limit]


def get_airport_stats(iata: str, year: int | None = None) -> list[AirportStats]:
    iata = iata.upper().strip()
    stats = _load_stats()
    airport_stats = stats.get(iata, [])
    if year is not None:
        return [s for s in airport_stats if s.year == year]
    return airport_stats


def get_latest_stats(iata: str) -> AirportStats | None:
    all_stats = get_airport_stats(iata)
    if not all_stats:
        return None
    return max(all_stats, key=lambda s: s.year)
