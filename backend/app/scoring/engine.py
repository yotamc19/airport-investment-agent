from app.data.airports import get_airport_by_iata, get_latest_stats
from app.scoring.formulas import (
    compute_capacity_gap,
    compute_congestion,
    compute_growth,
    compute_investment_score,
    compute_long_haul_ratio,
)
from app.scoring.models import ComparisonResult, ScoreResult


def score_airport(iata: str) -> ScoreResult | None:
    airport = get_airport_by_iata(iata)
    if airport is None:
        return None

    stats = get_latest_stats(iata)
    if stats is None:
        return None

    assumptions: list[str] = [
        f"Gate count ({airport.estimated_gates}) is an estimate from public sources",
        f"Capacity assumes ~5.5 flight turns per gate per day",
        f"Data is from {stats.year} BTS reports",
    ]

    congestion = compute_congestion(stats, airport)
    growth = compute_growth(stats)
    capacity_gap = compute_capacity_gap(stats)
    long_haul = compute_long_haul_ratio(stats)
    investment, score_assumptions = compute_investment_score(
        congestion, growth, capacity_gap, long_haul
    )
    assumptions.extend(score_assumptions)

    fields_present = sum([
        stats.total_departures > 0,
        stats.total_passengers > 0,
        stats.avg_departure_delay_min >= 0,
        stats.passenger_growth_yoy_pct is not None,
    ])
    data_completeness = round(fields_present / 4, 2)

    return ScoreResult(
        iata=airport.iata,
        airport_name=airport.name,
        congestion_index=congestion,
        growth_score=growth,
        capacity_gap_score=capacity_gap,
        long_haul_ratio=long_haul,
        investment_score=investment,
        data_completeness=data_completeness,
        assumptions=assumptions,
    )


def compare_airports(iata_codes: list[str]) -> ComparisonResult | None:
    scores: list[ScoreResult] = []
    for iata in iata_codes:
        result = score_airport(iata)
        if result is not None:
            scores.append(result)

    if not scores:
        return None

    analysis: dict[str, str] = {}
    metrics = [
        ("congestion_index", "Congestion"),
        ("capacity_gap_score", "Capacity Gap"),
        ("investment_score", "Investment Score"),
        ("long_haul_ratio", "Long-Haul Ratio"),
    ]

    for attr, label in metrics:
        best = max(scores, key=lambda s: getattr(s, attr))
        worst = min(scores, key=lambda s: getattr(s, attr))
        analysis[label] = (
            f"{best.iata} leads at {getattr(best, attr):.1f}, "
            f"{worst.iata} lowest at {getattr(worst, attr):.1f}"
        )

    growth_scores = [(s, s.growth_score) for s in scores if s.growth_score is not None]
    if growth_scores:
        best_growth = max(growth_scores, key=lambda x: x[1])
        analysis["Growth"] = (
            f"{best_growth[0].iata} leads at {best_growth[1]:.1f}"
        )

    return ComparisonResult(airports=scores, analysis=analysis)
