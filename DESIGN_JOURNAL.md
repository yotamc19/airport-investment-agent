# Design Journal — Airport Investment Intelligence Agent

A living document capturing the thinking process, decisions, and tradeoffs as this project was built. Written chronologically so you can follow the reasoning as it evolved.

---

## Entry 1 — Choosing the Architecture (June 24, 2026)

### The Question
How should the agent "know" about airports? Three options on the table:

1. **Fine-tuning** — Train the model on aviation data so it "memorizes" it
2. **RAG** — Pre-load documents into a searchable index, let the model look things up
3. **Tool-use agent** — Give the model functions it can call to fetch data on demand

### The Decision: Tool-use agent

**Why not fine-tuning?**
Our data is public and changes over time (flight volumes, delays, passenger counts). Baking it into the model means it goes stale. Fine-tuning is also expensive and slow — overkill for structured data that lives in APIs.

**Why not RAG?**
RAG shines when you have lots of unstructured text (reports, PDFs, articles) and need the model to find relevant passages. Our data is structured — numbers, statistics, tables. You don't "search" for a congestion score in a paragraph, you compute it from data.

**Why tool-use?**
The model acts as a reasoning layer on top of deterministic tools. When asked "How congested is LAX?", it calls a function that fetches real data and computes a score. The model then interprets and explains the result. Data is always fresh, scores are auditable, and the model focuses on what it's good at — reasoning and communication.

### Architecture Overview

```
[Chat UI — Next.js] → [Agent Backend — Python/FastAPI] → [Data + Scoring Layer]
                              |
                        LLM (orchestrator)
                              |
                    ┌─────────┼─────────┐
                    ↓         ↓         ↓
              search_airports  score   compare
              get_stats     flights   rank
```

- **Layer 1 — Chat UI:** Next.js React app. Sends messages, streams responses, maintains conversation history for follow-ups.
- **Layer 2 — Agent Backend:** The LLM receives the user's question + tool descriptions. It decides which tools to call, calls them, receives structured results, then composes a natural-language response with reasoning.
- **Layer 3 — Data + Scoring:** Pure Python. No LLM involved. Fetches data from public APIs, computes deterministic scores. This separation is critical — the numbers are never hallucinated.

### Key Tradeoff
Tool-use means the agent has no knowledge without calling tools. If an API is down or a data point is missing, the agent must say "I don't have this data" rather than guessing. We treat this as a feature — explicit uncertainty is better than confident hallucination in an investment context.

---

## Entry 2 — Scoring Methodology (June 24, 2026)

### The Problem
The assignment requires "deterministic scoring or ranking logic, not only LLM output." We need a clear, reproducible formula that an analyst could audit.

### The Scores

| Score | Range | What it measures | Why it matters for investment |
|-------|-------|-----------------|------------------------------|
| Congestion Index | 0–100 | How overloaded the airport is (delays, flights per gate) | High congestion = capacity ceiling = renovation demand |
| Growth Score | 0–100 | Year-over-year passenger/flight growth trajectory | Growing airports justify investment — the demand is coming |
| Capacity Gap | 0–100 | Gap between current throughput and estimated max capacity | Large gap = the airport physically can't handle its demand |
| Long-Haul Ratio | 0–100% | Share of flights over 1,500 miles | Long-haul = international/premium traffic = higher revenue per passenger |

### Composite: Investment Opportunity Score (0–100)

```
investment_score = (0.30 × congestion) + (0.30 × capacity_gap) + (0.25 × growth) + (0.15 × long_haul_ratio)
```

**Weight rationale:**
- Congestion and capacity gap weighted highest (0.30 each) — these directly indicate physical need for expansion
- Growth weighted next (0.25) — validates that demand will sustain the investment
- Long-haul ratio lowest (0.15) — it's a revenue quality indicator, not a direct capacity signal

### Assumptions & Caveats
- "Estimated max capacity" is derived from available data (gates, runways, historical peaks) — it's an approximation, not an engineering assessment
- Scores are relative within the dataset, not absolute truths
- The model is instructed to communicate these limitations when presenting results

---

## Entry 3 — Evaluation Strategy (June 24, 2026)

### The Problem
How do we know the agent is giving good answers? LLM outputs are non-deterministic — the same question can get different responses. We need a way to validate quality systematically.

### The Solution: Question-Answer Test Database
We maintain a set of test questions, each with an expected answer. On every logic change, we run the full suite and check how close the agent's responses are to the expected answers.

This serves two purposes:
1. **Regression testing** — catch when a change breaks previously working answers
2. **Quality benchmarking** — track improvement over time

### How "closeness" is evaluated
We use an LLM-as-judge approach: a separate LLM call compares the agent's response to the expected answer and scores on:
- **Factual accuracy** — are the numbers/rankings correct?
- **Reasoning quality** — does the explanation make sense?
- **Completeness** — did it address all parts of the question?

The test DB starts small (the 4 examples from the assignment) and grows as we discover edge cases.

---

## Entry 4 — Data Strategy: Static + Live Hybrid (June 25, 2026)

### The Problem
The assignment says "use public APIs to gather airport/aviation data." But real aviation APIs (AviationStack, BTS SODA) have rate limits, can be slow, and might be down during the interview demo. How do we satisfy the API requirement without risking a broken demo?

### The Decision: Hybrid — static JSON for historical stats, live FAA API for real-time status

**Historical stats (static):** Passenger counts, delays, growth, flight distributions — these are published annually by BTS and don't change day-to-day. Bundled as `airports.json` (62 airports) and `airport_stats.json` (4 years per airport). The scoring engine runs entirely on this data.

