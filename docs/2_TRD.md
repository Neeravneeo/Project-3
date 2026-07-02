# 🛠️ Technical Requirements Document (TRD)
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved

---

## 1. Architecture Overview

**Pattern:** Modular Monolith (v1) — clean domain boundaries, each module extractable to microservice in Phase 2.

**Data Flow:**
```
Market Data (yfinance / Alpaca WebSocket)
    │
    ▼ Hot Path (Redis) — latest ticks, indicators
    │ Cold Path (TimescaleDB) — historical OHLCV bars
    ▼
LangGraph Multi-Agent Intelligence Layer
    │ Technical Analyst Agent (pandas-ta)
    │ Sentiment Agent (FinBERT + Gemini)
    │ Risk Agent (VaR, beta, drawdown)
    ▼
Coordinator Agent → Signal Aggregation
    ▼
Risk Engine (pre-trade checks)  ←→  Hedge Engine (VIX / drawdown triggers)
    ▼
HUMAN-IN-THE-LOOP CHECKPOINT (live trading only)
    ▼
Execution Engine (alpaca-py paper=True/False)
    ▼
Portfolio Manager → PostgreSQL (positions, orders, P&L)
    ▼
WebSocket Fan-out → Next.js Frontend (real-time)
```

---

## 2. Frontend Stack

| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 14+ (App Router) | React framework, SSR, routing |
| **TypeScript** | 5.x | Type safety (non-negotiable for financial apps) |
| **TradingView Lightweight Charts** | 4.x | OHLC candlestick charts (Canvas-based, high performance) |
| **Recharts** | 2.x | Portfolio analytics charts (SVG) |
| **shadcn/ui** | latest | Accessible component library |
| **Tailwind CSS** | 3.x | Utility-first styling |
| **Zustand** | 4.x | Client state (granular subscriptions for real-time WebSocket) |
| **TanStack Query** | 5.x | Server state, REST API data fetching |
| **WebSocket (native)** | — | Real-time price and portfolio updates |

**Frontend pages:**
1. `/` — Portfolio Dashboard
2. `/strategies` — Strategy View
3. `/risk` — Risk Dashboard
4. `/insights` — AI Insights
5. `/orders` — Order History
6. `/settings` — User Settings

---

## 3. Backend Stack

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.12 | Core language |
| **FastAPI** | 0.115+ | Async REST API + WebSocket server |
| **Uvicorn** | 0.32+ | ASGI server |
| **uv** | latest | Package manager (replaces pip/poetry) |
| **Celery** | 5.4+ | Background task queue (NOT for order execution) |
| **Pydantic v2** | 2.10+ | Data validation at all module boundaries |
| **SQLAlchemy** | 2.0+ | Async ORM |
| **Alembic** | 1.14+ | Database migrations |
| **asyncpg** | 0.30+ | Raw async PostgreSQL driver |
| **ruff** | 0.8+ | Linting |
| **pyright** | 1.1.390+ | Type checking |

---

## 4. Database

### Primary: PostgreSQL 16 + TimescaleDB extension

**Two data paths:**
- **Hot Path (Redis):** Latest tick prices, current indicator values, active signals → sub-millisecond reads
- **Cold Path (TimescaleDB):** Historical OHLCV bars as hypertables, trade history, P&L logs

**Key tables:**
- `users` — authentication
- `portfolios` — portfolio metadata
- `positions` — open positions
- `orders` — order history
- `signals` — generated signals per strategy per symbol
- `market_bars` — OHLCV hypertable (TimescaleDB)
- `risk_snapshots` — daily risk metrics snapshots
- `hedge_events` — hedge trigger log
- `audit_log` — every significant action

### Cache: Redis 7
- Latest quotes: `price:{symbol}` (TTL: 60s)
- Latest signals: `signal:{symbol}` (TTL: 5min)
- Portfolio beta cache: `portfolio:beta` (TTL: 5min)
- WebSocket pub/sub channel: `realtime:updates`
- Celery broker: DB 1
- Celery results: DB 2

---

## 5. Authentication

- **Method:** JWT (JSON Web Tokens)
- **Library:** `python-jose` + `passlib[bcrypt]`
- **Token expiry:** 24 hours (configurable)
- **Flow:**
  1. `POST /api/v1/auth/login` → returns `access_token`
  2. All protected routes require `Authorization: Bearer <token>` header
  3. FastAPI `Depends(get_current_user)` validates token on every request
- **Password:** bcrypt hashed, never stored in plaintext
- **Future:** OAuth2 (Google) for Phase 2

---

## 6. APIs & Integrations

### Market Data
| Source | Library | Usage |
|---|---|---|
| yfinance | `yfinance` | Historical OHLCV (dev / backtesting) |
| Alpaca | `alpaca-py` | Live US market data (paper + live) |
| Yahoo Finance RSS | `feedparser` | News headlines for sentiment |

