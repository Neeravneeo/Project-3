'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// ── Design Tokens ─────────────────────────────────────────────────────────────
const T = {
  canvasNight:     '#000000',
  canvasNightSoft: '#0a0a0a',
  onPrimary:       '#ffffff',
  onPrimaryMute:   '#f0f0fa',
  hairline:        '#3a3a3f',
  inkMute:         '#5a5a5f',
  displayLG: {
    fontSize: 'clamp(24px, 3.5vw, 48px)', fontWeight: 700, lineHeight: 1.25,
    letterSpacing: '0.96px', textTransform: 'uppercase' as const, color: '#ffffff',
  } as React.CSSProperties,
  displayXL: {
    fontSize: 'clamp(32px, 4.5vw, 60px)', fontWeight: 700, lineHeight: 1.2,
    letterSpacing: '1.2px', textTransform: 'uppercase' as const, color: '#ffffff',
  } as React.CSSProperties,
  micro: {
    fontSize: '12px', fontWeight: 400, lineHeight: 2,
    letterSpacing: '0.96px', textTransform: 'uppercase' as const, color: '#f0f0fa',
  } as React.CSSProperties,
  buttonCap: {
    fontSize: '13.008px', fontWeight: 700, lineHeight: 0.94,
    letterSpacing: '1.17px', textTransform: 'uppercase' as const, color: '#ffffff',
  } as React.CSSProperties,
  body: {
    fontSize: '16px', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.32px', color: 'rgba(255,255,255,0.85)',
  } as React.CSSProperties,
  caption: {
    fontSize: '13.008px', fontWeight: 400, lineHeight: 1.5, color: '#5a5a5f',
  } as React.CSSProperties,
};

const HL = `1px solid ${T.hairline}`;

function DataCard({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: T.canvasNightSoft, border: HL,
      padding: '32px', ...style,
    }}>
      {children}
    </div>
  );
}

function GhostBtn({ children, onClick, type = 'button', loading }: { children: React.ReactNode; onClick?: () => void; type?: 'button' | 'submit'; loading?: boolean }) {
  const [hov, setHov] = useState(false);
  return (
    <button type={type} onClick={onClick} disabled={loading}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        padding: '14px 24px', border: HL, borderRadius: '32px',
        background: hov ? 'rgba(255,255,255,0.08)' : 'transparent',
        color: T.onPrimary, cursor: loading ? 'wait' : 'pointer', transition: 'background 0.2s',
        fontFamily: 'inherit', ...T.buttonCap, opacity: loading ? 0.6 : 1,
      }}>
      {loading ? 'PROCESSING...' : children}
    </button>
  );
}

function RiskGauge({ score = 34 }: { score?: number }) {
  const r = 70, cx = 90, cy = 90;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <svg width="180" height="180" viewBox="0 0 180 180">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#3a3a3f" strokeWidth="3" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#ffffff" strokeWidth="3"
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ transform: 'rotate(-90deg)', transformOrigin: '90px 90px', transition: 'stroke-dasharray 1s ease' }}
      />
      <text x="50%" y="46%" textAnchor="middle" dy="0.35em"
        style={{ fill: '#fff', fontSize: '32px', fontWeight: 700, fontFamily: 'inherit', letterSpacing: '1.6px' }}>
        {score}
      </text>
      <text x="50%" y="64%" textAnchor="middle"
        style={{ fill: '#f0f0fa', fontSize: '10px', fontFamily: 'inherit', letterSpacing: '0.96px', textTransform: 'uppercase' }}>
        RISK SCORE
      </text>
    </svg>
  );
}

