'use client';

import { useState } from 'react';

const HL = '1px solid #3a3a3f';
const MICRO: React.CSSProperties = { fontSize: '12px', fontWeight: 400, letterSpacing: '0.96px', textTransform: 'uppercase', color: '#f0f0fa', lineHeight: 2 };
const DISPLAY_LG: React.CSSProperties = { fontSize: 'clamp(24px,3vw,48px)', fontWeight: 700, lineHeight: 1.25, letterSpacing: '0.96px', textTransform: 'uppercase', color: '#fff' };
const DISPLAY_XL: React.CSSProperties = { fontSize: 'clamp(32px,4.5vw,60px)', fontWeight: 700, lineHeight: 1.2, letterSpacing: '1.2px', textTransform: 'uppercase', color: '#fff' };
const BODY: React.CSSProperties = { fontSize: '16px', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.32px', color: 'rgba(255,255,255,0.85)' };

const STRATEGIES = [
  {
    id: 'ema', name: 'EMA CROSSOVER', type: 'TREND FOLLOWING',
    signal: 'BUY', confidence: 0.78, active: true,
    params: { 'Fast EMA': '20', 'Slow EMA': '50', 'ADX Filter': '> 25', 'Time Horizon': 'INTRADAY' },
    desc: 'Golden cross / death cross detection on EMA 20/50 with ADX confirmation to avoid choppy markets. Look-ahead bias protected.',
  },
  {
    id: 'rsi', name: 'RSI MOMENTUM', type: 'MOMENTUM',
    signal: 'HOLD', confidence: 0.41, active: true,
    params: { 'RSI Period': '14', 'Oversold': '< 30', 'Overbought': '> 70', 'Time Horizon': 'SWING' },
    desc: 'RSI crossover at oversold/overbought levels with Rate-of-Change momentum and ATR-based dynamic stop loss.',
  },
  {
    id: 'mr', name: 'MEAN REVERSION', type: 'MEAN REVERSION',
    signal: 'SELL', confidence: 0.71, active: false,
    params: { 'BB Period': '20', 'BB Std Dev': '2.0', 'ADX Gate': '< 25', 'Z-Score': '> 2.0' },
    desc: 'Bollinger Band mean reversion with Z-score entry confirmation. Regime-gated — only fires in sideways markets (ADX < 25).',
  },
];

const signalColors: Record<string, string> = { BUY: '#1a3a1a', SELL: '#3a1a1a', HOLD: '#1a1a1a' };
const signalBorders: Record<string, string> = { BUY: '#2a5a2a', SELL: '#5a2a2a', HOLD: '#3a3a3f' };

function GhostBtn({ children, onClick, small }: { children: React.ReactNode; onClick?: () => void; small?: boolean }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        padding: small ? '10px 20px' : '14px 24px',
        border: HL, borderRadius: '32px',
        background: hov ? 'rgba(255,255,255,0.06)' : 'transparent',
        color: '#fff', fontFamily: 'inherit', fontSize: '13.008px',
        fontWeight: 700, letterSpacing: '1.17px', textTransform: 'uppercase',
        cursor: 'pointer', transition: 'background 0.2s',
      }}>
      {children}
    </button>
  );
}

export default function StrategiesPage() {
  const [selected, setSelected] = useState('ema');
  const strategy = STRATEGIES.find(s => s.id === selected)!;

  return (
    <div style={{ background: '#000', minHeight: '100vh', color: '#fff', fontFamily: "'Inter','Arial Narrow',Arial,sans-serif" }}>

      {/* Header */}
      <div style={{ borderBottom: HL, padding: '80px 32px 32px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ ...MICRO, marginBottom: '8px' }}>Intelligence Layer</p>
          <h1 style={{ ...DISPLAY_XL, marginBottom: 0 }}>STRATEGIES</h1>
        </div>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px', display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px' }}>

        {/* Strategy list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', background: '#3a3a3f', border: HL, alignSelf: 'start' }}>
          {STRATEGIES.map(s => (
            <button key={s.id} onClick={() => setSelected(s.id)}
              style={{
                background: selected === s.id ? '#0a0a0a' : '#000',
                padding: '20px 24px', border: 'none', textAlign: 'left',
                cursor: 'pointer', borderLeft: selected === s.id ? '1px solid #fff' : '1px solid transparent',
                transition: 'background 0.15s',
              }}>
              <p style={{ ...MICRO, color: s.active ? '#fff' : '#5a5a5f', marginBottom: '4px' }}>{s.name}</p>
              <span style={{
                fontSize: '11px', letterSpacing: '0.96px', textTransform: 'uppercase',
                padding: '2px 10px', borderRadius: '32px', lineHeight: 2, display: 'inline-block',
                background: signalColors[s.signal], border: `1px solid ${signalBorders[s.signal]}`, color: '#fff',
              }}>{s.signal}</span>
            </button>
          ))}
        </div>

        {/* Strategy detail */}
        <div style={{ background: '#0a0a0a', border: HL, padding: '40px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
            <div>
              <p style={{ ...MICRO, marginBottom: '8px' }}>{strategy.type}</p>
              <h2 style={{ ...DISPLAY_LG, marginBottom: '16px' }}>{strategy.name}</h2>
              <p style={{ ...BODY, maxWidth: '560px' }}>{strategy.desc}</p>
            </div>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{
                fontSize: '13px', letterSpacing: '0.96px', textTransform: 'uppercase',
                padding: '6px 16px', borderRadius: '32px',
                background: strategy.active ? '#1a3a1a' : '#1a1a1a',
                border: `1px solid ${strategy.active ? '#2a5a2a' : '#3a3a3f'}`, color: '#fff',
              }}>
                {strategy.active ? 'ACTIVE' : 'PAUSED'}
              </span>
              <GhostBtn small>{strategy.active ? 'PAUSE' : 'ACTIVATE'}</GhostBtn>
            </div>
          </div>

          {/* Confidence bar */}
          <div style={{ marginBottom: '40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <p style={MICRO}>Current Confidence</p>
              <p style={{ ...MICRO, color: '#fff' }}>{Math.round(strategy.confidence * 100)}%</p>
            </div>
            <div style={{ height: '1px', background: '#3a3a3f', position: 'relative' }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${strategy.confidence * 100}%`, background: '#fff', transition: 'width 0.6s ease' }} />
            </div>
          </div>

          {/* Parameters */}
          <p style={{ ...MICRO, marginBottom: '16px' }}>Parameters</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1px', background: '#3a3a3f', border: HL, marginBottom: '32px' }}>
            {Object.entries(strategy.params).map(([k, v]) => (
              <div key={k} style={{ background: '#000', padding: '16px 20px' }}>
                <p style={{ ...MICRO, marginBottom: '4px' }}>{k}</p>
                <p style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '0.96px', textTransform: 'uppercase', color: '#fff' }}>{v}</p>
              </div>
            ))}
          </div>

          <GhostBtn>RUN BACKTEST</GhostBtn>
        </div>
      </div>
    </div>
  );
}
