# 🚀 Implementation Plan
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved — Ready for Jules + Antigravity

---

## How to Read This Plan

- **Antigravity (AG)** = Complex logic, AI/ML, architecture — built interactively
- **Jules (J)** = Boilerplate, CRUD, schemas, tests, scaffolding — built via GitHub Issues
- **Both** = Coordinated work
- Each phase must be **fully complete before starting the next**
- All code goes into `https://github.com/Neeravneeo/Project-3`

---

## Phase 1A — Infrastructure & Foundation
> **Goal:** Full Docker stack running, database connected, API skeleton live

### Jules Tasks (create these as GitHub Issues)

#### Issue 1: Create TimescaleDB SQL init migration
```
Title: [1A] Create TimescaleDB SQL init migration

Create backend/migrations/init.sql with:
- Enable TimescaleDB and uuid-ossp extensions
- Create all tables from docs/5_BACKEND_SCHEMA.md:
  users, user_settings, portfolios, positions, orders,
  strategies, signals, market_bars (hypertable),
  risk_snapshots, hedge_events, news_items, audit_log
- All indexes from schema doc
- Continuous aggregate for market_bars_daily

Reference: docs/5_BACKEND_SCHEMA.md
```

#### Issue 2: Create Alembic migrations setup
```
Title: [1A] Setup Alembic migrations

- Initialize Alembic in backend/migrations/
- Configure alembic.ini to use DATABASE_URL from environment
- Create env.py with SQLAlchemy async support
- Create initial migration matching docs/5_BACKEND_SCHEMA.md
- Add migration run command to Dockerfile

Reference: docs/2_TRD.md Section 3
```

#### Issue 3: Create all SQLAlchemy ORM models
```
Title: [1A] Create SQLAlchemy ORM models

Create backend/app/models/ directory with these files:
- user.py — User, UserSettings models
- portfolio.py — Portfolio model
- position.py — Position model
- order.py — Order model
- strategy.py — Strategy model
- signal.py — Signal model
- risk.py — RiskSnapshot model
- hedge.py — HedgeEvent model
- news.py — NewsItem model
- audit.py — AuditLog model

Use SQLAlchemy 2.0 declarative style with async support.
Import Base from app.core.database.
All UUIDs use uuid_generate_v4() server default.
All timestamps are TIMESTAMPTZ.

Reference: docs/5_BACKEND_SCHEMA.md
```

#### Issue 4: Create all Pydantic schemas
```
Title: [1A] Create Pydantic v2 request/response schemas

Create backend/app/schemas/ directory with:
- user.py — UserCreate, UserResponse, UserUpdate
- portfolio.py — PortfolioResponse, PortfolioSummary
- position.py — PositionResponse
- order.py — OrderCreate, OrderResponse
- strategy.py — StrategyResponse, StrategyUpdate (with parameters JSONB)
- signal.py — SignalResponse
- risk.py — RiskMetricsResponse
- hedge.py — HedgeStatusResponse, HedgeEventResponse
- auth.py — LoginRequest, TokenResponse
- common.py — PaginatedResponse, ErrorResponse

Use Pydantic v2 model_config = ConfigDict(from_attributes=True)

Reference: docs/5_BACKEND_SCHEMA.md + docs/3_APP_FLOW.md
```

#### Issue 5: Create Prometheus monitoring config
```
Title: [1A] Create monitoring configuration

1. Create monitoring/prometheus.yml:
   - Scrape backend API /metrics endpoint
   - Scrape interval: 15s
   - Add alerting rules for: API down, high latency

2. Create monitoring/grafana/dashboards/trading.json:
   - Import TimescaleDB data source
   - Dashboard panels: API latency, active connections,
     signal generation rate, order count

Reference: docs/2_TRD.md Section 8
```