export default function RiskPage() {
  const [thresholds, setThresholds] = useState({
    maxDrawdown: '5.0',
    maxBeta: '0.90',
    singlePosLoss: '3.0',
    vixHedgeLevel: '25.0',
  });
  const [saved, setSaved] = useState(false);
  const [hedgeStatus, setHedgeStatus] = useState({
    isHedged: false,
    currentBeta: 0.82,
    vix: 18.2,
    regime: 'NORMAL',
    lastTrigger: 'NONE',
  });

  const handleSaveThresholds = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleManualHedgeTrigger = () => {
    setHedgeStatus(prev => ({
      ...prev,
      isHedged: true,
      lastTrigger: 'MANUAL',
      currentBeta: 0.42,
    }));
  };

  const SECTORS = [
    { name: 'Technology', weight: 58 },
    { name: 'Consumer Cyclical', weight: 22 },
    { name: 'Financial', weight: 12 },
    { name: 'Hedge (SH)', weight: 8 },
  ];

  const CORRELATION_MATRIX = [
    { sym: 'AAPL', aapl: 1.00, nvda: 0.72, msft: 0.68, spy: 0.84 },
    { sym: 'NVDA', aapl: 0.72, nvda: 1.00, msft: 0.64, spy: 0.79 },
    { sym: 'MSFT', aapl: 0.68, nvda: 0.64, msft: 1.00, spy: 0.86 },
    { sym: 'SPY',  aapl: 0.84, nvda: 0.79, msft: 0.86, spy: 1.00 },
  ];

  const HEDGE_EVENTS = [
    { id: 'h1', trigger: 'VIX_THRESHOLD', instrument: 'SH', shares: 100, cost: '$1,420', beta_before: '0.95', beta_after: '0.52', date: '2026-07-08 14:30' },
    { id: 'h2', trigger: 'DRAWDOWN', instrument: 'SDS', shares: 50, cost: '$1,725', beta_before: '1.12', beta_after: '0.45', date: '2026-06-15 09:45' },
  ];

  return (
    <div style={{ background: T.canvasNight, minHeight: '100vh', color: T.onPrimary, fontFamily: "'Inter','Arial Narrow',Arial,sans-serif" }}>

      {/* Header */}
      <div style={{ borderBottom: HL, padding: '80px 32px 32px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ ...T.micro, marginBottom: '8px' }}>Risk Engine &amp; Auto-Hedging</p>
          <h1 style={{ ...T.displayXL, marginBottom: '32px' }}>RISK DASHBOARD</h1>

          {/* Top 5 Metrics Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1px', background: T.hairline, border: HL }}>
            {[
              { label: 'Portfolio Beta', val: hedgeStatus.currentBeta.toFixed(2), detail: 'Cap: 0.90' },
              { label: 'VaR (95% 1-Day)', val: '-$1,248', detail: '1.0% portfolio value' },
              { label: 'Max Drawdown', val: '-4.2%', detail: 'Trigger: -5.0%' },
              { label: 'Sharpe Ratio', val: '1.42', detail: 'Risk-free: 4.5%' },
              { label: 'Hedge Status', val: hedgeStatus.isHedged ? 'HEDGED' : 'STANDBY', detail: `VIX: ${hedgeStatus.vix}` },
            ].map(m => (
              <div key={m.label} style={{ background: T.canvasNightSoft, padding: '20px 16px' }}>
                <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '8px' }}>{m.label}</p>
                <p style={{ ...T.displayLG, fontSize: 'clamp(20px,2vw,28px)', marginBottom: '4px' }}>{m.val}</p>
                <p style={{ ...T.caption, color: T.inkMute }}>{m.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>

        {/* 2-Column Row: Risk Score Gauge + Hedge Control Panel */}
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>

          {/* Risk Gauge Card */}
          <DataCard style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Composite Risk Score</p>
            <RiskGauge score={34} />
            <p style={{ ...T.caption, color: T.onPrimaryMute, marginTop: '16px' }}>
              LOW RISK PROFILE (34/100)
            </p>
          </DataCard>

          {/* Hedge Control Panel */}
          <DataCard>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '4px' }}>Hedge Engine Control</p>
                <h2 style={{ ...T.displayLG, fontSize: '24px', marginBottom: 0 }}>
                  STATUS: {hedgeStatus.isHedged ? 'ACTIVE HEDGE' : 'STANDBY (MONITORING)'}
                </h2>
              </div>
              <GhostBtn onClick={handleManualHedgeTrigger}>MANUAL HEDGE TRIGGER</GhostBtn>
            </div>
            <p style={{ ...T.body, marginBottom: '24px' }}>
              The auto-hedge engine continuously evaluates 5 triggers (VIX level, Portfolio Drawdown, Beta Cap, Position Loss, Manual). When triggered, it automatically executes beta-neutralizing trades via inverse ETFs (SH, SDS, PSQ).
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1px', background: T.hairline, border: HL }}>
              {[
                { label: 'VIX Level', val: `${hedgeStatus.vix} (NORMAL)` },
                { label: 'Current Beta', val: hedgeStatus.currentBeta.toFixed(2) },
                { label: 'Drawdown', val: '-4.2%' },
                { label: 'Recommended Instrument', val: 'SH (1x Inverse)' },
              ].map(info => (
                <div key={info.label} style={{ background: T.canvasNight, padding: '16px' }}>
                  <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '4px' }}>{info.label}</p>
                  <p style={{ ...T.buttonCap }}>{info.val}</p>
                </div>
              ))}
            </div>
          </DataCard>
        </div>

        {/* 2-Column Row: Exposure Breakdown + Editable Risk Thresholds */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>

          {/* Sector Exposure */}
          <DataCard>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Sector Exposure Breakdown</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {SECTORS.map(s => (
                <div key={s.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ ...T.buttonCap }}>{s.name}</span>
                    <span style={{ ...T.caption, color: T.onPrimary }}>{s.weight}%</span>
                  </div>
                  <div style={{ height: '2px', background: T.hairline, position: 'relative' }}>
                    <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${s.weight}%`, background: T.onPrimary }} />
                  </div>
                </div>
              ))}
            </div>
          </DataCard>

          {/* Risk Thresholds Form */}
          <DataCard>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Configure Risk Gate Thresholds</p>
            <form onSubmit={handleSaveThresholds} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '4px' }}>Max Drawdown Trigger (%)</label>
                  <input type="text" value={thresholds.maxDrawdown} onChange={e => setThresholds({ ...thresholds, maxDrawdown: e.target.value })}
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none' }} />
                </div>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '4px' }}>Max Portfolio Beta Cap</label>
                  <input type="text" value={thresholds.maxBeta} onChange={e => setThresholds({ ...thresholds, maxBeta: e.target.value })}
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none' }} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '4px' }}>Single Position Loss Limit (%)</label>
                  <input type="text" value={thresholds.singlePosLoss} onChange={e => setThresholds({ ...thresholds, singlePosLoss: e.target.value })}
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none' }} />
                </div>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '4px' }}>VIX Trigger Level</label>
                  <input type="text" value={thresholds.vixHedgeLevel} onChange={e => setThresholds({ ...thresholds, vixHedgeLevel: e.target.value })}
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none' }} />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px' }}>
                <GhostBtn type="submit">SAVE THRESHOLDS</GhostBtn>
                {saved && <span style={{ ...T.micro, color: '#ffffff' }}>UPDATED SUCCESSFULLY</span>}
              </div>
            </form>
          </DataCard>
        </div>

        {/* Asset Correlation Matrix */}
        <DataCard>
          <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Asset Correlation Matrix</p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: HL }}>
                  <th style={{ ...T.micro, color: T.onPrimaryMute, padding: '12px', textAlign: 'left' }}>ASSET</th>
                  {CORRELATION_MATRIX.map(c => (
                    <th key={c.sym} style={{ ...T.micro, color: T.onPrimaryMute, padding: '12px', textAlign: 'center' }}>{c.sym}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CORRELATION_MATRIX.map((row, i) => (
                  <tr key={row.sym} style={{ borderBottom: i < CORRELATION_MATRIX.length - 1 ? HL : 'none' }}>
                    <td style={{ ...T.buttonCap, padding: '12px' }}>{row.sym}</td>
                    {[row.aapl, row.nvda, row.msft, row.spy].map((val, idx) => (
                      <td key={idx} style={{
                        padding: '12px', textAlign: 'center', ...T.body,
                        background: val === 1.0 ? 'rgba(255,255,255,0.1)' : 'transparent',
                      }}>
                        {val.toFixed(2)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataCard>

        {/* Hedge Event Log Table */}
        <DataCard style={{ padding: 0 }}>
          <div style={{ padding: '24px 32px', borderBottom: HL }}>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: 0 }}>Hedge Event Execution Log</p>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: HL }}>
                {['TRIGGER', 'INSTRUMENT', 'SHARES', 'COST', 'BETA BEFORE', 'BETA AFTER', 'TIMESTAMP'].map(h => (
                  <th key={h} style={{ ...T.micro, color: T.onPrimaryMute, padding: '16px 24px', textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {HEDGE_EVENTS.map((e, i) => (
                <tr key={e.id} style={{ borderBottom: i < HEDGE_EVENTS.length - 1 ? HL : 'none' }}>
                  <td style={{ padding: '16px 24px', ...T.buttonCap }}>{e.trigger}</td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{e.instrument}</td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{e.shares}</td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{e.cost}</td>
                  <td style={{ padding: '16px 24px', ...T.caption, color: T.onPrimaryMute }}>{e.beta_before}</td>
                  <td style={{ padding: '16px 24px', ...T.caption, color: T.onPrimary }}>{e.beta_after}</td>
                  <td style={{ padding: '16px 24px', ...T.caption }}>{e.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>

      </div>
    </div>
  );
}
