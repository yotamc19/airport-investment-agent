from app.scoring.models import Airport, AirportStats


def compute_congestion(stats: AirportStats, airport: Airport) -> float:
    delay_score = min(stats.avg_departure_delay_min / 30.0, 1.0) * 50

    load_pressure = max(stats.load_factor - 0.70, 0) / 0.25
    load_score = min(load_pressure, 1.0) * 30

    if airport.estimated_gates > 0:
        daily_flights = stats.total_departures / 365
        flights_per_gate = daily_flights / airport.estimated_gates
        gate_score = min(flights_per_gate / 6.0, 1.0) * 20
    else:
        gate_score = 10.0

    return round(delay_score + load_score + gate_score, 1)


def compute_growth(stats: AirportStats) -> float | None:
    if stats.passenger_growth_yoy_pct is None:
        return None
    score = ((stats.passenger_growth_yoy_pct + 5) / 15) * 100
    return round(max(0, min(100, score)), 1)


def compute_capacity_gap(stats: AirportStats) -> float:
    if stats.estimated_annual_capacity <= 0:
        return 50.0
    utilization = stats.total_departures / stats.estimated_annual_capacity
    score = ((utilization - 0.5) / 0.5) * 100
    return round(max(0, min(100, score)), 1)


def compute_long_haul_ratio(stats: AirportStats) -> float:
    total = (
        stats.flights_under_500mi
        + stats.flights_500_to_1000mi
        + stats.flights_1000_to_1500mi
        + stats.flights_over_1500mi
    )
    if total == 0:
        return 0.0
    return round(stats.flights_over_1500mi / total * 100, 1)


def compute_investment_score(
    congestion: float,
    growth: float | None,
    capacity_gap: float,
    long_haul_ratio: float,
) -> tuple[float, list[str]]:
    assumptions: list[str] = []

    if growth is None:
        growth = 50.0
        assumptions.append("Growth data unavailable; assumed neutral (50/100)")

    score = (
        0.30 * congestion
        + 0.30 * capacity_gap
        + 0.25 * growth
        + 0.15 * long_haul_ratio
    )
    return round(score, 1), assumptions
