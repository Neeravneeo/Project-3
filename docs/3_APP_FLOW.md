# 🗺️ App Flow Document
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved

---

## 1. All Pages / Screens

| # | Page | Route | Auth Required |
|---|---|---|---|
| 1 | Login | `/login` | No |
| 2 | Register | `/register` | No |
| 3 | Portfolio Dashboard | `/` | Yes |
| 4 | Strategy View | `/strategies` | Yes |
| 5 | Risk Dashboard | `/risk` | Yes |
| 6 | AI Insights | `/insights` | Yes |
| 7 | Order History | `/orders` | Yes |
| 8 | Settings | `/settings` | Yes |

---

## 2. Auth Flow

```
User visits app
      │
      ▼
No JWT in localStorage?
      │
  Yes │                    No
      ▼                    ▼
 /login page         Load dashboard
      │
 Enter email + password
      │
 POST /api/v1/auth/login
      │
 ┌────┴────┐
 │ Success │──► Store JWT → redirect to /
 └────┬────┘
      │ Fail
      ▼
 Show error toast
 "Invalid credentials"
```

### Login Page
- **Fields:** Email, Password
- **Actions:**
  - Submit → `POST /api/v1/auth/login`
  - "Don't have account?" → `/register`
- **Success:** Store JWT in localStorage → redirect to `/`
- **Error:** Toast "Invalid email or password"
- **Empty state:** None (always shows form)

### Register Page
- **Fields:** Full Name, Email, Password, Confirm Password
- **Actions:**
  - Submit → `POST /api/v1/auth/register`
  - "Already have account?" → `/login`
- **Success:** Auto-login → redirect to `/`
- **Error states:**
  - Passwords don't match → inline error
  - Email already exists → toast error
  - Weak password → inline error (min 8 chars)

---

## 3. Portfolio Dashboard (`/`)

### On Load
```
Component mounts
      │
      ├─► GET /api/v1/portfolio          → portfolio summary
      ├─► GET /api/v1/portfolio/positions → positions table
      ├─► GET /api/v1/risk/metrics        → risk score
      ├─► GET /api/v1/hedge/status        → hedge status
      └─► WebSocket connect ws://…/ws    → real-time prices
```

### Layout (top to bottom)
1. **Top Nav:** Logo | Dashboard | Strategies | Risk | Insights | Orders | [Avatar → Settings / Logout]
2. **Summary Cards Row:**
   - Portfolio Value (+ sparkline 7d)
   - Daily P&L (absolute + %)
   - Cash Available
   - Risk Score (0–100 gauge)
3. **Hedge Status Banner** (only visible when hedge is active):
   - 🔴 "Hedge Active — SH position open. Beta reduced from 1.2 → 0.3"
   - Button: "View Details"
4. **Positions Table:**
   - Columns: Symbol | Shares | Avg Cost | Current Price | P&L $ | P&L % | Weight | Strategy | Actions
   - Actions per row: "Close Position" button
   - Empty state: "No open positions. Enable a strategy to start trading."
5. **Open Orders Panel:**
   - Columns: Symbol | Side | Qty | Type | Status | Time
   - Empty state: "No open orders"
6. **Portfolio Chart:**
   - Line chart of portfolio value over time (1D / 1W / 1M / 3M / 1Y)
   - Toggle: Paper / Live mode indicator

### User Actions
| Action | Trigger | Behavior |
|---|---|---|
| Click position row | Click | Expand: show strategy signals, entry reason |
| Close position | Button | Confirm modal → `DELETE /api/v1/orders` → refresh |
| Switch time range | Tab buttons | Fetch new chart data |
| Real-time price update | WebSocket | Cells flash green/red on change, P&L recalculates |
| Logout | Avatar menu | Clear JWT → redirect `/login` |

### Error States
- API down → "Unable to load portfolio. Retrying…" with spinner
- No positions → illustrated empty state with CTA "Go to Strategies"

---

## 4. Strategy View (`/strategies`)