**Real-time status (live API):** The FAA Airport Status API (`soa.smext.faa.gov`) provides current delays, ground stops, and weather. Free, no key needed, reliable. This is the `get_airport_status` tool — it's the only tool making a real HTTP call.

**Timeframe: 2019 + 2022-2024.** We include 2019 as a pre-COVID baseline and skip 2020-2021 (anomaly years that would distort growth trends). This gives us real recovery trajectory data — is the airport growing vs its own pre-COVID peak?

### Alternatives Considered
- **All live API:** More impressive but fragile. AviationStack's free tier gives ~100 requests/month — one demo could exhaust it.
- **All static:** Reliable but doesn't satisfy the "use public APIs" requirement.
- **Multiple live APIs:** More code for marginal benefit. One live API demonstrates the pattern; the interviewer can see it works.

### Tradeoff
Static data is frozen at 2024. We document this assumption in the system prompt and every score result, so the agent always tells the user the data vintage.

---

## Entry 5 — Tool Call Observability (June 25, 2026)

### The Problem
When the agent takes 10 seconds to answer, the user stares at a loading spinner with no idea what's happening. And during development, we need to see which tools the agent calls and whether the results make sense.

### The Decision: Log tool calls server-side AND display them in the frontend

**Server-side:** Each tool call logs to stdout with name, input, and result preview. The terminal shows the full reasoning chain as it happens.

**Client-side:** The `/chat` response includes a `tool_calls` array. The frontend renders a "Tools called" section above each assistant message showing exactly which tools were invoked (e.g., `search_airports(query="New England")`, `score_airport(iata_code="BOS")`).

### Why This Matters
For the interview, this is a differentiator. It shows the agent isn't a black box — the interviewer can see the agent's reasoning process. It also builds trust: you can verify the agent called the right tools and used real data.

### What We Didn't Do (Yet)
Server-Sent Events for live streaming of tool calls as they happen. The user sees them only after all tools complete. This is a future polish item — adds complexity without changing correctness.

---

## Entry 6 — LLM Model Choice: Sonnet over Opus (June 25, 2026)

### The Problem
Which Claude model should the agent use? The Anthropic API offers several options with different capability/cost/speed tradeoffs.

### The Decision: Claude Sonnet 4.6 (`claude-sonnet-4-6`)

**Why not Opus?** The LLM's job is orchestration — deciding which tools to call and interpreting deterministic results. This doesn't require frontier-level reasoning. Sonnet handles tool-calling and natural language interpretation well. Opus costs ~5x more and is slower, which means longer wait times for the user with no meaningful quality improvement.

**Why not Haiku?** Haiku is fast and cheap but may produce less nuanced interpretations. For an interview demo where response quality matters, Sonnet is the sweet spot.

### Key Insight
The scoring quality doesn't depend on the LLM at all — scores are deterministic Python. The LLM only needs to: (1) parse user intent correctly, (2) call the right tools, (3) explain the results clearly. Sonnet does all three well.

---

## Entry 7 — Replace Next.js with Vite (June 25, 2026)

### The Problem
The frontend uses Next.js, but we don't use any of its distinguishing features: no server-side rendering, no file-based routing, no API routes (the API is a separate Python backend). The app is a single-page chat UI.

### The Decision: Swap to Vite + React
Vite is a lightweight build tool that does exactly what we need — fast dev server, HMR, and production bundling — without the abstraction overhead of a full framework.

### What we considered
- **Keep Next.js:** Familiar, but adds ~10 config files and concepts (App Router, `"use client"` directives, `next/font`, server components) that don't serve us. Extra complexity with no benefit is a code smell in a take-home.
- **Vite:** Minimal config (`vite.config.ts`, `index.html`, `main.tsx`). Same `bun run dev` workflow. No framework concepts to explain away.
- **Parcel / esbuild direct:** Even lighter, but Vite's React plugin and Tailwind integration are more mature and well-documented.

### Tradeoffs
- Lost Next.js's built-in font optimization (`next/font`) — replaced with a standard Google Fonts `<link>`. Negligible impact for an internal tool / demo.
- Lost built-in ESLint config (`eslint-config-next`) — removed for now; can add a standalone config if needed.
- CORS origin updated from port 3000 to 5173 (Vite's default).

---

## Entry 8 — Migrate FAA Live Status API (June 25, 2026)

### The Problem
The `get_airport_status` tool calls the FAA's Airport Status Web Service at `soa.smext.faa.gov/asws/api/airport/status/{IATA}` for live delay and closure data. This endpoint started returning DNS resolution failures (NXDOMAIN) — the FAA retired the hostname.

### The Decision: Switch to the FAA NAS Status API
The replacement endpoint is `nasstatus.faa.gov/api/airport-status-information`. Key differences from the old API:

- **Single endpoint, all airports:** Returns one XML document covering all US airports, instead of per-airport JSON. We fetch once and filter by IATA code.
- **XML instead of JSON:** Requires parsing with `xml.etree.ElementTree` instead of `response.json()`.
- **Categorized events:** The response groups events by type (closures, ground stops, delays), so we surface that structure to the LLM.

### What we considered
- **Remove the tool entirely:** The tool isn't used for scoring, so we could drop it. But live status adds real value for an investment analyst — knowing an airport is currently experiencing ground stops or closures adds context. It also demonstrates the agent can combine static analysis with real-time data.
- **Mock/stub the response:** Would make the demo more predictable, but undermines the point of having a live data tool.

### Tradeoffs
- The new API returns everything in one call, so we parse more data than needed per request. For ~60 airports this is negligible.
- If the FAA moves this endpoint again, the same failure mode returns. The error handling remains in place for graceful degradation.

---

*Entries will be added as development progresses...*
