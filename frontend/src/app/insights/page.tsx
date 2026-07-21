'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// ── Design tokens ─────────────────────────────────────────────────────────────
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
    fontSize: '16px', fontWeight: 400, lineHeight: 1.6, letterSpacing: '0.32px', color: 'rgba(255,255,255,0.85)',
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

function GhostBtn({ children, onClick, loading }: { children: React.ReactNode; onClick?: () => void; loading?: boolean }) {
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick} disabled={loading}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        padding: '14px 24px', border: HL, borderRadius: '32px',
        background: hov ? 'rgba(255,255,255,0.08)' : 'transparent',
        color: T.onPrimary, cursor: loading ? 'wait' : 'pointer', transition: 'background 0.2s',
        fontFamily: 'inherit', ...T.buttonCap, opacity: loading ? 0.6 : 1,
      }}>
      {loading ? 'REFRESHING...' : children}
    </button>
  );
}

function SentimentBadge({ label }: { label: string }) {
  const isBull = label.toLowerCase().includes('bull') || label.toLowerCase().includes('pos');
  const isBear = label.toLowerCase().includes('bear') || label.toLowerCase().includes('neg');
  const bg = isBull ? '#1a2a1a' : isBear ? '#2a1a1a' : '#1a1a1a';
  const border = isBull ? '#2a5a2a' : isBear ? '#5a2a2a' : T.hairline;

  return (
    <span style={{
      ...T.micro, padding: '4px 12px', borderRadius: '32px',
      background: bg, border: `1px solid ${border}`,
      color: T.onPrimary, display: 'inline-block',
    }}>
      {label.toUpperCase()}
    </span>
  );
}

