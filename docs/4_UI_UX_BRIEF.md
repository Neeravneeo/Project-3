# 🎨 UI/UX Design Brief
# AI Investment Intelligence Platform
**Version:** 1.0 | **Status:** Approved

---

## 1. Design Style

**Theme:** Dark mode first, professional fintech aesthetic
**Feel:** Premium, data-dense, trustworthy — inspired by Bloomberg Terminal meets modern SaaS (Linear, Vercel dashboard)
**Mood:** Confident, intelligent, calm — NOT flashy or gamified

---

## 2. Color Palette

```css
/* Background layers */
--bg-base:        #0A0B0E;   /* deepest background */
--bg-surface:     #111318;   /* cards, panels */
--bg-elevated:    #1A1D24;   /* modals, dropdowns */
--bg-hover:       #22262F;   /* hover states */

/* Brand accent */
--accent-primary: #3B82F6;   /* electric blue — primary actions */
--accent-hover:   #2563EB;
--accent-glow:    rgba(59, 130, 246, 0.15);

/* Semantic colors */
--green:          #22C55E;   /* profit, buy, positive */
--green-muted:    #16A34A;
--red:            #EF4444;   /* loss, sell, negative, alert */
--red-muted:      #DC2626;
--yellow:         #F59E0B;   /* caution, pending */
--purple:         #A855F7;   /* AI / insight indicators */

/* Text */
--text-primary:   #F1F5F9;   /* main readable text */
--text-secondary: #94A3B8;   /* labels, subtitles */
--text-muted:     #475569;   /* timestamps, disabled */

/* Borders */
--border:         #1E2330;
--border-focus:   #3B82F6;
```

---

## 3. Typography

```css
/* Import from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base font */
font-family: 'Inter', -apple-system, sans-serif;

/* Monospace for numbers/prices */
font-family: 'JetBrains Mono', monospace;  /* ALL price/number displays */

/* Type scale */
--text-xs:   0.75rem;   /* 12px — timestamps, badges */
--text-sm:   0.875rem;  /* 14px — table cells, labels */
--text-base: 1rem;      /* 16px — body text */
--text-lg:   1.125rem;  /* 18px — card titles */
--text-xl:   1.25rem;   /* 20px — section headings */
--text-2xl:  1.5rem;    /* 24px — page headings */
--text-3xl:  1.875rem;  /* 30px — portfolio value */
--text-4xl:  2.25rem;   /* 36px — hero numbers */
```

**Rules:**
- All monetary values → JetBrains Mono, tabular numbers
- Positive P&L → `--green`, negative → `--red`
- Section headings → Inter 600 (SemiBold)
- Body text → Inter 400 (Regular)

---

## 4. Layout Rules

### Global Layout
```
┌──────────────────────────────────────────────────────┐
│  SIDEBAR (64px collapsed / 240px expanded)           │
│  ┌────┐  ┌──────────────────────────────────────┐   │
│  │    │  │  TOP BAR (56px)                      │   │
│  │ S  │  │  Logo | Breadcrumb | Status | Avatar │   │
│  │ I  │  ├──────────────────────────────────────┤   │
│  │ D  │  │                                      │   │
│  │ E  │  │  MAIN CONTENT AREA                   │   │
│  │ B  │  │  (scrollable, 24px padding)           │   │
│  │ A  │  │                                      │   │
│  │ R  │  │                                      │   │
│  └────┘  └──────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Grid System
- Content area: 12-column grid
- Card gap: 16px (desktop), 12px (tablet)
- Page padding: 24px (desktop), 16px (mobile)
- Max content width: 1440px (centered on large screens)

### Card Style
```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  /* Subtle glow on hover */
  transition: border-color 0.2s, box-shadow 0.2s;
}
.card:hover {
  border-color: #2A3040;
  box-shadow: 0 0 0 1px #2A3040;
}
```

---

## 5. Component Style

### Buttons
```css
/* Primary */
.btn-primary {
  background: var(--accent-primary);
  color: white;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 500;
  font-size: 14px;
  transition: background 0.15s, transform 0.1s;
}
.btn-primary:hover  { background: var(--accent-hover); }
.btn-primary:active { transform: scale(0.98); }

/* Danger */
.btn-danger { background: var(--red); }

