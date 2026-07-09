'use client';

import { useState } from 'react';
import Link from 'next/link';

// ── Design tokens (inline for isolation) ─────────────────────────────────────
const T = {
  canvasNight:     '#000000',
  canvasNightSoft: '#0a0a0a',
  onPrimary:       '#ffffff',
  onPrimaryMute:   '#f0f0fa',
  hairline:        '#3a3a3f',
  inkMute:         '#5a5a5f',
  displayLG: {
    fontSize: '48px', fontWeight: 700, lineHeight: 1.25,
    letterSpacing: '0.96px', textTransform: 'uppercase' as const,
  } as React.CSSProperties,
  displayXL: {
    fontSize: '60px', fontWeight: 700, lineHeight: 1.2,
    letterSpacing: '1.2px', textTransform: 'uppercase' as const,
  } as React.CSSProperties,
  micro: {
    fontSize: '12px', fontWeight: 400, lineHeight: 2,
    letterSpacing: '0.96px', textTransform: 'uppercase' as const,
  } as React.CSSProperties,
  buttonCap: {
    fontSize: '13.008px', fontWeight: 700, lineHeight: 0.94,
    letterSpacing: '1.17px', textTransform: 'uppercase' as const,
  } as React.CSSProperties,
  body: {
    fontSize: '16px', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.32px',
  } as React.CSSProperties,
  caption: {
    fontSize: '13.008px', fontWeight: 400, lineHeight: 1.5,
  } as React.CSSProperties,
};

const hl = `1px solid ${T.hairline}`;

// ── Shared card ───────────────────────────────────────────────────────────────
function DataCard({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: T.canvasNightSoft, border: hl,
      padding: '24px', ...style,
    }}>
      {children}
    </div>
  );
}

// ── Signal badge ──────────────────────────────────────────────────────────────
function SignalBadge({ direction }: { direction: 'BUY' | 'SELL' | 'HOLD' }) {
  const colors: Record<string, string> = { BUY: '#1a3a1a', SELL: '#3a1a1a', HOLD: '#1a1a1a' };
  const borders: Record<string, string> = { BUY: '#2a5a2a', SELL: '#5a2a2a', HOLD: '#3a3a3f' };
  return (
    <span style={{
      ...T.micro, padding: '4px 12px', borderRadius: '32px',
      background: colors[direction], border: `1px solid ${borders[direction]}`,
      color: T.onPrimary, display: 'inline-block',
    }}>
      {direction}
    </span>
  );
}

// ── Ghost pill button ─────────────────────────────────────────────────────────
function GhostBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        ...T.buttonCap, padding: '14px 24px', border: hl, borderRadius: '32px',
        background: hov ? 'rgba(255,255,255,0.06)' : 'transparent',
        color: T.onPrimary, cursor: 'pointer', transition: 'background 0.2s',
        fontFamily: 'inherit',
      }}>
      {children}
    </button>
  );
}

// ── Sparkline (pure SVG, no deps) ─────────────────────────────────────────────
function Sparkline({ data, positive }: { data: number[]; positive: boolean }) {
  const w = 120, h = 40;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ overflow: 'visible' }}>
      <polyline points={pts} fill="none"
        stroke={positive ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.3)'}
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Mock data ─────────────────────────────────────────────────────────────────
const POSITIONS = [
  { symbol: 'AAPL', qty: 50, price: 213.40, avgCost: 198.20, pnlPct: 7.67, sparkData: [198, 200, 197, 205, 210, 208, 213] },
  { symbol: 'NVDA', qty: 20, price: 134.60, avgCost: 118.50, pnlPct: 13.59, sparkData: [118, 122, 119, 128, 130, 132, 134] },
  { symbol: 'MSFT', qty: 30, price: 442.10, avgCost: 448.00, pnlPct: -1.31, sparkData: [448, 445, 449, 443, 441, 440, 442] },
  { symbol: 'SH',   qty: 100, price: 14.20, avgCost: 14.00, pnlPct: 1.43, sparkData: [14.0, 14.1, 14.0, 14.2, 14.1, 14.2, 14.2] },
];

const SIGNALS = [
  { symbol: 'AAPL', direction: 'BUY' as const,  confidence: 0.78, strategies: 'EMA + RSI', time: '2m ago' },
  { symbol: 'NVDA', direction: 'BUY' as const,  confidence: 0.83, strategies: 'EMA + MR',  time: '4m ago' },
  { symbol: 'MSFT', direction: 'HOLD' as const, confidence: 0.41, strategies: 'RSI',        time: '5m ago' },
  { symbol: 'TSLA', direction: 'SELL' as const, confidence: 0.71, strategies: 'MR + RSI',  time: '6m ago' },
];