### On Load
```
GET /api/v1/strategies       → list of all strategies + enabled status
GET /api/v1/signals          → latest signals per symbol per strategy
GET /api/v1/market/watchlist → prices for watched symbols
```

### Layout
1. **Strategy Cards Grid** (one card per strategy):
   - Strategy name + description
   - Toggle switch: Enabled / Disabled
   - Status badge: Active / Paused / No Signal
   - Stats: Win Rate | Avg Return | Sharpe
   - Expand button → show parameters

2. **Signal Feed** (right panel or below cards):
   - Real-time list of latest signals
   - Columns: Symbol | Strategy | Signal (BUY/SELL/HOLD) | Confidence | Time | Reason
   - Confidence shown as color-coded badge (green > 0.7, yellow 0.4–0.7, red < 0.4)
   - Click signal row → Signal Detail Drawer

3. **Signal Detail Drawer** (slides in from right):
   - Symbol + current price
   - Signal direction + confidence score (0–100%)
   - Contributing factors breakdown:
     - Technical score: 72%
     - Sentiment score: 65%
     - Regime alignment: Bull ✅
   - AI explanation (Gemini-generated paragraph)
   - Action buttons: "Paper Trade This" | "Dismiss"

4. **Parameter Panel** (expands per strategy card):
   - Sliders for configurable params (e.g., EMA fast period: 5–50)
   - Reset to defaults button
   - Save button → `PUT /api/v1/strategies/{id}`

### User Actions
| Action | Trigger | Behavior |
|---|---|---|
| Toggle strategy | Switch | `PUT /api/v1/strategies/{id}` → toast "EMA Crossover enabled" |
| Adjust parameter | Slider | Local state → Save button appears |
| Save parameters | Button | `PUT /api/v1/strategies/{id}` → recalculate signals |
| Paper trade signal | Button | `POST /api/v1/orders` with paper=true → toast confirmation |
| Click signal row | Click | Open Signal Detail Drawer |

### Error States
- Strategy engine down → "Signal generation paused. Check system status."
- No signals yet → "Generating signals… This may take up to 60 seconds on first run."

---

## 5. Risk Dashboard (`/risk`)

### On Load
```
GET /api/v1/risk/metrics     → VaR, beta, drawdown, Sharpe, Sortino
GET /api/v1/risk/exposure    → sector + asset breakdown
GET /api/v1/hedge/status     → current hedge state
GET /api/v1/hedge/history    → hedge event log
```

### Layout
1. **Risk Metrics Row** (5 cards):
   - Portfolio Beta (gauge: 0–2, red > 0.9)
   - VaR 95% (1-day $ amount)
   - Max Drawdown (% from peak)
   - Sharpe Ratio
   - Hedge Effectiveness (% risk reduction from active hedges)

2. **Exposure Charts** (side by side):
   - Donut chart: Sector exposure (Tech / Finance / Healthcare / etc.)
   - Bar chart: Top 10 position weights

3. **Correlation Matrix:**
   - Heatmap of position correlations
   - Color: dark red (highly correlated) → dark blue (inversely correlated)

4. **Risk Heatmap:**
   - Grid of symbols × risk factors
   - Color intensity = risk contribution

5. **Hedge Engine Panel:**
   - Current trigger thresholds (editable)
   - Hedge status: Monitoring / Triggered / Active
   - Last hedge event: time, reason, instrument, size
   - Button: "Manually Trigger Hedge Analysis"

6. **Hedge Event Log:**
   - Table: Time | Trigger | Instrument | Shares | Cost | Beta Before | Beta After

### User Actions
| Action | Trigger | Behavior |
|---|---|---|
| Edit threshold | Input field | `PUT /api/v1/risk/thresholds` |
| Manual hedge trigger | Button | Confirm modal → `POST /api/v1/hedge/trigger` |
| View hedge detail | Click row | Expand: show full Gemini explanation |

---

## 6. AI Insights (`/insights`)

### On Load
```
GET /api/v1/insights/summary    → Gemini market summary
GET /api/v1/insights/news       → news feed + FinBERT sentiment
GET /api/v1/insights/sentiment  → aggregated sentiment per ticker
GET /api/v1/insights/regime     → current market regime
```

