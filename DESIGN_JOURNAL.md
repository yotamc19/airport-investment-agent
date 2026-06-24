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

*Entries will be added as development progresses...*