const METRICS = [
  { label: 'Portfolio Value', value: '$124,850', sub: '+$4,850 today' },
  { label: 'Sharpe Ratio',   value: '1.42',      sub: 'Annualized' },
  { label: 'Max Drawdown',   value: '-4.2%',     sub: '90-day period' },
  { label: 'Risk Score',     value: '34 / 100',  sub: 'Low risk' },
  { label: 'Portfolio Beta', value: '0.82',      sub: 'vs SPY benchmark' },
  { label: 'VaR (95%)',      value: '-$1,248',   sub: 'Daily estimate' },
];

// ── Page ──────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'positions' | 'signals' | 'risk'>('positions');

  const tabStyle = (tab: string): React.CSSProperties => ({
    ...T.micro, padding: '12px 24px', cursor: 'pointer', background: 'transparent',
    border: 'none', borderBottom: activeTab === tab ? `1px solid ${T.onPrimary}` : '1px solid transparent',
    color: activeTab === tab ? T.onPrimary : T.inkMute,
    fontFamily: 'inherit', transition: 'color 0.2s, border-color 0.2s',
  });

  return (
    <div style={{ background: T.canvasNight, minHeight: '100vh', color: T.onPrimary, fontFamily: "'Inter','Arial Narrow',Arial,sans-serif" }}>

      {/* Page header */}
      <div style={{ borderBottom: hl, padding: '48px 32px 32px', background: T.canvasNight }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '8px' }}>Overview</p>
          <h1 style={{ ...T.displayXL, fontSize: 'clamp(32px,4vw,60px)', marginBottom: '32px' }}>DASHBOARD</h1>

          {/* Top metrics grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: '1px', background: T.hairline, border: hl }}>
            {METRICS.map((m, i) => (
              <div key={m.label} style={{ background: T.canvasNightSoft, padding: '20px 16px' }}>
                <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '8px' }}>{m.label}</p>
                <p style={{ ...T.displayLG, fontSize: 'clamp(20px,2vw,28px)', marginBottom: '4px' }}>{m.value}</p>
                <p style={{ ...T.caption, color: T.inkMute }}>{m.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', alignItems: 'start' }}>

          {/* Left: Tabs panel */}
          <div>
            {/* Tab bar */}
            <div style={{ display: 'flex', borderBottom: hl, marginBottom: '24px' }}>
              {(['positions', 'signals', 'risk'] as const).map(tab => (
                <button key={tab} style={tabStyle(tab)} onClick={() => setActiveTab(tab)}>
                  {tab}
                </button>
              ))}
            </div>

            {/* Positions tab */}
            {activeTab === 'positions' && (
              <DataCard style={{ padding: 0 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: hl }}>
                      {['SYMBOL', 'QTY', 'PRICE', 'AVG COST', 'P&L', 'TREND', ''].map(h => (
                        <th key={h} style={{ ...T.micro, color: T.onPrimaryMute, padding: '16px', textAlign: 'left' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {POSITIONS.map((p, i) => (
                      <tr key={p.symbol} style={{ borderBottom: i < POSITIONS.length - 1 ? hl : 'none' }}>
                        <td style={{ padding: '16px', ...T.buttonCap }}>{p.symbol}</td>
                        <td style={{ padding: '16px', ...T.body, color: T.onPrimaryMute }}>{p.qty}</td>
                        <td style={{ padding: '16px', ...T.body }}>${p.price.toFixed(2)}</td>
                        <td style={{ padding: '16px', ...T.body, color: T.onPrimaryMute }}>${p.avgCost.toFixed(2)}</td>
                        <td style={{ padding: '16px', ...T.body, color: p.pnlPct >= 0 ? '#ffffff' : 'rgba(255,255,255,0.45)' }}>
                          {p.pnlPct >= 0 ? '+' : ''}{p.pnlPct.toFixed(2)}%
                        </td>
                        <td style={{ padding: '16px' }}>
                          <Sparkline data={p.sparkData} positive={p.pnlPct >= 0} />
                        </td>
                        <td style={{ padding: '16px' }}>
                          <GhostBtn>CLOSE</GhostBtn>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </DataCard>
            )}

            {/* Signals tab */}
            {activeTab === 'signals' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', background: T.hairline, border: hl }}>
                {SIGNALS.map(s => (
                  <div key={s.symbol} style={{
                    background: T.canvasNightSoft, padding: '20px 24px',
                    display: 'flex', alignItems: 'center', gap: '24px',
                  }}>
                    <span style={{ ...T.buttonCap, minWidth: '60px' }}>{s.symbol}</span>
                    <SignalBadge direction={s.direction} />
                    <div style={{ flexGrow: 1 }}>
                      <p style={{ ...T.caption, color: T.onPrimaryMute }}>{s.strategies}</p>
                    </div>
                    {/* Confidence bar */}
                    <div style={{ width: '120px' }}>
                      <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '4px' }}>{Math.round(s.confidence * 100)}% CONF</p>
                      <div style={{ height: '1px', background: T.hairline, position: 'relative' }}>
                        <div style={{ position: 'absolute', left: 0, top: 0, height: '1px', width: `${s.confidence * 100}%`, background: T.onPrimary }} />
                      </div>
                    </div>
                    <span style={{ ...T.caption, color: T.inkMute, minWidth: '50px' }}>{s.time}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Risk tab */}
            {activeTab === 'risk' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: T.hairline, border: hl }}>
                {[
                  { label: 'Portfolio Beta', value: '0.82', detail: 'Below 1.5 cap — no hedge required' },
                  { label: 'VaR 95%', value: '-$1,248', detail: '1-day historical Value at Risk' },
                  { label: 'CVaR 95%', value: '-$1,890', detail: 'Expected Shortfall beyond VaR' },
                  { label: 'Max Drawdown', value: '-4.2%', detail: '90-day period, from equity peak' },
                  { label: 'Annualized Vol', value: '14.8%', detail: 'Below average market volatility' },
                  { label: 'Hedge Status', value: 'INACTIVE', detail: 'VIX: 18.2 — Normal regime' },
                ].map(r => (
                  <div key={r.label} style={{ background: T.canvasNightSoft, padding: '24px' }}>
                    <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '8px' }}>{r.label}</p>
                    <p style={{ ...T.displayLG, fontSize: '28px', marginBottom: '8px' }}>{r.value}</p>
                    <p style={{ ...T.caption, color: T.inkMute }}>{r.detail}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: sidebar panels */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

            {/* Hedge status */}
            <DataCard>
              <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '16px' }}>Hedge Engine</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <p style={{ ...T.displayLG, fontSize: '24px', marginBottom: 0 }}>STANDBY</p>
                <SignalBadge direction="HOLD" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
                {[
                  { label: 'VIX Level', value: '18.2' },
                  { label: 'Regime', value: 'NORMAL' },
                  { label: 'Beta', value: '0.82' },
                  { label: 'Drawdown', value: '-4.2%' },
                ].map(r => (
                  <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: hl, paddingBottom: '8px' }}>
                    <span style={{ ...T.micro, color: T.onPrimaryMute }}>{r.label}</span>
                    <span style={{ ...T.caption }}>{r.value}</span>
                  </div>
                ))}
              </div>
              <GhostBtn>RUN ANALYSIS</GhostBtn>
            </DataCard>

            {/* Market status */}
            <DataCard>
              <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '16px' }}>Market Status</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { symbol: 'SPY', price: '558.40', change: '+0.82%', pos: true },
                  { symbol: 'QQQ', price: '484.20', change: '+1.14%', pos: true },
                  { symbol: 'VXX', price: '18.20',  change: '-2.10%', pos: false },
                  { symbol: 'SH',  price: '14.20',  change: '-0.84%', pos: false },
                ].map(m => (
                  <div key={m.symbol} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ ...T.buttonCap }}>{m.symbol}</span>
                    <span style={{ ...T.body }}>${m.price}</span>
                    <span style={{ ...T.caption, color: m.pos ? '#ffffff' : 'rgba(255,255,255,0.45)' }}>{m.change}</span>
                  </div>
                ))}
              </div>
            </DataCard>

            {/* Quick actions */}
            <DataCard>
              <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '16px' }}>Quick Actions</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <GhostBtn>REFRESH SIGNALS</GhostBtn>
                <GhostBtn>HEDGE ANALYSIS</GhostBtn>
                <GhostBtn>RISK REPORT</GhostBtn>
              </div>
            </DataCard>
          </div>
        </div>
      </div>
    </div>
  );
}