#### Issue 6: Create frontend Next.js scaffold
```
Title: [1A] Scaffold Next.js frontend

Initialize Next.js 14 app in frontend/ directory:
- next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components (init)
- Install: zustand, @tanstack/react-query, recharts,
  lightweight-charts, react-countup, clsx

Create folder structure:
frontend/src/
  app/
    layout.tsx        (root layout with Inter + JetBrains Mono fonts)
    page.tsx          (redirect to /dashboard)
    login/page.tsx    (login page shell)
    register/page.tsx (register page shell)
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

Apply design system from docs/4_UI_UX_BRIEF.md:
- Colors, typography, dark theme
- Create globals.css with all CSS variables

Reference: docs/4_UI_UX_BRIEF.md + docs/3_APP_FLOW.md
```

#### Issue 7: Create frontend Dockerfile
```
Title: [1A] Create frontend Dockerfile

Create frontend/Dockerfile:
- FROM node:20-alpine
- Install dependencies with npm ci
- Build with next build
- Run with next start on port 3000
- Multi-stage build for smaller image

Create frontend/package.json with all dependencies listed above.
```

### Antigravity Builds (already in progress)
- ✅ `backend/app/main.py` — FastAPI app with lifespan
- ✅ `backend/app/core/config.py` — pydantic-settings
- ✅ `backend/app/core/database.py` — asyncpg + SQLAlchemy
- ✅ `backend/pyproject.toml` — all dependencies
- ✅ `backend/Dockerfile`
- ✅ `docker-compose.yml`
- ✅ `.env.example`
- [ ] `backend/app/core/security.py` — JWT + bcrypt
- [ ] `backend/app/core/redis_client.py` — Redis connection
- [ ] `backend/app/core/logging.py` — structured JSON logging
- [ ] `backend/app/api/v1/auth.py` — login + register endpoints
- [ ] `backend/app/api/v1/websocket.py` — WebSocket hub

### ✅ Phase 1A Complete When:
- `docker-compose up` starts all services without error
- `GET /health` returns `{"status": "healthy"}`
- `POST /api/v1/auth/register` creates a user
- `POST /api/v1/auth/login` returns a JWT token
- Frontend loads at `http://localhost:3000`
- Database tables are created

---

## Phase 1B — Data Ingestion & Strategy Engine
> **Goal:** Market data flowing, 3 strategies generating signals, paper broker executing

### Jules Tasks

#### Issue 8: Create market data API router
```
Title: [1B] Create market data API endpoints

Create backend/app/api/v1/market_data.py:
- GET /api/v1/market/quote/{symbol}
  → return latest price from Redis cache
- GET /api/v1/market/bars/{symbol}?timeframe=1d&limit=200
  → return OHLCV bars from TimescaleDB
- GET /api/v1/market/watchlist
  → return prices for user's watchlist symbols
- GET /api/v1/market/search?q={query}
  → search for ticker symbols

Reference: docs/3_APP_FLOW.md + docs/2_TRD.md
```

#### Issue 9: Create strategies API router
```
Title: [1B] Create strategies API endpoints

Create backend/app/api/v1/strategies.py:
- GET /api/v1/strategies → list all strategies for user
- PUT /api/v1/strategies/{id} → update strategy (enable/disable/params)
- GET /api/v1/strategies/{id}/performance → win rate, Sharpe, avg return

Create backend/app/api/v1/signals.py:
- GET /api/v1/signals → latest signals (all symbols, all strategies)
- GET /api/v1/signals/history → paginated signal history
- GET /api/v1/signals/{id} → single signal with full explanation

Reference: docs/3_APP_FLOW.md Section 4
```

#### Issue 10: Create portfolio & orders API routers
```
Title: [1B] Create portfolio and orders API endpoints

backend/app/api/v1/portfolio.py:
- GET /api/v1/portfolio → portfolio summary (value, P&L, cash, beta)
- GET /api/v1/portfolio/positions → all open positions
- GET /api/v1/portfolio/performance → historical P&L chart data

backend/app/api/v1/orders.py:
- GET /api/v1/orders → paginated order history
- POST /api/v1/orders → place a manual paper order
- DELETE /api/v1/orders/{id} → cancel pending order

Reference: docs/3_APP_FLOW.md Sections 3 + 7
```

