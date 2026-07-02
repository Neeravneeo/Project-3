# ⚡ TradeAI — AI Investment Intelligence Platform

> An AI-powered trading platform that auto-trades and auto-hedges your portfolio using real-time market signals, news sentiment, and explainable AI recommendations.

---

## 📋 Project Documents (Read These First)

| # | Document | Purpose |
|---|---|---|
| 1 | [PRD](docs/1_PRD.md) | What we're building, user stories, MVP scope |
| 2 | [TRD](docs/2_TRD.md) | Full tech stack, architecture, APIs |
| 3 | [App Flow](docs/3_APP_FLOW.md) | Every page, user action, navigation path |
| 4 | [UI/UX Brief](docs/4_UI_UX_BRIEF.md) | Design system, colors, components |
| 5 | [Backend Schema](docs/5_BACKEND_SCHEMA.md) | All database tables, indexes, Redis keys |
| 6 | [Implementation Plan](docs/6_IMPLEMENTATION_PLAN.md) | Phase-by-phase build order (Jules + Antigravity) |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| AI Agents | LangGraph + LangChain + Google Gemini |
| Sentiment | FinBERT (ProsusAI/finbert) |
| Database | PostgreSQL 16 + TimescaleDB |
| Cache | Redis 7 |
| Task Queue | Celery |
| Broker (US) | Alpaca (alpaca-py) |
| Frontend | Next.js 14, TypeScript, Tailwind, shadcn/ui |
| Charts | TradingView Lightweight Charts + Recharts |
| Monitoring | Prometheus + Grafana + LangSmith |

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Neeravneeo/Project-3.git
cd Project-3
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys:
# - ALPACA_API_KEY + ALPACA_SECRET_KEY (from alpaca.markets)
# - GEMINI_API_KEY (from aistudio.google.com)
# - LANGCHAIN_API_KEY (from smith.langchain.com) — optional
```

### 3. Start all services
```bash
docker-compose up -d
```

### 4. Access the platform
| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| Grafana | http://localhost:3001 |
| Flower (Celery) | http://localhost:5555 |
| Prometheus | http://localhost:9090 |

---

## 📁 Project Structure

```
Project-3/
├── docs/                          # All 6 planning documents
│   ├── 1_PRD.md
│   ├── 2_TRD.md
│   ├── 3_APP_FLOW.md
│   ├── 4_UI_UX_BRIEF.md
│   ├── 5_BACKEND_SCHEMA.md
│   └── 6_IMPLEMENTATION_PLAN.md
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── core/                  # Config, DB, Redis, auth
│   │   ├── api/v1/                # API route handlers
│   │   ├── domains/               # Business logic modules
│   │   │   ├── market_data/
│   │   │   ├── strategies/        # EMA, RSI, Mean Reversion
│   │   │   ├── ai_agents/         # LangGraph agents
│   │   │   ├── risk/              # VaR, beta, drawdown
│   │   │   ├── hedge/             # Auto-hedging engine
│   │   │   ├── orders/
│   │   │   └── portfolio/
│   │   ├── brokers/               # BaseBroker, Alpaca, Paper
│   │   └── models/                # SQLAlchemy ORM models
│   ├── workers/                   # Celery tasks
│   ├── backtesting/               # vectorbt + Backtrader
│   ├── migrations/                # Alembic + init.sql
│   ├── tests/
│   └── pyproject.toml
├── frontend/                      # Next.js 14 app
├── monitoring/                    # Prometheus + Grafana configs
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚠️ Important Notes

> **Paper Trading Only by Default** — The platform runs in paper trading mode. No real money is used until you explicitly set `ALPACA_PAPER=false` and accept the risks.

> **Never commit `.env`** — Your `.env` file contains real API keys. It is in `.gitignore`. Only `.env.example` is committed.

> **alpaca-py only** — Use `alpaca-py` (the 2025 official SDK). The old `alpaca-trade-api-python` is deprecated.

---

## 🤝 Build Workflow

This project is built collaboratively by:
- **Antigravity** (AI coding assistant) — complex logic, AI/ML, architecture
- **Jules** (Google async coding agent) — boilerplate, CRUD, tests, scaffolding

See [docs/6_IMPLEMENTATION_PLAN.md](docs/6_IMPLEMENTATION_PLAN.md) for the full task breakdown.

---

## 📄 License

MIT License — see LICENSE file.
