# 🗄️ Backend Schema Document
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved

---

## 1. Database Overview

- **Engine:** PostgreSQL 16 + TimescaleDB extension
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Naming convention:** `snake_case` for all tables and columns
- **Primary keys:** UUID v4 (all tables except hypertables)
- **Timestamps:** `created_at`, `updated_at` on all tables (UTC, TIMESTAMPTZ)

---

## 2. TimescaleDB Setup

```sql
-- Run once after DB creation
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

## 3. Tables

---

### 3.1 `users`
Stores authenticated user accounts.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'trader',
    -- role: 'admin' | 'trader' | 'analyst' | 'paper_trader'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

---

### 3.2 `user_settings`
Per-user configurable risk thresholds and preferences.

```sql
CREATE TABLE user_settings (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- Broker
    alpaca_api_key_encrypted     TEXT,
    alpaca_secret_key_encrypted  TEXT,
    alpaca_paper_mode            BOOLEAN NOT NULL DEFAULT TRUE,
    -- Risk thresholds
    max_drawdown_trigger        NUMERIC(5,4) NOT NULL DEFAULT 0.05,
    max_position_beta           NUMERIC(4,2) NOT NULL DEFAULT 0.90,
    single_position_loss        NUMERIC(5,4) NOT NULL DEFAULT 0.03,
    vix_caution_level           NUMERIC(5,2) NOT NULL DEFAULT 20.0,
    vix_hedge_level             NUMERIC(5,2) NOT NULL DEFAULT 25.0,
    vix_aggressive_level        NUMERIC(5,2) NOT NULL DEFAULT 30.0,
    max_position_weight         NUMERIC(5,4) NOT NULL DEFAULT 0.10,
    -- Notifications
    notify_trade_executed       BOOLEAN NOT NULL DEFAULT TRUE,
    notify_hedge_activated      BOOLEAN NOT NULL DEFAULT TRUE,
    notify_risk_threshold       BOOLEAN NOT NULL DEFAULT TRUE,
    notify_strategy_disabled    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);
```

---

### 3.3 `portfolios`
Top-level portfolio container per user.

```sql
CREATE TABLE portfolios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL DEFAULT 'My Portfolio',
    broker          VARCHAR(50) NOT NULL DEFAULT 'paper',
    -- broker: 'paper' | 'alpaca' | 'zerodha'
    currency        VARCHAR(10) NOT NULL DEFAULT 'USD',
    initial_capital NUMERIC(18,2) NOT NULL DEFAULT 100000.00,
    cash_balance    NUMERIC(18,2) NOT NULL DEFAULT 100000.00,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
