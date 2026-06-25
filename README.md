# ✈️ Airport Investment Intelligence Agent

AI-powered agent that helps analysts identify promising US airport investment opportunities for terminal expansion and modernization.

Ask it questions like:
- *"Which airports in New England are strong candidates for terminal expansion?"*
- *"Compare LAX and Santa Ana airport congestion levels"*
- *"What percentage of flights out of Anchorage are long-haul?"*

The agent calls tools, crunches real data, and explains its reasoning — it never makes up numbers.

---

## 🏗️ How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Chat UI    │────▶│  Agent Backend   │────▶│  Scoring Engine  │
│  Vite/React  │◀────│  Python/FastAPI   │◀────│  Pure Python     │
└──────────────┘     └──────────────────┘     └─────────────────┘
                            │
                      Claude (LLM)
                      orchestrates
                      tool calls
```

**The key design principle:** The LLM decides *which* tools to call and *explains* the results, but all scores are computed deterministically in Python. No hallucinated statistics.

| Layer | Role |
|---|---|
| 🖥️ **Frontend** | Chat interface with markdown rendering, voice input/output |
| 🤖 **Agent** | Claude orchestrates tool calls based on user questions |
| 📊 **Scoring** | Deterministic formulas for congestion, growth, capacity gap |
| 📦 **Data** | Static BTS/FAA dataset (~60 airports) + live FAA status API |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [Bun](https://bun.sh) (or Node.js 18+)
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone & set up environment

```bash
git clone <repo-url>
cd airport-investment-agent
```

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
bun install
bun dev
```

Open **http://localhost:5173** and start chatting! 💬

---

## 📊 Scoring Methodology

All scores are **0–100**, computed from public FAA/BTS data:

| Score | What It Measures | Formula Highlights |
|---|---|---|
| 🔴 **Congestion** | How overloaded is the airport? | Delay severity + load factor + gate intensity |
| 📈 **Growth** | Is demand increasing? | YoY passenger growth mapped linearly |
| 🏗️ **Capacity Gap** | Is the airport underbuilt? | Flight volume vs. estimated max capacity |
| 🌍 **Long-Haul Ratio** | Revenue quality indicator | % of flights over 1,500 miles |
| ⭐ **Investment Score** | Composite opportunity signal | 30% congestion + 30% capacity gap + 25% growth + 15% long-haul |

A high investment score means: *congested, growing, physically underbuilt, and serving premium routes.*

> 📖 Full methodology details in [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🧰 Agent Tools

The LLM has 6 tools available:

| Tool | Description | Data Source |
|---|---|---|
| `search_airports` | Find airports by name, city, state, or region | Static dataset |
| `get_airport_stats` | Passenger counts, delays, load factors | Static dataset |
| `score_airport` | Compute all investment scores | Scoring engine |
| `compare_airports` | Side-by-side multi-airport comparison | Scoring engine |
| `get_flight_distribution` | Short/medium/long-haul breakdown | Static dataset |
| `get_airport_status` | Live delays, weather, ground stops | 🔴 FAA API (real-time) |

---

## 🎙️ Bonus: Voice Support

- **Voice input** — click the microphone button to speak your question (uses browser Speech Recognition API)
- **Voice output** — click "Listen" on any response, or toggle "Auto-speak" to hear every answer (uses browser Speech Synthesis API)

No external services required — voice runs entirely in the browser.

---

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agent/          # LLM orchestrator + system prompt + tool definitions
│   │   ├── data/           # Airport database + region mappings
│   │   │   └── static/     # airports.json + airport_stats.json
│   │   ├── scoring/        # Deterministic scoring formulas
│   │   └── routers/        # FastAPI endpoints
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── App.tsx          # Chat UI component
│       └── hooks/           # useVoiceInput + useVoiceOutput
├── evals/
│   └── questions.json       # Test database with expected-answer assertions
├── ARCHITECTURE.md          # Detailed design & scoring doc
├── DESIGN_JOURNAL.md        # Chronological decision log
└── .env                     # Your API key (not committed)
```

---

## 📝 Design Documents

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Scoring formulas, data strategy, where AI is used, key tradeoffs
- **[DESIGN_JOURNAL.md](./DESIGN_JOURNAL.md)** — Chronological record of every design decision and why

---

## ⚠️ Assumptions & Limitations

1. **US airports only** — dataset covers ~60 major airports
2. **Gate counts are estimates** — sourced from public references, not official engineering data
3. **Capacity formula is approximate** — assumes ~5.5 flights/gate/day (industry average)
4. **Data vintage** — static data from 2019 + 2022–2024 BTS reports (COVID years excluded)
5. **Scoring weights are opinionated** — the 30/30/25/15 split reflects one investment thesis

The agent is designed to communicate these limitations in every response.
