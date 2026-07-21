# 🤖 Jules Task Board
# TradeAI — AI Investment Intelligence Platform

> **Jules** handles all boilerplate, CRUD, schemas, tests, and scaffolding via GitHub Issues.
> **Antigravity** handles complex logic, AI/ML, and architecture interactively.
> Each phase must be **fully complete** before starting the next.

---

## 📌 Status Legend

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[!]` | Blocked — waiting on Antigravity |

---

## ✅ Already Done (Antigravity — Commit `e010a2f`)

| File | Description |
|---|---|
| `backend/app/main.py` | FastAPI app with lifespan, CORS, Prometheus |
| `backend/app/core/config.py` | pydantic-settings configuration |
| `backend/app/core/database.py` | asyncpg + SQLAlchemy 2.0 async |
| `backend/pyproject.toml` | All Python dependencies (uv-managed) |
| `backend/Dockerfile` | Python 3.12 + uv |
| `docker-compose.yml` | Full stack: TimescaleDB, Redis, Celery, Grafana, Prometheus |
| `.env.example` | All environment variables documented |
| `.gitignore` | Secrets protected |
| `README.md` | Quick start guide |
| `docs/1_PRD.md` | Product Requirements Document |
| `docs/2_TRD.md` | Technical Requirements Document |
| `docs/3_APP_FLOW.md` | Complete App Flow |
| `docs/4_UI_UX_BRIEF.md` | UI/UX Design System |
| `docs/5_BACKEND_SCHEMA.md` | Full database schema (12 tables + Redis keys) |
| `docs/6_IMPLEMENTATION_PLAN.md` | Phase-by-phase build plan |

---

## 🚀 Phase 1A — Infrastructure & Foundation

> **Goal:** Full Docker stack running, database connected, API skeleton live

### Issue 1 — `[1A]` Create TimescaleDB SQL init migration
- [ ] File: `backend/migrations/init.sql`
- [ ] Enable `timescaledb` and `uuid-ossp` extensions
- [ ] Create all 12 tables from `docs/5_BACKEND_SCHEMA.md`:
  - `users`, `user_settings`, `portfolios`, `positions`, `orders`
  - `strategies`, `signals`, `market_bars` (hypertable)
  - `risk_snapshots`, `hedge_events`, `news_items`, `audit_log`
- [ ] All indexes from schema doc
- [ ] Continuous aggregate for `market_bars_daily`
- **Reference:** `docs/5_BACKEND_SCHEMA.md`

---

### Issue 2 — `[1A]` Setup Alembic migrations
- [ ] Initialize Alembic in `backend/migrations/`
- [ ] Configure `alembic.ini` to use `DATABASE_URL` from environment
- [ ] Create `env.py` with SQLAlchemy async support
- [ ] Create initial migration matching `docs/5_BACKEND_SCHEMA.md`
- [ ] Add migration run command to `Dockerfile`
- **Reference:** `docs/2_TRD.md` Section 3

---

### Issue 3 — `[1A]` Create SQLAlchemy ORM models
- [ ] Create `backend/app/models/` directory
- [ ] `user.py` — `User`, `UserSettings` models
- [ ] `portfolio.py` — `Portfolio` model
- [ ] `position.py` — `Position` model
- [ ] `order.py` — `Order` model
- [ ] `strategy.py` — `Strategy` model
- [ ] `signal.py` — `Signal` model
- [ ] `risk.py` — `RiskSnapshot` model
- [ ] `hedge.py` — `HedgeEvent` model
- [ ] `news.py` — `NewsItem` model
- [ ] `audit.py` — `AuditLog` model
- SQLAlchemy 2.0 declarative style, async, all UUIDs with `uuid_generate_v4()` server default, all timestamps `TIMESTAMPTZ`
- **Reference:** `docs/5_BACKEND_SCHEMA.md`

---

### Issue 4 — `[1A]` Create Pydantic v2 request/response schemas
- [ ] Create `backend/app/schemas/` directory
- [ ] `user.py` — `UserCreate`, `UserResponse`, `UserUpdate`
- [ ] `portfolio.py` — `PortfolioResponse`, `PortfolioSummary`
- [ ] `position.py` — `PositionResponse`
- [ ] `order.py` — `OrderCreate`, `OrderResponse`
- [ ] `strategy.py` — `StrategyResponse`, `StrategyUpdate` (with JSONB parameters)
- [ ] `signal.py` — `SignalResponse`
- [ ] `risk.py` — `RiskMetricsResponse`
- [ ] `hedge.py` — `HedgeStatusResponse`, `HedgeEventResponse`
- [ ] `auth.py` — `LoginRequest`, `TokenResponse`
- [ ] `common.py` — `PaginatedResponse`, `ErrorResponse`
- Use `model_config = ConfigDict(from_attributes=True)` (Pydantic v2)
- **Reference:** `docs/5_BACKEND_SCHEMA.md` + `docs/3_APP_FLOW.md`

---

### Issue 5 — `[1A]` Create Prometheus monitoring config
- [ ] Create `monitoring/prometheus.yml`
  - Scrape backend API `/metrics` endpoint
  - Scrape interval: 15s
  - Alerting rules for: API down, high latency
- [ ] Create `monitoring/grafana/dashboards/trading.json`
  - TimescaleDB data source import
  - Panels: API latency, active connections, signal generation rate, order count
- **Reference:** `docs/2_TRD.md` Section 8

---

### Issue 6 — `[1A]` Scaffold Next.js frontend
- [ ] Initialize Next.js 14 App Router in `frontend/` directory (TypeScript, Tailwind, shadcn/ui)
- [ ] Install: `zustand`, `@tanstack/react-query`, `recharts`, `lightweight-charts`, `react-countup`, `clsx`
- [ ] Create folder structure:
  ```
  frontend/src/
    app/
      layout.tsx        (Inter + JetBrains Mono fonts)
      page.tsx          (redirect to /dashboard)
      login/page.tsx
      register/page.tsx
      dashboard/page.tsx
      strategies/page.tsx
      risk/page.tsx
      insights/page.tsx
      orders/page.tsx
      settings/page.tsx
    components/
      layout/
        Sidebar.tsx
        TopBar.tsx
        PageWrapper.tsx
      ui/               (shadcn components)
    lib/
      api.ts            (axios/fetch client with JWT header)
      utils.ts
    store/
      authStore.ts      (Zustand: user, token, login, logout)
      portfolioStore.ts (Zustand: portfolio value, positions)
      websocketStore.ts (Zustand: connection state)
    hooks/
      useWebSocket.ts
      usePortfolio.ts
  ```
- [ ] Create `globals.css` with all CSS variables from design system
- Apply full design system from `docs/4_UI_UX_BRIEF.md` (dark theme, colors, typography)
- **Reference:** `docs/4_UI_UX_BRIEF.md` + `docs/3_APP_FLOW.md`

---

### Issue 7 — `[1A]` Create frontend Dockerfile
- [ ] `frontend/Dockerfile` (multi-stage, `node:20-alpine`)
- [ ] Install deps with `npm ci`, build with `next build`, run on port 3000
- [ ] Create `frontend/package.json` with all required dependencies
- **Reference:** Issue 6 dependency list

---

### ✅ Phase 1A Complete When:
- [ ] `docker-compose up` starts all services without error
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `POST /api/v1/auth/register` creates a user
- [ ] `POST /api/v1/auth/login` returns a JWT token
- [ ] Frontend loads at `http://localhost:3000`
- [ ] Database tables are created

