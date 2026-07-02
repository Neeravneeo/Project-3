# 📋 Product Requirements Document (PRD)
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved

---

## 1. App Overview

| Field | Details |
|---|---|
| **App Name** | TradeAI — AI Investment Intelligence Platform |
| **One-line Idea** | An AI-powered platform that auto-trades and auto-hedges your portfolio using real-time market signals, news sentiment, and explainable AI recommendations |
| **Target Users** | Retail investors, swing traders, portfolio managers, quantitative analysts |
| **Problem Solved** | Manual trading is emotional, slow, and unprotected. Most tools either trade OR hedge — not both together intelligently |

---

## 2. Problem Statement

Retail and semi-professional investors face three core problems:

1. **Emotional trading** — buying high, selling low due to fear/greed
2. **No automated downside protection** — positions bleed during market stress with no auto-hedge
3. **Information overload** — too many signals, news, and data points with no unified AI to synthesize them

**TradeAI solves all three** by combining automated signal generation, portfolio risk monitoring, and auto-hedging into a single explainable AI system.

---

## 3. Target Users

### Retail Investor
- Has $5,000–$100,000 to invest
- Wants automation but limited time for research
- Needs: auto-trading + downside protection

### Swing Trader
- Holds positions 2–14 days
- Uses technical analysis
- Needs: multi-signal AI + volatility-triggered hedging

### Portfolio Manager
- Manages $100K+ portfolios
- Needs: exposure monitoring + automated hedge adjustments + risk reports

### Quantitative Analyst
- Wants to test strategies without touching execution code
- Needs: modular strategy engine + backtesting

---

## 4. Core Features (MVP)

### 4.1 AI Intelligence Layer
- News ingestion + FinBERT sentiment scoring per ticker
- Market regime detection (Bull / Bear / High Volatility / Sideways)
- Daily AI market summary (Gemini LLM)
- Portfolio observations and commentary

### 4.2 Strategy Engine
- **EMA Crossover** (20/50 EMA + ADX filter)
- **RSI Momentum** (RSI + Rate of Change)
- **Mean Reversion** (Bollinger Bands + Z-score)
- Each strategy: generates BUY / SELL / HOLD signals with confidence score (0–1)
- Signal aggregator: combines signals into unified recommendation

### 4.3 Auto-Hedging Engine
- Continuous portfolio risk monitoring
- Hedge triggers: VIX level, portfolio drawdown, portfolio beta, single-position loss
- Dynamic hedge sizing (proportional to stress level, not binary on/off)
- Hedge instruments: SH, SDS, PSQ (inverse ETFs)
- Full explainability: why hedge triggered, expected risk reduction

### 4.4 Execution Engine
- **Paper trading** (default, always safe — simulated fills)
- **Live trading** via Alpaca (US markets, gated feature, requires explicit opt-in)
- Human-in-the-loop approval checkpoint before any live order
- Order lifecycle: place, modify, cancel, track

### 4.5 Portfolio Manager
- Real-time position tracking
- Realized + unrealized P&L
- Sector and asset exposure breakdown
- Portfolio beta vs SPY
- Cash allocation

### 4.6 Risk Dashboard
- VaR (95%, historical simulation)
- CVaR / Expected Shortfall
- Max drawdown (rolling)
- Portfolio beta
- Sharpe ratio, Sortino ratio, Calmar ratio
- Position concentration limits

### 4.7 Analytics Dashboard
- Portfolio value chart (sparkline + full history)
- Strategy performance (win rate, avg return, Sharpe per strategy)
- Backtesting results (vectorbt + Backtrader)
- quantstats HTML tear sheets

---

## 5. User Stories

| As a... | I want to... | So that... |
|---|---|---|
| Retail investor | See my portfolio value and P&L in real-time | I know my financial position at all times |
| Retail investor | Have the system automatically hedge when market drops | I don't lose sleep over sudden crashes |
| Swing trader | See AI signals with confidence scores and explanations | I understand why a trade is recommended |
| Swing trader | Enable/disable individual strategies | I can tune the system to my style |
| Portfolio manager | View exposure by sector and asset | I can manage concentration risk |
| Portfolio manager | Get alerts when risk thresholds are breached | I can intervene before losses compound |
| Quant analyst | Add a new strategy without touching execution code | I can iterate strategies safely |
| Risk manager | See every trade and hedge pass through risk validation | No unvalidated order ever executes |

---

## 6. User Roles

| Role | Permissions |
|---|---|
| **Admin** | Full access, manage users, configure system |
| **Trader** | View signals, execute trades, manage portfolio |
| **Analyst** | View-only: signals, risk, AI insights |
| **Paper Trader** | Full access but paper mode only (no live trading) |

---

## 7. Success Metrics (MVP)

| Metric | Target |
|---|---|
| Signal generation latency | < 5 seconds after market data update |
| Dashboard real-time update | < 1 second WebSocket delay |
| Hedge trigger response | < 10 seconds from trigger detection to order |
| Paper trade fill accuracy | Within 0.5% of last price |
| Uptime | 99.5% during market hours |

---

## 8. MVP Scope

**Included in v1:**
- Single user (personal use)
- US equities via Alpaca (paper trading)
- 3 strategies (EMA Crossover, RSI Momentum, Mean Reversion)
- Auto-hedging with inverse ETFs (SH, SDS, PSQ)
- AI insights (Gemini + FinBERT)
- 4 frontend pages (Dashboard, Strategy View, Risk Dashboard, AI Insights)
- Docker Compose deployment (local machine)

**NOT included in v1:**
- Indian markets (Zerodha Kite) — Phase 2
- Live trading — gated, Phase 2
- Options-based hedging — Phase 2
- Multi-user / team features — Phase 3
- Mobile app — Phase 3
- Backtesting laboratory UI — Phase 2
- Strategy marketplace — Phase 3
