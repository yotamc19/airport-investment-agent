STATE_TO_REGION: dict[str, str] = {
    "CT": "New England", "ME": "New England", "MA": "New England",
    "NH": "New England", "RI": "New England", "VT": "New England",
    "NJ": "Mid-Atlantic", "NY": "Mid-Atlantic", "PA": "Mid-Atlantic",
    "DC": "Mid-Atlantic", "DE": "Mid-Atlantic", "MD": "Mid-Atlantic",
    "VA": "Mid-Atlantic",
    "AL": "Southeast", "AR": "Southeast", "FL": "Southeast",
    "GA": "Southeast", "KY": "Southeast", "LA": "Southeast",
    "MS": "Southeast", "NC": "Southeast", "SC": "Southeast",
    "TN": "Southeast", "WV": "Southeast",
    "IL": "Midwest", "IN": "Midwest", "IA": "Midwest",
    "KS": "Midwest", "MI": "Midwest", "MN": "Midwest",
    "MO": "Midwest", "NE": "Midwest", "ND": "Midwest",
    "OH": "Midwest", "SD": "Midwest", "WI": "Midwest",
    "AZ": "Southwest", "NM": "Southwest", "OK": "Southwest",
    "TX": "Southwest",
    "CO": "Mountain", "ID": "Mountain", "MT": "Mountain",
    "NV": "Mountain", "UT": "Mountain", "WY": "Mountain",
    "CA": "West", "OR": "West", "WA": "West",
    "AK": "Pacific", "HI": "Pacific",
}

REGION_STATES: dict[str, list[str]] = {}
for state, region in STATE_TO_REGION.items():
    REGION_STATES.setdefault(region, []).append(state)