---

## 🔄 Phase 1B — Data Ingestion & Strategy Engine

> **Goal:** Market data flowing, 3 strategies generating signals, paper broker executing

### Issue 8 — `[1B]` Create market data API endpoints
- [ ] Create `backend/app/api/v1/market_data.py`
- [ ] `GET /api/v1/market/quote/{symbol}` → latest price from Redis cache
- [ ] `GET /api/v1/market/bars/{symbol}?timeframe=1d&limit=200` → OHLCV from TimescaleDB
- [ ] `GET /api/v1/market/watchlist` → prices for user's watchlist
- [ ] `GET /api/v1/market/search?q={query}` → ticker symbol search
- **Reference:** `docs/3_APP_FLOW.md` + `docs/2_TRD.md`

---

### Issue 9 — `[1B]` Create strategies & signals API endpoints
- [ ] Create `backend/app/api/v1/strategies.py`
  - `GET /api/v1/strategies`
  - `PUT /api/v1/strategies/{id}`
  - `GET /api/v1/strategies/{id}/performance`
- [ ] Create `backend/app/api/v1/signals.py`
  - `GET /api/v1/signals`
  - `GET /api/v1/signals/history`
  - `GET /api/v1/signals/{id}`
- **Reference:** `docs/3_APP_FLOW.md` Section 4

