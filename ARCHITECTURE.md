# Architecture & Design Document

## Overview

An AI-powered agent that helps investment analysts identify airports where renovations will be most profitable. The agent combines **deterministic scoring** (auditable, reproducible numbers) with **LLM reasoning** (natural language interpretation, multi-step planning) to answer open-ended investment questions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                   (Next.js + React)                         │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ InputBar │→ │ useChat hook │→ │ POST /chat            │ │
│  └──────────┘  │ (owns state) │  │ {message, history}    │ │
│                └──────────────┘  └───────────┬───────────┘ │
│  ┌─────────────────────────────┐             │             │
│  │ MessageList + Message       │             │             │
│  │ (markdown, tables, scores)  │             │             │
│  └─────────────────────────────┘             │             │
└──────────────────────────────────────────────┼─────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  Agent Orchestrator                     │ │
│  │                                                        │ │
│  │  1. Receive user message + conversation history        │ │
│  │  2. Send to Claude API with tool definitions           │ │
│  │  3. If Claude requests tool calls → execute them       │ │
│  │  4. Feed tool results back to Claude                   │ │
│  │  5. Repeat until Claude returns final text response    │ │
│  │                                                        │ │
│  │  Claude decides WHICH tools to call and in WHAT ORDER  │ │
│  │  based on the user's question. It never generates      │ │
│  │  data — only interprets tool results.                  │ │
│  └──────────┬─────────────────────────────────────────────┘ │
│             │ calls                                         │
│             ▼                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Agent Tools                         │ │
│  │                                                        │ │
│  │  search_airports(query)        ── Static JSON lookup   │ │
│  │  get_airport_stats(iata)       ── Static JSON lookup   │ │
│  │  score_airport(iata)           ── Scoring Engine        │ │
│  │  compare_airports(iata[])      ── Scoring Engine        │ │
│  │  get_flight_distribution(iata) ── Static JSON lookup   │ │
│  │  get_airport_status(iata)      ── Live FAA API ←──────────── Real-time
│  │                                                        │ │
│  └──────────┬──────────────┬──────────────────────────────┘ │
│             │              │                                │
│             ▼              ▼                                │
│  ┌──────────────┐  ┌─────────────────────────────────────┐ │
│  │  Data Layer  │  │        Scoring Engine                │ │
│  │              │  │        (pure Python)                 │ │
│  │  airports    │  │                                     │ │
│  │  .json       │→ │  congestion_index()    ─┐           │ │
│  │              │  │  growth_score()         │→ invest-  │ │
│  │  airport_    │  │  capacity_gap_score()   │  ment_    │ │
│  │  stats.json  │→ │  long_haul_ratio()     ─┘  score() │ │
│  │              │  │                                     │ │
│  │  FAA API     │  │  No LLM. No estimation.             │ │
│  │  (live)      │  │  Deterministic & auditable.         │ │
│  └──────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Where & How AI Is Used

The LLM (Claude) serves exactly one role: **orchestration and interpretation**. It does NOT generate data or compute scores.

| Responsibility | Who does it | Why |
|---|---|---|
| Understand the user's question | LLM | Natural language understanding, intent parsing |
| Decide which tools to call | LLM | Multi-step reasoning (e.g., "search region first, then score each airport") |
| Fetch airport data | Tools (Python) | Deterministic lookup from static data or FAA API |
| Compute investment scores | Tools (Python) | Deterministic formulas — reproducible, auditable |
| Interpret results for the user | LLM | Explain what scores mean, compare airports, flag caveats |
| Handle follow-up questions | LLM | Conversation history management, context awareness |

### Example: "Which airports in New England are strong candidates for terminal expansion?"

```
User asks question
  → LLM: "I need to find airports in New England, then score each one"
  → LLM calls: search_airports("New England")
  → Tool returns: [BOS, BDL, PVD, MHT, PWM, BTV]
  → LLM calls: score_airport("BOS"), score_airport("BDL"), ...
  → Tool returns: deterministic scores for each
  → LLM: ranks by investment_score, explains WHY BOS ranks highest
        (high congestion + high growth + large capacity gap),
        mentions assumptions and data limitations
```

### Why not RAG or fine-tuning?

| Approach | Why it doesn't fit |
|---|---|
| **Fine-tuning** | Our data is public and changes over time. Baking it into model weights means it goes stale. Also expensive and slow for structured data. |
| **RAG** | Best for searching unstructured text (reports, PDFs). Our data is structured numbers and statistics — you compute scores from data, you don't search for them in paragraphs. |
| **Tool-use** (chosen) | The model reasons over real-time tool results. Data is always fresh, scores are auditable, and the model focuses on what it's good at — reasoning and communication. |

---

## Scoring Methodology

All scores are computed deterministically in Python. The LLM interprets and explains them but never generates them.

### Individual Scores

#### Congestion Index (0–100)
How overloaded is this airport? High congestion signals physical need for expansion.

```
congestion = delay_severity (0-50) + load_factor_pressure (0-30) + gate_intensity (0-20)

delay_severity    = min(avg_delay_minutes / 30, 1.0) × 50
load_factor_pressure = min(max(load_factor - 0.70, 0) / 0.25, 1.0) × 30
gate_intensity    = min(daily_flights_per_gate / 6.0, 1.0) × 20
```

