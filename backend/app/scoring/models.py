from pydantic import BaseModel


class Airport(BaseModel):
    iata: str
    icao: str
    name: str
    city: str
    state: str
    region: str
    latitude: float
    longitude: float
    estimated_gates: int
    runways: int
    hub_size: str


class AirportStats(BaseModel):
    year: int
    total_departures: int
    total_passengers: int
    available_seats: int
    load_factor: float
    avg_departure_delay_min: float
    pct_flights_delayed: float
    flights_under_500mi: int
    flights_500_to_1000mi: int
    flights_1000_to_1500mi: int
    flights_over_1500mi: int
    passenger_growth_yoy_pct: float | None
    estimated_annual_capacity: int


class ScoreResult(BaseModel):
    iata: str
    airport_name: str
    congestion_index: float
    growth_score: float | None
    capacity_gap_score: float
    long_haul_ratio: float
    investment_score: float
    data_completeness: float
    assumptions: list[str]


class ComparisonResult(BaseModel):
    airports: list[ScoreResult]
    analysis: dict[str, str]
