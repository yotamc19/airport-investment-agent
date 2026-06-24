# Airport Investment Intelligence Agent

## Project Overview
AI-powered agent that helps analysts identify promising airport investment opportunities for terminal expansion and modernization. Built as a take-home assignment for Wonderful (agent startup).

## Architecture
- **Frontend:** Next.js + React chat interface
- **Backend:** Python + FastAPI — LLM orchestrator with tool-calling pattern
- **Scoring Layer:** Pure Python, deterministic — no LLM involved in number crunching
- **LLM Role:** Orchestrator only — decides which tools to call, interprets deterministic results, explains reasoning to the user

The LLM has NO pre-loaded aviation knowledge. It calls tools (Python functions) that fetch data from public APIs and compute scores. This separation ensures scores are auditable and never hallucinated.

## Tech Stack
- `bun` for frontend package management
- Python with FastAPI for backend
- Next.js + React for chat UI

## Key Files
- `DESIGN_JOURNAL.md` — Chronological decision log. Shows the interviewer how we thought through the problem.
- `evals/questions.json` — Test database. Questions with expected answers for validating agent quality.

## Rules — IMPORTANT

### Design Journal
When making a significant architectural, design, or scoring decision, **add a new numbered entry** to `DESIGN_JOURNAL.md`. Each entry must include:
- A clear title and date
- The problem or question being addressed
- The decision and reasoning
- What alternatives were considered and why they were rejected
- Any tradeoffs accepted

Do NOT rewrite existing entries. Append only. The journal is chronological — it tells a story.

### Evaluation Database
When encountering a question or edge case the agent handles poorly:
1. Add it to `evals/questions.json` with `must_include` and `must_not_include` assertions
2. Fix the agent logic
3. Re-run evals to confirm the fix doesn't break other questions

The eval DB only grows — never remove questions. If an expected answer changes due to a logic update, update the expected answer and document why in the design journal.

### Scoring
All scores (congestion, growth, capacity gap, long-haul ratio, investment score) are computed deterministically in Python. The LLM interprets and explains scores but NEVER generates them. If a score can't be computed due to missing data, return null — don't estimate.

### Uncertainty
The agent must explicitly communicate:
- What data it has vs. what it's missing
- What assumptions the scoring model makes
- Confidence level in its recommendations
- When a question falls outside its capabilities

### Code Conventions
- TypeScript strict in frontend; no `any`
- Python type hints throughout backend
- No speculative abstractions — solve the current problem