#### Issue 11: Create Celery worker setup
```
Title: [1B] Create Celery worker and scheduled tasks

Create backend/workers/celery_app.py:
- Configure Celery with Redis broker
- Define beat schedule:
  * refresh_market_data: every 60 seconds (market hours only)
  * generate_signals: every 5 minutes
  * monitor_risk: every 60 seconds
  * daily_report: daily at 18:00 UTC

Create backend/workers/tasks/data_refresh.py:
- Task: fetch_ohlcv_bars(symbols: list[str])
  → fetch from yfinance → insert into TimescaleDB
  → update Redis hot cache

Create backend/workers/tasks/reports.py:
- Task: generate_daily_report(portfolio_id: str)
  → compute risk snapshot → save to risk_snapshots table

Reference: docs/2_TRD.md Section 6
```

### Antigravity Builds
- [ ] `backend/app/domains/market_data/services.py` — hot/cold data path logic
- [ ] `backend/app/domains/strategies/base_strategy.py` — abstract BaseStrategy
- [ ] `backend/app/domains/strategies/ema_crossover.py` — EMA 20/50 + ADX
- [ ] `backend/app/domains/strategies/rsi_momentum.py` — RSI + ROC
- [ ] `backend/app/domains/strategies/mean_reversion.py` — Bollinger + Z-score
- [ ] `backend/app/domains/strategies/signal_aggregator.py` — weighted voting
- [ ] `backend/app/brokers/base.py` — abstract BaseBroker
- [ ] `backend/app/brokers/paper.py` — paper broker with slippage model
- [ ] `backend/app/brokers/alpaca.py` — alpaca-py integration

### ✅ Phase 1B Complete When:
- `GET /api/v1/market/quote/AAPL` returns live price
- `GET /api/v1/signals` returns signals with confidence scores
- A paper trade can be placed via `POST /api/v1/orders`
- Position appears in `GET /api/v1/portfolio/positions`
- Strategy View page shows signals with explanations

---

## Phase 1C — Risk Engine & Auto-Hedging
> **Goal:** Risk metrics computed, hedge engine monitoring and triggering automatically

### Jules Tasks

#### Issue 12: Create risk API router
```
Title: [1C] Create risk API endpoints

Create backend/app/api/v1/risk.py:
- GET /api/v1/risk/metrics → VaR, CVaR, beta, drawdown, Sharpe, Sortino
- GET /api/v1/risk/exposure → sector + asset exposure breakdown
- PUT /api/v1/risk/thresholds → update user's risk thresholds

Create backend/app/api/v1/hedge.py:
- GET /api/v1/hedge/status → current hedge state + active hedge positions
- GET /api/v1/hedge/history → paginated hedge event log
- POST /api/v1/hedge/trigger → manually trigger hedge analysis

Reference: docs/3_APP_FLOW.md Section 5
```

#### Issue 13: Create unit tests for risk metrics
```
Title: [1C] Write unit tests for risk engine

Create backend/tests/test_risk_metrics.py:
Test all functions in app/domains/risk/metrics.py:
- test_sharpe_ratio: known inputs → expected output
- test_sortino_ratio
- test_max_drawdown: verify -0.05 on known data
- test_portfolio_beta: verify beta=1.0 when portfolio = SPY
- test_var_historical: verify 95% VaR calculation
- test_cvar: verify expected shortfall
- test_calmar_ratio

Use pytest with sample pandas Series data.
Mock yfinance calls.

Reference: docs/5_BACKEND_SCHEMA.md + docs/2_TRD.md
```