---

### Issue 10 — `[1B]` Create portfolio & orders API endpoints
- [ ] Create `backend/app/api/v1/portfolio.py`
  - `GET /api/v1/portfolio`
  - `GET /api/v1/portfolio/positions`
  - `GET /api/v1/portfolio/performance`
- [ ] Create `backend/app/api/v1/orders.py`
  - `GET /api/v1/orders`
  - `POST /api/v1/orders`
  - `DELETE /api/v1/orders/{id}`
- **Reference:** `docs/3_APP_FLOW.md` Sections 3 + 7

---

### Issue 11 — `[1B]` Create Celery worker and scheduled tasks
- [ ] Create `backend/workers/celery_app.py`
  - Redis broker
  - Beat schedule: `refresh_market_data` (60s), `generate_signals` (5min), `monitor_risk` (60s), `daily_report` (18:00 UTC)
- [ ] Create `backend/workers/tasks/data_refresh.py`
  - Task: `fetch_ohlcv_bars(symbols)` → yfinance → TimescaleDB → Redis
- [ ] Create `backend/workers/tasks/reports.py`
  - Task: `generate_daily_report(portfolio_id)` → risk_snapshots table
- **Reference:** `docs/2_TRD.md` Section 6

---

### ✅ Phase 1B Complete When:
- [ ] `GET /api/v1/market/quote/AAPL` returns live price
- [ ] `GET /api/v1/signals` returns signals with confidence scores
- [ ] Paper trade placed via `POST /api/v1/orders`
- [ ] Position visible in `GET /api/v1/portfolio/positions`
- [ ] Strategy View page shows signals with explanations

---

## 🛡️ Phase 1C — Risk Engine & Auto-Hedging

> **Goal:** Risk metrics computed, hedge engine monitoring and triggering automatically

### Issue 12 — `[1C]` Create risk & hedge API endpoints
- [x] Create `backend/app/api/v1/risk.py`
  - [x] `GET /api/v1/risk/metrics` → VaR, CVaR, beta, drawdown, Sharpe, Sortino
  - [x] `GET /api/v1/risk/exposure` → sector + asset exposure
  - [x] `PUT /api/v1/risk/thresholds` → update user risk thresholds
- [x] Create `backend/app/api/v1/hedge.py`
  - [x] `GET /api/v1/hedge/status`
  - [x] `GET /api/v1/hedge/history`
  - [x] `POST /api/v1/hedge/trigger`
- **Reference:** `docs/3_APP_FLOW.md` Section 5

---

### Issue 13 — `[1C]` Write unit tests for risk engine
- [x] Create `backend/tests/test_risk_metrics.py`
- [x] `test_sharpe_ratio`
- [x] `test_sortino_ratio`
- [x] `test_max_drawdown` — verify `-0.05` on known data
- [x] `test_portfolio_beta` — verify `beta=1.0` when portfolio = SPY
- [x] `test_var_historical` — 95% VaR
- [x] `test_cvar` — expected shortfall
- [x] `test_calmar_ratio`
- Use `pytest` + sample pandas Series. Mock yfinance calls.
- **Reference:** `docs/5_BACKEND_SCHEMA.md` + `docs/2_TRD.md`

---

### ✅ Phase 1C Complete When:
- [x] `GET /api/v1/risk/metrics` returns all risk metrics
- [x] Hedge engine detects VIX > threshold (simulated)
- [x] Hedge recommendation generated with explanation
- [x] Risk Dashboard page displays all metrics

---

## 🧠 Phase 1D — AI Intelligence Layer

> **Goal:** LangGraph agents running, FinBERT scoring news, Gemini generating summaries