/* Ghost */
.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
```

### Badges / Status Pills
```css
.badge-buy     { background: rgba(34,197,94,0.15);  color: #22C55E; }
.badge-sell    { background: rgba(239,68,68,0.15);  color: #EF4444; }
.badge-hold    { background: rgba(148,163,184,0.1); color: #94A3B8; }
.badge-active  { background: rgba(59,130,246,0.15); color: #3B82F6; }
.badge-hedge   { background: rgba(239,68,68,0.2);   color: #EF4444; border: 1px solid rgba(239,68,68,0.4); }
.badge-ai      { background: rgba(168,85,247,0.15); color: #A855F7; }
/* All badges: border-radius: 9999px; padding: 2px 10px; font-size: 12px; font-weight: 500; */
```

### Tables
```css
/* Zebra striping on dark bg */
.table-row:nth-child(even) { background: rgba(255,255,255,0.02); }
.table-row:hover           { background: var(--bg-elevated); cursor: pointer; }
/* Positive/negative columns flash animation */
@keyframes flash-green { 0%,100%{background:transparent} 50%{background:rgba(34,197,94,0.2)} }
@keyframes flash-red   { 0%,100%{background:transparent} 50%{background:rgba(239,68,68,0.2)} }
```

### Input Fields
```css
.input {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-glow);
  outline: none;
}
```

### Toggle / Switch
- Uses shadcn/ui Switch component
- Active state: `--accent-primary` track, white thumb
- Disabled: `--text-muted` track

---

## 6. Key Component Designs

### Portfolio Value Card
```
┌─────────────────────────────────────┐
│ Portfolio Value                     │
│ $124,850.00          [sparkline 7d] │
│ ▲ +$1,240 (+1.02%)  today           │
│ ● Paper Trading Mode                │
└─────────────────────────────────────┘
- Value: JetBrains Mono, 36px, --text-primary
- Change: JetBrains Mono, 18px, --green or --red
- Sparkline: 80px wide TradingView chart, no axes
```

### Risk Score Gauge
```
        85 / 100
    ════════════░░░
   LOW        HIGH
```
- Arc gauge using SVG
- Color: green (0–40) → yellow (40–70) → red (70–100)
- Updates in real-time via WebSocket

### Signal Confidence Badge
```
[▲ BUY  ████████░░  82%]  ← EMA Crossover
```
- Direction icon: ▲ green (BUY) / ▼ red (SELL) / — grey (HOLD)
- Progress bar fill = confidence percentage
- Color: green > 70%, yellow 40–70%, red < 40%

### Hedge Status Banner
```
┌──────────────────────────────────────────────────────┐
│ 🔴  HEDGE ACTIVE  │ SH (Short S&P500) │ 48 shares    │
│ Portfolio beta: 1.2 → 0.31  │  VIX triggered: 26.4  │
│                                    [View Details] [✕] │
└──────────────────────────────────────────────────────┘
- Background: rgba(239,68,68,0.08)
- Border: 1px solid rgba(239,68,68,0.3)
- Border-left: 3px solid --red
```

### AI Insight Card
```
┌─────────────────────────────────────────────────────────┐
│ ✦ AI Market Summary              Generated 09:35 AM [↻] │
│─────────────────────────────────────────────────────────│
│ Markets opened cautiously today as investors digested    │
│ mixed jobless claims data. Tech sector shows relative    │
│ strength with NVDA leading gains...                      │
│                                           [Read more]   │
└─────────────────────────────────────────────────────────┘
- ✦ icon in --purple
- Card border-left: 3px solid --purple
```

---

## 7. Micro-Animations

```css
/* Page transition */
.page-enter { animation: fadeSlideUp 0.2s ease-out; }
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Card hover lift */
.card { transition: transform 0.15s, box-shadow 0.15s; }
.card:hover { transform: translateY(-2px); }

/* Number count-up on load */
/* Use react-countup for portfolio value */

/* Price flash on WebSocket update */
.price-up   { animation: flash-green 0.6s ease-out; }
.price-down { animation: flash-red   0.6s ease-out; }

/* Sidebar nav active indicator */
.nav-active::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  width: 3px; height: 20px;
  background: var(--accent-primary);
  border-radius: 0 2px 2px 0;
  transform: translateY(-50%);
}

/* Skeleton loader shimmer */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(90deg, #1A1D24 25%, #22262F 50%, #1A1D24 75%);
  background-size: 400px;
  animation: shimmer 1.4s infinite;
  border-radius: 6px;
}
```

---

## 8. Chart Specifications

### TradingView Lightweight Charts (OHLC)
```js
const chart = createChart(container, {
  layout: {
    background: { color: '#0A0B0E' },
    textColor: '#94A3B8',
  },
  grid: {
    vertLines: { color: '#1E2330' },
    horzLines: { color: '#1E2330' },
  },
  crosshair: { mode: CrosshairMode.Normal },
  rightPriceScale: { borderColor: '#1E2330' },
  timeScale: { borderColor: '#1E2330', timeVisible: true },
});
// Candlestick series: up candles #22C55E, down candles #EF4444
```

### Portfolio Value Line Chart (Recharts)
- Background: transparent
- Line color: `#3B82F6` (accent blue)
- Area fill: `rgba(59,130,246,0.08)`
- Tooltip: dark bg, JetBrains Mono numbers
- No X axis labels on small cards (sparkline mode)

### Exposure Donut Chart
- Segment colors: preset palette per sector
- Center label: "Total Exposure"
- Hover: expand segment + show tooltip

### Correlation Heatmap
- Library: custom SVG grid or recharts `<ScatterChart>`
- Color scale: `#EF4444` (1.0) → `#1A1D24` (0.0) → `#3B82F6` (-1.0)

---

## 9. Sidebar Navigation

```
┌──────────────────┐
│  ⚡ TradeAI      │  ← logo + name (collapsed: icon only)
├──────────────────┤
│  ▦  Dashboard    │
│  ⟰  Strategies  │
│  ⚠  Risk         │
│  ✦  AI Insights  │
│  ≡  Orders       │
├──────────────────┤
│  ⚙  Settings     │
│  [Avatar] Neerav │
└──────────────────┘
```
- Active item: accent left border + slightly brighter text
- Hover: `--bg-hover` background
- Collapsed (64px): icons only, tooltip on hover

---

## 10. Mobile Behavior (< 768px)

- Sidebar → bottom tab bar (5 main items)
- Cards → single column, full width
- Tables → horizontal scroll with sticky first column
- Charts → simplified, touch-friendly interactions
- Hedge banner → compact single line with icon
- Drawer panels → full-screen bottom sheet