### Antigravity Builds
- [ ] `backend/app/domains/risk/metrics.py` — VaR, CVaR, beta, Sharpe, Sortino, Calmar, drawdown
- [ ] `backend/app/domains/risk/pre_trade.py` — pre-trade validation checks
- [ ] `backend/app/domains/risk/post_trade.py` — real-time P&L monitoring
- [ ] `backend/app/domains/hedge/trigger.py` — VIX/drawdown/beta trigger logic
- [ ] `backend/app/domains/hedge/recommender.py` — dynamic hedge sizing formula
- [ ] `backend/app/domains/hedge/validator.py` — cost + liquidity validation

### ✅ Phase 1C Complete When:
- `GET /api/v1/risk/metrics` returns all risk metrics
- Hedge engine detects when VIX > threshold (simulated test)
- Hedge recommendation generated with explanation
- Risk Dashboard page displays all metrics correctly

---

## Phase 1D — AI Intelligence Layer
> **Goal:** LangGraph agents running, FinBERT scoring news, Gemini generating summaries

### Jules Tasks

#### Issue 14: Create AI insights API router
```
Title: [1D] Create AI insights API endpoints

Create backend/app/api/v1/ai_insights.py:
- GET /api/v1/insights/summary → Gemini market summary (cached 1hr)
- GET /api/v1/insights/news → news feed with FinBERT sentiment scores
- GET /api/v1/insights/sentiment → aggregated sentiment per ticker (last 24h)
- GET /api/v1/insights/regime → current market regime classification
- GET /api/v1/insights/observations → Gemini portfolio observations

Reference: docs/3_APP_FLOW.md Section 6
```

#### Issue 15: Create news ingestion Celery task
```
Title: [1D] Create news ingestion background task

Create backend/workers/tasks/news.py:
- Task: fetch_news_headlines()
  → Fetch RSS from Yahoo Finance using feedparser
    for each symbol in user watchlists
  → Store raw headlines in news_items table
  → Queue sentiment scoring task

- Task: score_news_sentiment(news_item_id: str)
  → Load headline from DB
  → Run ProsusAI/finbert inference
  → Update sentiment_label + sentiment_score in DB
  → Update Redis: sentiment:{SYMBOL} aggregate

Schedule: every 15 minutes during market hours

Reference: docs/2_TRD.md Section 6
```

#### Issue 16: Create frontend AI Insights page
```
Title: [1D] Build AI Insights frontend page

Create frontend/src/app/insights/page.tsx with:
1. Market Regime Banner (pill badge: BULL/BEAR/HIGH_VOL/SIDEWAYS)
2. Daily Market Summary card (Gemini text + refresh button)
3. Portfolio Observations card (Gemini bullet points)
4. News Feed table:
   - Columns: Source | Headline | Sentiment badge | Score | Time
   - Filter tabs: All | Positive | Negative | Watchlist
   - Sentiment badge: green/red/grey pill
5. Sentiment Trend chart (Recharts line chart per ticker)
6. Skeleton loaders for all sections

Use TanStack Query for data fetching.
Follow design system from docs/4_UI_UX_BRIEF.md exactly.

Reference: docs/3_APP_FLOW.md Section 6 + docs/4_UI_UX_BRIEF.md
```

### Antigravity Builds
- [ ] `backend/app/domains/ai_agents/coordinator.py` — LangGraph coordinator
- [ ] `backend/app/domains/ai_agents/technical_analyst.py` — pandas-ta batch Strategy
- [ ] `backend/app/domains/ai_agents/sentiment_analyst.py` — FinBERT + VADER pipeline
- [ ] `backend/app/domains/ai_agents/risk_agent.py` — VaR + position sizing agent
- [ ] `backend/app/domains/ai_agents/market_regime.py` — regime classifier
- [ ] LangSmith tracing integration

### ✅ Phase 1D Complete When:
- `GET /api/v1/insights/summary` returns Gemini-generated text
- News headlines have FinBERT sentiment scores in DB
- Market regime detected correctly (test with known market dates)
- AI Insights page displays all 5 sections

---

## Phase 1E — Frontend Build-Out
> **Goal:** All 4 main pages complete, real-time WebSocket connected, full UX

### Jules Tasks