### Issue 14 — `[1D]` Create AI insights API endpoints
- [ ] Create `backend/app/api/v1/ai_insights.py`
  - `GET /api/v1/insights/summary` → Gemini market summary (cached 1hr)
  - `GET /api/v1/insights/news` → news feed with FinBERT scores
  - `GET /api/v1/insights/sentiment` → aggregated sentiment per ticker (24h)
  - `GET /api/v1/insights/regime` → market regime classification
  - `GET /api/v1/insights/observations` → Gemini portfolio observations
- **Reference:** `docs/3_APP_FLOW.md` Section 6

---

### Issue 15 — `[1D]` Create news ingestion background task
- [ ] Create `backend/workers/tasks/news.py`
  - Task: `fetch_news_headlines()` → Yahoo Finance RSS (feedparser) → `news_items` table
  - Task: `score_news_sentiment(news_item_id)` → FinBERT → update `sentiment_label`, `sentiment_score`, Redis cache
- Schedule: every 15 minutes during market hours
- **Reference:** `docs/2_TRD.md` Section 6

---

### Issue 16 — `[1D]` Build AI Insights frontend page
- [ ] Create `frontend/src/app/insights/page.tsx`
- [ ] Market Regime Banner (pill badge: BULL / BEAR / HIGH_VOL / SIDEWAYS)
- [ ] Daily Market Summary card (Gemini text + refresh button)
- [ ] Portfolio Observations card (Gemini bullet points)
- [ ] News Feed table (Source | Headline | Sentiment badge | Score | Time) + filter tabs
- [ ] Sentiment Trend chart (Recharts line chart per ticker)
- [ ] Skeleton loaders for all sections
- Use TanStack Query. Follow design system exactly.
- **Reference:** `docs/3_APP_FLOW.md` Section 6 + `docs/4_UI_UX_BRIEF.md`

---

### ✅ Phase 1D Complete When:
- [ ] `GET /api/v1/insights/summary` returns Gemini-generated text
- [ ] News headlines have FinBERT sentiment scores in DB
- [ ] Market regime detected correctly
- [ ] AI Insights page displays all 5 sections

---

## 🖥️ Phase 1E — Frontend Build-Out

> **Goal:** All 4 main pages complete, real-time WebSocket connected, full UX

### Issue 17 — `[1E]` Build Portfolio Dashboard page
- [ ] Create `frontend/src/app/dashboard/page.tsx`
- [ ] Summary cards row (4 cards): Portfolio Value, Daily P&L, Cash Available, Risk Score gauge
- [ ] Hedge Status Banner (conditional, red background)
- [ ] Positions Table (expandable rows, Close Position modal, empty state)
- [ ] Open Orders Panel
- [ ] Portfolio Value Line Chart (Recharts AreaChart, tabs: 1D / 1W / 1M / 3M / 1Y)
- [ ] WebSocket real-time price flashing
- [ ] Skeleton loaders for all sections
- **Reference:** `docs/3_APP_FLOW.md` Section 3 + `docs/4_UI_UX_BRIEF.md`

---

### Issue 18 — `[1E]` Build Strategy View page
- [ ] Create `frontend/src/app/strategies/page.tsx`
- [ ] Strategy Cards Grid (toggle switch, status badge, win rate stats, expandable param sliders)
- [ ] Signal Feed panel (Symbol | Strategy | Signal badge | Confidence bar | Time)
- [ ] Signal Detail Drawer (slides from right: factors breakdown, Gemini explanation, "Paper Trade This" button)
- **Reference:** `docs/3_APP_FLOW.md` Section 4 + `docs/4_UI_UX_BRIEF.md`

---

### Issue 19 — `[1E]` Build Risk Dashboard page
- [ ] Create `frontend/src/app/risk/page.tsx`
- [ ] Risk Metrics Row (5 cards): Portfolio Beta, VaR 95%, Max Drawdown, Sharpe Ratio, Hedge Effectiveness
- [ ] Exposure Charts side-by-side: Recharts PieChart (sector donut) + BarChart (top 10 positions)
- [ ] Correlation Matrix (SVG/CSS heatmap, red → blue)
- [ ] Hedge Engine Panel (editable thresholds, status badge, manual trigger + confirm modal)
- [ ] Hedge Event Log table
- **Reference:** `docs/3_APP_FLOW.md` Section 5 + `docs/4_UI_UX_BRIEF.md`