- Delay severity: 30+ minutes average delay = max score
- Load factor: measures how full planes are (0.70 baseline, 0.95 = max pressure)
- Gate intensity: 6+ flights per gate per day = max intensity

#### Growth Score (0–100)
Is demand increasing? Growing airports justify investment.

```
growth_score = clamp(((yoy_passenger_growth% + 5) / 15) × 100, 0, 100)
```

Maps year-over-year passenger growth linearly: -5% → 0, +10% → 100. If growth data is unavailable, defaults to 50 (neutral) with a documented assumption.

#### Capacity Gap Score (0–100)
Can the airport handle its current demand?

```
utilization = total_departures / estimated_annual_capacity
capacity_gap = clamp(((utilization - 0.5) / 0.5) × 100, 0, 100)
```

50% utilization → score 0 (plenty of room). 100%+ utilization → score 100 (over capacity).

**Key assumption:** `estimated_annual_capacity = gates × 5.5 flights/gate/day × 365`. The 5.5 figure is a blended industry average (~6 for domestic, ~4 for international). This is an approximation, not an engineering assessment.

#### Long-Haul Ratio (0–100%)
What share of flights travel over 1,500 miles?

```
long_haul_ratio = flights_over_1500mi / total_flights × 100
```

Higher ratio indicates international/premium traffic with higher revenue per passenger. Important for investment return projections.

### Composite: Investment Opportunity Score (0–100)

```
investment_score = 0.30 × congestion
                 + 0.30 × capacity_gap
                 + 0.25 × growth
                 + 0.15 × long_haul_ratio
```

| Weight | Score | Rationale |
|--------|-------|-----------|
| 0.30 | Congestion | Directly indicates physical need for expansion |
| 0.30 | Capacity Gap | Quantifies how much the airport is underbuilt for its demand |
| 0.25 | Growth | Validates that demand will sustain the investment |
| 0.15 | Long-Haul Ratio | Revenue quality indicator — not a direct capacity signal, so weighted lowest |

---

## Data Strategy

### Static Dataset (bundled, primary)
Two JSON files with pre-aggregated data for ~60 US airports:
- **`airports.json`** — metadata: IATA, name, city, state, region, gates, runways, hub size
- **`airport_stats.json`** — performance: departures, passengers, seats, delays, load factor, flight distance buckets, YoY growth

Source: BTS T-100 Domestic Segment + On-Time Performance databases (2019 baseline + 2022–2024, skipping COVID anomaly years 2020–2021). Gate counts curated from FAA and public sources.

### Live API (FAA Airport Status, supplemental)
- **Endpoint:** `https://soa.smext.faa.gov/asws/api/airport/status/{code}`
- **No API key required**
- **Provides:** current delays, ground stops, weather conditions
- **Used by:** `get_airport_status` tool — gives the agent real-time context that static data can't provide

### Why this split?
Historical stats (passengers, delays, growth) don't change in real time — an API adds no value over bundled data, and introduces a failure point. Current airport status (delays, weather) is inherently real-time and justifies a live API call. The interviewer sees real API calls; the demo never breaks because scoring relies on local data.

---

## Key Tradeoffs

| Decision | Alternative | Why we chose this |
|---|---|---|
| Tool-use over RAG | RAG with aviation documents | Our data is structured numbers, not text to search. Tool-use computes from data directly. |
| Static + live hybrid | Fully live API | Static data is reliable for demos. FAA API satisfies "use public APIs" requirement without risking the scoring pipeline. |
| Synchronous over streaming | Streaming responses | Tool-use + streaming is significantly more complex. Synchronous is cleaner for a one-day build. |
| Stateless backend | Server-side session storage | Frontend owns conversation history. Simpler, no session management, easy to reason about. |
| Estimated capacity | Omit capacity metric | No public API provides max capacity. Our estimate (gates × 5.5 × 365) is transparent and documented. Omitting it would lose a key investment signal. |
| Keyword eval over LLM-judge | LLM-as-judge evaluation | Keyword matching is fast, free, deterministic, and debuggable. LLM-judge can be layered on later. |

---

## Assumptions & Limitations

1. **Gate counts are estimates** — sourced from public references (FAA, airport websites), not official engineering data
2. **Capacity formula is approximate** — 5.5 flights/gate/day is an industry average, not airport-specific
3. **Data vintage** — static dataset is from 2023–2024 BTS reports; real-time conditions may differ
4. **US airports only** — the dataset covers ~60 major US airports; international airports are out of scope
5. **Scoring weights are opinionated** — the 30/30/25/15 split reflects our investment thesis; different investors might weight differently
6. **Growth requires 2+ years of data** — airports with only one year default to a neutral growth score (50/100)

The agent is instructed to communicate these limitations in every response.

---

## Evaluation Strategy

A test database (`evals/questions.json`) contains questions with expected answer assertions:
- `must_include` — facts/reasoning the response must contain
- `must_not_include` — red flags (wrong airports, hallucinated data)

An eval runner sends each question to the agent, grades responses via keyword matching, and reports pass/fail. The database grows as edge cases are discovered — questions are never removed, only added.