### Layout
1. **Market Regime Banner** (top):
   - Large pill badge: 🟢 BULL TRENDING | 🔴 BEAR TRENDING | 🟡 HIGH VOLATILITY | ⚪ SIDEWAYS
   - Sub-text: "SPY above 50-day MA | VIX: 18.4 (Normal)"

2. **Daily Market Summary** (Gemini-generated):
   - Card with AI-written paragraph
   - Timestamp: "Generated at 09:35 AM"
   - Refresh button

3. **Portfolio Observations** (Gemini-generated):
   - Bulleted AI commentary on user's specific portfolio
   - e.g., "Your AAPL position is up 12% — consider taking partial profits per mean reversion signal"

4. **News Feed + Sentiment:**
   - List of latest news headlines (last 24h)
   - Per headline: Source | Headline | Sentiment badge (🟢 Positive / 🔴 Negative / ⚪ Neutral) | Score | Time
   - Filter tabs: All | Positive | Negative | Watchlist only

5. **Sentiment Trend Chart:**
   - Line chart: aggregate sentiment score per ticker (last 7 days)
   - Toggle between tickers in watchlist

6. **Macro Events Calendar:**
   - Upcoming events: Fed meeting, CPI release, earnings dates
   - Color-coded by expected market impact

### Error States
- Gemini API unavailable → "AI summary unavailable. Showing cached version from [time]"
- No news → "No news found for your watchlist in the last 24 hours"

---

## 7. Order History (`/orders`)

### Layout
- Filter bar: All / Paper / Live | Buy / Sell | Date range
- Table: Time | Symbol | Side | Qty | Price | Total | Strategy | Status | Type
- Status badges: Filled (green) / Pending (yellow) / Cancelled (grey) / Failed (red)
- Empty state: "No orders yet. Enable a strategy or place a manual order."
- Export button: Download CSV

---

## 8. Settings (`/settings`)

### Sections
1. **Profile:** Name, email, change password
2. **Broker Connection:** Alpaca API key + secret (masked), test connection button, paper/live toggle
3. **Risk Thresholds:** Max drawdown %, VIX hedge level, max position weight — all configurable sliders
4. **Notification Preferences:** Toggle: Trade executed / Hedge activated / Risk threshold exceeded / Strategy disabled
5. **Active Strategies:** Quick enable/disable grid (same as Strategy View)
6. **Danger Zone:** Delete account | Reset all data

---

## 9. Navigation Flow

```
/login ──────────────────────────────────────────── /register
   │                                                      │
   └──────────────────┬───────────────────────────────────┘
                      │ (authenticated)
                      ▼
              / (Dashboard)
              │
   ┌──────────┼──────────┬──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼          ▼          ▼
/strategies /risk   /insights  /orders  /settings  [logout → /login]
```

---

## 10. Global UI Behaviors

### Toast Notifications (top-right)
| Event | Toast |
|---|---|
| Trade executed | 🟢 "AAPL BUY 10 shares filled @ $185.20" |
| Hedge activated | 🔴 "Hedge activated — SH position opened (VIX > 25)" |
| Strategy disabled | 🟡 "EMA Crossover disabled — insufficient signals" |
| Risk threshold exceeded | 🔴 "Portfolio beta exceeded 0.9 limit" |
| Market anomaly | 🔴 "Unusual volume detected in NVDA" |
| API error | 🔴 "Connection lost. Reconnecting…" |

### WebSocket Behavior
- Auto-reconnect with exponential backoff on disconnect
- Show "● Live" green indicator in top nav when connected
- Show "● Reconnecting…" yellow indicator when disconnected
- Price cells flash green (price up) or red (price down) on update

### Loading States
- All data sections show skeleton loaders (not spinners)
- Charts show shimmer placeholders while loading

### Responsive Behavior
- Desktop (> 1280px): Full multi-column layout
- Tablet (768–1280px): Collapsible sidebar, stacked cards
- Mobile (< 768px): Bottom nav, single column, simplified charts