#### Issue 17: Build Dashboard page
```
Title: [1E] Build Portfolio Dashboard page

Create frontend/src/app/dashboard/page.tsx with ALL sections from docs/3_APP_FLOW.md Section 3:

1. Summary cards row (4 cards):
   - Portfolio Value (JetBrains Mono, 36px, sparkline)
   - Daily P&L (green/red with arrow)
   - Cash Available
   - Risk Score (arc gauge SVG, 0-100)

2. Hedge Status Banner (conditional — only when hedge active):
   - Red background, left border, instrument + beta info

3. Positions Table:
   - All columns from APP_FLOW.md
   - Row expansion on click
   - "Close Position" button with confirm modal
   - Empty state with CTA

4. Open Orders Panel

5. Portfolio Value Line Chart:
   - Recharts AreaChart
   - Time range tabs: 1D / 1W / 1M / 3M / 1Y

Wire up WebSocket from useWebSocket.ts hook for real-time price flashing.
Use design system from docs/4_UI_UX_BRIEF.md exactly.
Skeleton loaders for all sections.

Reference: docs/3_APP_FLOW.md Section 3 + docs/4_UI_UX_BRIEF.md
```

#### Issue 18: Build Strategy View page
```
Title: [1E] Build Strategy View page

Create frontend/src/app/strategies/page.tsx with ALL sections from docs/3_APP_FLOW.md Section 4:

1. Strategy Cards Grid (one per strategy):
   - Name, description, toggle switch, status badge
   - Win rate, avg return, Sharpe stats
   - Expandable parameter sliders (shadcn Slider)
   - Save button

2. Signal Feed panel:
   - Columns: Symbol | Strategy | Signal badge | Confidence bar | Time
   - Signal Detail Drawer (slides from right)
   - Confidence progress bar (green/yellow/red)

3. Signal Detail Drawer:
   - Symbol, price, signal direction
   - Contributing factors breakdown bars
   - Gemini AI explanation text
   - "Paper Trade This" button

Follow design system docs/4_UI_UX_BRIEF.md exactly.

Reference: docs/3_APP_FLOW.md Section 4 + docs/4_UI_UX_BRIEF.md
```

#### Issue 19: Build Risk Dashboard page
```
Title: [1E] Build Risk Dashboard page

Create frontend/src/app/risk/page.tsx with ALL sections from docs/3_APP_FLOW.md Section 5:

1. Risk Metrics Row (5 cards):
   - Portfolio Beta gauge
   - VaR 95% dollar amount
   - Max Drawdown %
   - Sharpe Ratio
   - Hedge Effectiveness %

2. Exposure Charts side by side:
   - Recharts PieChart: sector exposure donut
   - Recharts BarChart: top 10 position weights

3. Correlation Matrix:
   - SVG/CSS heatmap grid
   - Color: red (correlated) → blue (inverse)

4. Hedge Engine Panel:
   - Editable threshold inputs
   - Status: Monitoring / Triggered / Active
   - Manual trigger button with confirm modal

5. Hedge Event Log table

Reference: docs/3_APP_FLOW.md Section 5 + docs/4_UI_UX_BRIEF.md
```

#### Issue 20: Build Sidebar, TopBar, Notifications
```
Title: [1E] Build Sidebar navigation and global components

Create frontend/src/components/layout/Sidebar.tsx:
- Collapsible: 240px expanded / 64px collapsed
- Nav items: Dashboard, Strategies, Risk, AI Insights, Orders
- Bottom: Settings, User avatar with name
- Active state: left accent border
- Design from docs/4_UI_UX_BRIEF.md Section 9

Create frontend/src/components/layout/TopBar.tsx:
- Breadcrumb navigation
- "● Live" WebSocket status indicator
- Notification bell with count badge

Create frontend/src/components/ui/ToastNotifications.tsx:
- All toast types from docs/3_APP_FLOW.md Section 10
- Green/Yellow/Red variants
- Auto-dismiss after 5 seconds

Create frontend/src/app/login/page.tsx and register/page.tsx:
- Full auth forms with validation
- JWT storage in localStorage
- Redirect on success

Reference: docs/3_APP_FLOW.md + docs/4_UI_UX_BRIEF.md
```