---

### Issue 20 — `[1E]` Build Sidebar, TopBar & auth pages
- [ ] Create `frontend/src/components/layout/Sidebar.tsx`
  - Collapsible: 240px expanded / 64px collapsed
  - Nav items: Dashboard, Strategies, Risk, AI Insights, Orders
  - Bottom: Settings, User avatar
  - Active state: left accent border
- [ ] Create `frontend/src/components/layout/TopBar.tsx`
  - Breadcrumb, WebSocket live indicator, notification bell
- [ ] Create `frontend/src/components/ui/ToastNotifications.tsx`
  - Green / Yellow / Red variants, auto-dismiss 5s
- [ ] Create `frontend/src/app/login/page.tsx` (JWT → localStorage, redirect on success)
- [ ] Create `frontend/src/app/register/page.tsx`
- **Reference:** `docs/3_APP_FLOW.md` + `docs/4_UI_UX_BRIEF.md`

---

### Issue 21 — `[1E]` Write frontend unit tests
- [ ] Create `frontend/src/__tests__/` directory
- [ ] `dashboard.test.tsx` — renders without error, skeleton on load
- [ ] `strategies.test.tsx` — toggle calls API, signal badge colors correct
- [ ] `risk.test.tsx` — gauge renders with correct color at given beta
- [ ] `auth.test.tsx` — login form validation, error state display
- [ ] `websocket.test.ts` — reconnection logic, message parsing
- Use Jest + React Testing Library + MSW (Mock Service Worker)

---

### ✅ Phase 1E Complete When:
- [ ] All 4 pages load with real data
- [ ] Real-time price updates flash in dashboard
- [ ] Strategy can be enabled and generates a signal
- [ ] Paper trade placed from Strategy View
- [ ] Hedge status banner appears when hedge is active

---

## 📊 Phase 1F — Backtesting Module

> **Goal:** Strategies testable against historical data, quantstats reports generated

### Issue 22 — `[1F]` Create backtesting API endpoints
- [x] Create `backend/app/api/v1/backtesting.py`
  - [x] `POST /api/v1/backtest/run` → queue Celery task → return `task_id`
  - [x] `GET /api/v1/backtest/results/{task_id}` → status + results
  - [x] `GET /api/v1/backtest/reports/{task_id}` → quantstats HTML report URL
- **Reference:** `docs/2_TRD.md` Section 6

---

### ✅ Phase 1F Complete When:
- [ ] Backtest runs EMA Crossover on AAPL for 1 year
- [ ] quantstats HTML report generated (Sharpe, MDD, returns)
- [x] Results accessible via API

---

## 🗺️ Quick Reference: Jules vs Antigravity

| Phase | Jules Issues | Antigravity Tasks |
|---|---|---|
| 1A | Issues 1–7 | `security.py`, `redis_client.py`, `logging.py`, `auth.py`, `websocket.py` |
| 1B | Issues 8–11 | strategies, brokers, signal aggregator |
| 1C | Issues 12–13 | risk engine, hedge engine |
| 1D | Issues 14–16 | LangGraph agents, AI layer |
| 1E | Issues 17–21 | WebSocket hub, settings page |
| 1F | Issue 22 | `vectorbt_runner.py`, `backtrader_runner.py`, Celery backtesting task |

---

## 📎 Master Prompt for Jules (prepend to every issue)

> "Read the following documents before starting:
> - `docs/1_PRD.md` — what we're building
> - `docs/2_TRD.md` — the full tech stack
> - `docs/3_APP_FLOW.md` — how users interact with each page
> - `docs/4_UI_UX_BRIEF.md` — exactly how the UI must look
> - `docs/5_BACKEND_SCHEMA.md` — all database tables and fields
> - `docs/6_IMPLEMENTATION_PLAN.md` — build order and context
>
> Do not guess. If something is unclear, reference these docs.
> Use Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2,
> `alpaca-py` (NOT `alpaca-trade-api-python`), Next.js 14 App Router,
> TypeScript, Tailwind CSS, shadcn/ui, Zustand, TanStack Query."

---

*Last updated: 2026-07-03 | Repo: [Neeravneeo/Project-3](https://github.com/Neeravneeo/Project-3)*