### Broker
| Broker | Library | Notes |
|---|---|---|
| Alpaca | `alpaca-py` 0.36+ | US equities, `paper=True` for paper trading |
| Zerodha Kite | `kiteconnect` | Indian markets — Phase 2 |

**Critical Alpaca notes:**
- Use `alpaca-py` NOT deprecated `alpaca-trade-api-python`
- Paper WebSocket: `wss://stream.data.sandbox.alpaca.markets/v2/iex`
- Implement manual exponential-backoff reconnection — do not trust auto-reconnect
- Never route order execution through Celery — keep in asyncio event loop

### AI / LLM
| Tool | Library | Purpose |
|---|---|---|
| Google Gemini 2.0 Flash | `langchain-google-genai` | Market summaries, explanations, trade narration |
| OpenAI GPT-4o | `langchain-openai` | Fallback LLM |
| LangGraph | `langgraph` | Multi-agent stateful workflow orchestration |
| LangChain | `langchain` | Tool use, prompt templates, LLM abstraction |
| LangSmith | `langsmith` | Agent monitoring, trace debugging |
| FinBERT | `transformers` (`ProsusAI/finbert`) | News sentiment scoring |
| VADER | `vaderSentiment` | Fast fallback sentiment (< 1ms vs FinBERT ~100ms) |

### Portfolio Optimization
| Tool | Library | Purpose |
|---|---|---|
| PyPortfolioOpt | `PyPortfolioOpt` | MVO, HRP, Black-Litterman weight allocation |
| Riskfolio-Lib | `Riskfolio-Lib` | CVaR, Expected Shortfall optimization |
| quantstats | `quantstats` | HTML tear sheets, Sharpe, MDD, Calmar |

### Backtesting
| Tool | Library | Purpose |
|---|---|---|
| vectorbt | `vectorbt` | Fast vectorized parameter sweeps |
| Backtrader | `backtrader` | Realistic event-driven fill simulation |

---

## 7. Real-time Architecture

```
Alpaca WebSocket Feed
    │
    ▼ (asyncio coroutine — never blocking)
Redis Pub/Sub (channel: realtime:prices)
    │
    ├─► Strategy signal recalculation (in-process)
    ├─► Risk monitoring update (in-process)
    └─► FastAPI WebSocket → broadcast to connected clients
```

**WebSocket endpoint:** `ws://localhost:8000/ws`
**Message format:**
```json
{
  "type": "price_update | signal | portfolio_update | hedge_alert | risk_alert",
  "data": { ... },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

---

## 8. Observability

| Tool | Purpose |
|---|---|
| Prometheus | Metrics collection (`prometheus-fastapi-instrumentator`) |
| Grafana | Dashboards — connects to both Prometheus and TimescaleDB |
| Flower | Celery task monitoring UI |
| LangSmith | LangGraph agent trace monitoring |
| Structured JSON logging | All backend logs in JSON format (Uvicorn + custom) |

**Custom Prometheus metrics:**
- `trading_signal_latency_seconds` — time to generate signal
- `trading_order_latency_seconds` — time from signal to order
- `trading_hedge_trigger_total` — hedge activation count
- `trading_active_positions` — current open positions

---

## 9. Security Requirements

- ❌ **NEVER** hardcode API keys in source code
- ✅ All secrets from `.env` file (local) or HashiCorp Vault (production)
- ✅ Principle of Least Privilege — broker keys: trade-only, no withdrawal
- ✅ All API keys masked in logs
- ✅ HTTPS only in production (Let's Encrypt)
- ✅ Rate limiting on auth endpoints
- ✅ Audit log for every order, hedge, and login event
- ✅ `.env` in `.gitignore` — only `.env.example` committed

---

## 10. Performance Requirements

| Requirement | Target |
|---|---|
| API response time (p95) | < 200ms |
| Signal generation (per symbol) | < 5 seconds |
| WebSocket price update latency | < 500ms |
| Dashboard initial load | < 3 seconds |
| Database query (OHLCV 1yr) | < 500ms (TimescaleDB hypertable) |
| Redis cache read | < 5ms |

---

## 11. Deployment (v1)

- **Platform:** Docker Compose on local machine / single cloud VM
- **Services:** api, frontend, db (TimescaleDB), redis, celery-worker, celery-beat, flower, prometheus, grafana
- **Environment:** `.env` file with all secrets
- **Commands:**
  ```bash
  docker-compose up -d          # start all services
  docker-compose logs -f api    # watch logs
  docker-compose down           # stop
  ```
- **Future (Phase 2):** AWS EC2 / GCP VM → Kubernetes (Phase 3)