#### Issue 21: Write frontend unit tests
```
Title: [1E] Write frontend unit tests

Create frontend/src/__tests__/:

- dashboard.test.tsx: renders without error, shows skeleton on load
- strategies.test.tsx: toggle switch calls API, signal badge colors
- risk.test.tsx: gauge renders with correct color at given beta value
- auth.test.tsx: login form validation, error state display
- websocket.test.ts: reconnection logic, message parsing

Use Jest + React Testing Library.
Mock API calls with MSW (Mock Service Worker).
```

### Antigravity Builds
- [ ] `backend/app/api/v1/websocket.py` — WebSocket hub with Redis pub/sub fan-out
- [ ] Frontend WebSocket hook — price updates, reconnection logic
- [ ] Settings page — broker key management, threshold configuration

### ✅ Phase 1E Complete When:
- All 4 pages load with real data
- Real-time price updates flash in dashboard
- A strategy can be enabled and generates a signal
- A paper trade can be placed from Strategy View
- Hedge status banner appears when hedge is active

---

## Phase 1F — Backtesting Module
> **Goal:** Strategies testable against historical data, quantstats reports generated

### Jules Tasks

#### Issue 22: Create backtesting API endpoints
```
Title: [1F] Create backtesting API endpoints

Create backend/app/api/v1/backtesting.py:
- POST /api/v1/backtest/run
  Body: {strategy: str, symbol: str, start: date, end: date, capital: float}
  → queue Celery task → return task_id

- GET /api/v1/backtest/results/{task_id}
  → return status + results when complete

- GET /api/v1/backtest/reports/{task_id}
  → return quantstats HTML report URL

Reference: docs/2_TRD.md Section 6 (Backtesting)
```

### Antigravity Builds
- [ ] `backend/backtesting/vectorbt_runner.py` — fast parameter sweeps
- [ ] `backend/backtesting/backtrader_runner.py` — realistic fills
- [ ] `backend/workers/tasks/backtesting.py` — Celery task wrapper

### ✅ Phase 1F Complete When:
- Backtest runs EMA Crossover on AAPL for 1 year
- quantstats HTML report generated with Sharpe, MDD, returns
- Results accessible via API

---

## Final Push to GitHub

After each phase completion:
```bash
git add .
git commit -m "feat: Phase 1X — [description]"
git push origin main
```

Jules picks up new GitHub Issues → creates PRs → you review with Antigravity → merge.

---

## Quick Reference: Who Builds What

| Phase | Jules Issues | Antigravity |
|---|---|---|
| 1A | Issues 1–7 | main.py, config, database, auth, websocket core |
| 1B | Issues 8–11 | strategies, brokers, signal aggregator |
| 1C | Issues 12–13 | risk engine, hedge engine |
| 1D | Issues 14–16 | LangGraph agents, AI layer |
| 1E | Issues 17–21 | WebSocket hub, settings page |
| 1F | Issue 22 | backtesting runners |

---

## Master Prompt for Jules

When giving Jules any issue, prepend this:

> "Read the following documents before starting:
> - docs/1_PRD.md — what we're building
> - docs/2_TRD.md — the full tech stack
> - docs/3_APP_FLOW.md — how users interact with each page
> - docs/4_UI_UX_BRIEF.md — exactly how the UI must look
> - docs/5_BACKEND_SCHEMA.md — all database tables and fields
> - docs/6_IMPLEMENTATION_PLAN.md — build order and context
>
> Do not guess. If something is unclear, reference these docs.
> Use Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2,
> alpaca-py (NOT alpaca-trade-api-python), Next.js 14 App Router,
> TypeScript, Tailwind CSS, shadcn/ui, Zustand, TanStack Query."