```

---

### 3.4 `positions`
Currently open positions in a portfolio.

```sql
CREATE TABLE positions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,
    exchange        VARCHAR(20) NOT NULL DEFAULT 'NASDAQ',
    side            VARCHAR(10) NOT NULL DEFAULT 'long',
    -- side: 'long' | 'short'
    quantity        NUMERIC(18,6) NOT NULL,
    avg_cost        NUMERIC(18,6) NOT NULL,
    current_price   NUMERIC(18,6),
    unrealized_pnl  NUMERIC(18,2),
    realized_pnl    NUMERIC(18,2) NOT NULL DEFAULT 0,
    strategy        VARCHAR(100),
    -- strategy that opened this position
    is_hedge        BOOLEAN NOT NULL DEFAULT FALSE,
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_positions_portfolio_id ON positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
```

---

### 3.5 `orders`
Full order history (paper + live).

```sql
CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    broker_order_id VARCHAR(255),
    -- ID returned by broker (Alpaca order ID, Kite order ID, etc.)
    symbol          VARCHAR(20) NOT NULL,
    side            VARCHAR(10) NOT NULL,
    -- side: 'buy' | 'sell'
    order_type      VARCHAR(20) NOT NULL DEFAULT 'market',
    -- order_type: 'market' | 'limit' | 'stop' | 'stop_limit'
    quantity        NUMERIC(18,6) NOT NULL,
    limit_price     NUMERIC(18,6),
    stop_price      NUMERIC(18,6),
    filled_price    NUMERIC(18,6),
    filled_qty      NUMERIC(18,6),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- status: 'pending' | 'filled' | 'partial' | 'cancelled' | 'failed'
    strategy        VARCHAR(100),
    signal_id       UUID REFERENCES signals(id),
    is_paper        BOOLEAN NOT NULL DEFAULT TRUE,
    is_hedge        BOOLEAN NOT NULL DEFAULT FALSE,
    reason          TEXT,
    -- human-readable reason (AI-generated)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_portfolio_id ON orders(portfolio_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

---

### 3.6 `strategies`
Strategy definitions and per-user configuration.

```sql
CREATE TABLE strategies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    -- name: 'ema_crossover' | 'rsi_momentum' | 'mean_reversion'
    display_name    VARCHAR(100) NOT NULL,
    description     TEXT,
    is_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
    parameters      JSONB NOT NULL DEFAULT '{}',
    -- e.g.: {"fast_period": 20, "slow_period": 50, "adx_threshold": 25}
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, name)
);

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
```

**Default parameters per strategy:**
```json
// EMA Crossover
{"fast_period": 20, "slow_period": 50, "adx_threshold": 25, "timeframe": "1d"}

// RSI Momentum
{"rsi_period": 14, "oversold": 30, "overbought": 70, "roc_period": 12, "timeframe": "1d"}

// Mean Reversion
{"bb_period": 20, "bb_std": 2.0, "z_score_threshold": 2.0, "adx_max": 20, "timeframe": "1d"}
```

---

### 3.7 `signals`
Generated trading signals from each strategy.

```sql
CREATE TABLE signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id     UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,
    direction       VARCHAR(10) NOT NULL,
    -- direction: 'buy' | 'sell' | 'hold'
    confidence      NUMERIC(5,4) NOT NULL,
    -- 0.0000 to 1.0000
    technical_score NUMERIC(5,4),
    sentiment_score NUMERIC(5,4),
    regime_aligned  BOOLEAN,
    explanation     TEXT,
    -- Gemini-generated explanation
    raw_indicators  JSONB,
    -- snapshot of all indicator values at signal time
    -- e.g.: {"ema_20": 185.5, "ema_50": 180.2, "adx": 28.3, "rsi": 55}
    time_horizon    VARCHAR(50),
    -- 'short' | 'medium' | 'long'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signals_user_id ON signals(user_id);
CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_signals_direction ON signals(direction);
```

---

### 3.8 `market_bars` (TimescaleDB Hypertable)
OHLCV price data — the hot/cold path backbone.

```sql
CREATE TABLE market_bars (
    time        TIMESTAMPTZ NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    exchange    VARCHAR(20) NOT NULL DEFAULT 'NASDAQ',
    timeframe   VARCHAR(10) NOT NULL DEFAULT '1d',
    -- timeframe: '1m' | '5m' | '15m' | '1h' | '1d'
    open        NUMERIC(18,6) NOT NULL,
    high        NUMERIC(18,6) NOT NULL,
    low         NUMERIC(18,6) NOT NULL,
    close       NUMERIC(18,6) NOT NULL,
    volume      BIGINT NOT NULL DEFAULT 0,
    vwap        NUMERIC(18,6),
    num_trades  INTEGER
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('market_bars', 'time');

-- Indexes for common query patterns
CREATE INDEX idx_market_bars_symbol_time ON market_bars(symbol, time DESC);
CREATE INDEX idx_market_bars_timeframe ON market_bars(timeframe, symbol, time DESC);

-- Continuous aggregate: pre-compute daily bars from 1m bars
CREATE MATERIALIZED VIEW market_bars_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    symbol,
    FIRST(open, time)  AS open,
    MAX(high)          AS high,
    MIN(low)           AS low,
    LAST(close, time)  AS close,
    SUM(volume)        AS volume
FROM market_bars
WHERE timeframe = '1m'
GROUP BY bucket, symbol;
```

---

### 3.9 `risk_snapshots`
Daily snapshot of portfolio risk metrics.

```sql
CREATE TABLE risk_snapshots (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id        UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    snapshot_date       DATE NOT NULL,
    portfolio_value     NUMERIC(18,2),
    cash_balance        NUMERIC(18,2),
    portfolio_beta      NUMERIC(6,4),
    var_95              NUMERIC(18,2),
    -- Value at Risk (95%, 1-day, in $)
    cvar_95             NUMERIC(18,2),
    -- Conditional VaR / Expected Shortfall
    max_drawdown        NUMERIC(6,4),
    -- e.g. -0.0523 = -5.23%
    sharpe_ratio        NUMERIC(6,4),
    sortino_ratio       NUMERIC(6,4),
    calmar_ratio        NUMERIC(6,4),
    risk_score          INTEGER,
    -- 0–100 composite risk score
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(portfolio_id, snapshot_date)
);

CREATE INDEX idx_risk_portfolio_date ON risk_snapshots(portfolio_id, snapshot_date DESC);
```

---

### 3.10 `hedge_events`
Log of every hedge trigger and action.

```sql
CREATE TABLE hedge_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id        UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    trigger_type        VARCHAR(50) NOT NULL,
    -- 'vix_threshold' | 'drawdown' | 'beta_exceeded' | 'position_loss' | 'manual'
    trigger_value       NUMERIC(10,4),
    -- the value that caused the trigger (e.g. VIX = 26.4)
    trigger_threshold   NUMERIC(10,4),
    -- the configured threshold
    portfolio_beta_before   NUMERIC(6,4),
    portfolio_beta_after    NUMERIC(6,4),
    hedge_instrument    VARCHAR(20),
    -- 'SH' | 'SDS' | 'PSQ'
    hedge_quantity      NUMERIC(18,6),
    hedge_cost          NUMERIC(18,2),
    estimated_risk_reduction NUMERIC(5,4),
    explanation         TEXT,
    -- Gemini-generated explanation
    order_id            UUID REFERENCES orders(id),
    status              VARCHAR(20) NOT NULL DEFAULT 'triggered',
    -- 'triggered' | 'executed' | 'rejected' | 'expired'
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hedge_portfolio ON hedge_events(portfolio_id, created_at DESC);
```

---

### 3.11 `news_items`
Cached news headlines with sentiment scores.

```sql
CREATE TABLE news_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    headline        TEXT NOT NULL,
    source          VARCHAR(100),
    url             TEXT,
    symbols         TEXT[],
    -- array of ticker symbols mentioned
    published_at    TIMESTAMPTZ,
    sentiment_label VARCHAR(20),
    -- 'positive' | 'negative' | 'neutral'
    sentiment_score NUMERIC(5,4),
    -- FinBERT confidence score
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_published ON news_items(published_at DESC);
CREATE INDEX idx_news_symbols ON news_items USING GIN(symbols);
```

---

### 3.12 `audit_log`
Immutable log of all significant system actions.

```sql
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    -- 'order_placed' | 'hedge_triggered' | 'strategy_enabled' | 'login' | etc.
    entity_type VARCHAR(50),
    entity_id   UUID,
    details     JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_action ON audit_log(action, created_at DESC);
```

---

## 4. Relationships Summary

```
users
  ├── user_settings (1:1)
  ├── portfolios (1:many)
  │     ├── positions (1:many)
  │     ├── orders (1:many)
  │     ├── risk_snapshots (1:many)
  │     └── hedge_events (1:many)
  └── strategies (1:many)
        └── signals (1:many)
              └── orders (signal_id FK, optional)

market_bars (hypertable, independent — no FK)
news_items (independent — no FK)
audit_log (user_id FK, optional)
```

---

## 5. Redis Key Schema

```
# Hot price cache (TTL: 60 seconds)
price:{SYMBOL}                → {"price": 185.20, "change": 1.2, "ts": "..."}

# Latest signal per symbol per strategy (TTL: 5 minutes)
signal:{SYMBOL}:{STRATEGY}    → {"direction": "buy", "confidence": 0.82, "ts": "..."}

# Portfolio cache (TTL: 30 seconds)
portfolio:{PORTFOLIO_ID}      → {"value": 124850, "beta": 0.72, "ts": "..."}

# WebSocket pub/sub channels
realtime:prices               → price update fan-out
realtime:signals              → new signal fan-out
realtime:alerts               → hedge/risk alert fan-out

# Celery queues (DB 1)
default                       → general tasks
signals                       → signal generation tasks
reports                       → report generation tasks
```

---

## 6. Data Ownership & Permissions

| Table | Owner | Read | Write |
|---|---|---|---|
| users | admin | self | self (profile) / admin |
| user_settings | user | self | self |
| portfolios | user | self | self |
| positions | user | self | system (auto) |
| orders | user | self | self + system |
| strategies | user | self | self |
| signals | system | user | system only |
| market_bars | system | all | system only |
| risk_snapshots | system | user | system only |
| hedge_events | system | user | system only |
| news_items | system | all | system only |
| audit_log | system | admin + self | system only |