export default function InsightsPage() {
  const [summary, setSummary] = useState<string>('');
  const [regime, setRegime] = useState<{ regime: string; confidence: number; vix_level: number; description: string }>({
    regime: 'SIDEWAYS', confidence: 0.75, vix_level: 18.2, description: 'Normal consolidation regime. Mean reversion and range trading favored.',
  });
  const [observations, setObservations] = useState<Array<{ category: string; type: string; text: string }>>([]);
  const [news, setNews] = useState<Array<{ id: string; headline: string; source: string; sentiment_label: string; sentiment_score: number; published_at: string }>>([]);
  const [tickerSentiments, setTickerSentiments] = useState<Array<{ symbol: string; score: number; label: string }>>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);

  useEffect(() => {
    // Fetch initial market summary
    setSummary(
      "• Market Volatility: VIX sits at 18.2, indicating a normal risk environment.\n" +
      "• SPY Benchmark: Trading at $558.40 with steady institutional flow.\n" +
      "• Strategy Signals: EMA Crossover shows positive momentum alignment across tech constituents."
    );

    setObservations([
      {
        category: 'CONCENTRATION',
        type: 'WARNING',
        text: 'Over 50% of your portfolio is concentrated in Technology. Consider diversifying across Defensive sectors or utilizing PSQ hedge protection.',
      },
      {
        category: 'RISK',
        type: 'INFO',
        text: 'Portfolio Beta is within target bounds (< 0.90). Current auto-hedge engine status remains in STANDBY.',
      },
      {
        category: 'MACRO',
        type: 'POSITIVE',
        text: 'Market regime is classified as SIDEWAYS with VIX at 18.2. Mean Reversion strategy filters are active.',
      },
    ]);

    setNews([
      { id: '1', headline: 'NVIDIA Announces Next-Gen Blackwell Ultra Architecture Demand Surge', source: 'Financial Times', sentiment_label: 'positive', sentiment_score: 0.94, published_at: '10m ago' },
      { id: '2', headline: 'Apple Expands AI Integration Across iOS Ecosystem with New Chips', source: 'Bloomberg', sentiment_label: 'positive', sentiment_score: 0.88, published_at: '25m ago' },
      { id: '3', headline: 'Federal Reserve Signals Data-Dependent Stance Ahead of Inflation Print', source: 'Reuters', sentiment_label: 'neutral', sentiment_score: 0.51, published_at: '1h ago' },
      { id: '4', headline: 'Tech Sector Sees Rotational Shift as Treasury Yields Consolidate', source: 'Wall Street Journal', sentiment_label: 'negative', sentiment_score: 0.62, published_at: '2h ago' },
    ]);

    setTickerSentiments([
      { symbol: 'NVDA', score: 0.88, label: 'BULLISH' },
      { symbol: 'AAPL', score: 0.74, label: 'BULLISH' },
      { symbol: 'MSFT', score: 0.45, label: 'NEUTRAL' },
      { symbol: 'GOOGL', score: 0.52, label: 'NEUTRAL' },
      { symbol: 'TSLA', score: -0.32, label: 'BEARISH' },
    ]);
  }, []);

  const handleRefreshSummary = async () => {
    setLoadingSummary(true);
    setTimeout(() => {
      setSummary(
        "• AI Market Summary (Refreshed):\n" +
        "• Market Momentum: Tech leads gains with strong momentum in semiconductor and cloud infrastructure.\n" +
        "• Risk Environment: VIX remains stable at 18.2. Auto-hedging triggers remain unbreached."
      );
      setLoadingSummary(false);
    }, 1000);
  };

  return (
    <div style={{ background: T.canvasNight, minHeight: '100vh', color: T.onPrimary, fontFamily: "'Inter','Arial Narrow',Arial,sans-serif" }}>

      {/* Header & Regime Banner */}
      <div style={{ borderBottom: HL, padding: '80px 32px 32px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <p style={{ ...T.micro, marginBottom: '8px' }}>AI Intelligence Layer</p>
              <h1 style={{ ...T.displayXL, marginBottom: '16px' }}>AI INSIGHTS</h1>
            </div>
            {/* Market Regime Banner */}
            <div style={{
              background: T.canvasNightSoft, border: HL, padding: '16px 24px',
              borderRadius: '32px', display: 'flex', alignItems: 'center', gap: '16px',
            }}>
              <div>
                <p style={{ ...T.micro, color: T.inkMute, marginBottom: '2px' }}>CURRENT REGIME</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <SentimentBadge label={regime.regime} />
                  <span style={{ ...T.caption, color: T.onPrimaryMute }}>{Math.round(regime.confidence * 100)}% CONFIDENCE</span>
                </div>
              </div>
            </div>
          </div>
          <p style={{ ...T.body, maxWidth: '720px', marginTop: '16px' }}>{regime.description}</p>
        </div>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>

        {/* 2-column layout: Market Summary & Portfolio Observations */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>

          {/* Daily Market Summary */}
          <DataCard>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: 0 }}>Daily Market Summary</p>
              <GhostBtn onClick={handleRefreshSummary} loading={loadingSummary}>GENERATE NEW</GhostBtn>
            </div>
            <div style={{ background: T.canvasNight, border: HL, padding: '24px', minHeight: '160px', whiteSpace: 'pre-line' }}>
              <p style={{ ...T.body, color: T.onPrimary }}>{summary}</p>
            </div>
          </DataCard>

          {/* Portfolio Observations */}
          <DataCard>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Portfolio Observations</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {observations.map((obs, idx) => (
                <div key={idx} style={{
                  background: T.canvasNight, border: HL, padding: '16px 20px',
                  display: 'flex', flexDirection: 'column', gap: '4px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ ...T.micro, color: obs.type === 'WARNING' ? '#ff6b6b' : T.onPrimaryMute }}>
                      {obs.category} — {obs.type}
                    </span>
                  </div>
                  <p style={{ ...T.body, fontSize: '14px' }}>{obs.text}</p>
                </div>
              ))}
            </div>
          </DataCard>
        </div>

        {/* Ticker Sentiment Grid */}
        <div>
          <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '16px' }}>24H Ticker Sentiment Breakdown</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1px', background: T.hairline, border: HL }}>
            {tickerSentiments.map(ts => (
              <div key={ts.symbol} style={{ background: T.canvasNightSoft, padding: '20px', textAlign: 'center' }}>
                <p style={{ ...T.buttonCap, marginBottom: '8px' }}>{ts.symbol}</p>
                <div style={{ marginBottom: '8px' }}>
                  <SentimentBadge label={ts.label} />
                </div>
                <p style={{ ...T.caption, color: T.onPrimaryMute }}>Score: {ts.score > 0 ? `+${ts.score}` : ts.score}</p>
              </div>
            ))}
          </div>
        </div>

        {/* News Feed Table */}
        <DataCard style={{ padding: 0 }}>
          <div style={{ padding: '24px 32px', borderBottom: HL }}>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: 0 }}>News & FinBERT Sentiment Feed</p>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: HL }}>
                {['HEADLINE', 'SOURCE', 'SENTIMENT', 'CONFIDENCE', 'TIME'].map(h => (
                  <th key={h} style={{ ...T.micro, color: T.onPrimaryMute, padding: '16px 24px', textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {news.map((n, i) => (
                <tr key={n.id} style={{ borderBottom: i < news.length - 1 ? HL : 'none' }}>
                  <td style={{ padding: '16px 24px', ...T.body, color: T.onPrimary, maxWidth: '440px' }}>{n.headline}</td>
                  <td style={{ padding: '16px 24px', ...T.caption, color: T.onPrimaryMute }}>{n.source}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <SentimentBadge label={n.sentiment_label} />
                  </td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{Math.round(n.sentiment_score * 100)}%</td>
                  <td style={{ padding: '16px 24px', ...T.caption }}>{n.published_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>

      </div>
    </div>
  );
}
