'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

// ── Animated candlestick background ──────────────────────────────────────────
function CandleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Generate fake OHLCV data
    const candles: { o: number; h: number; l: number; c: number }[] = [];
    let price = 420;
    for (let i = 0; i < 80; i++) {
      const open = price;
      const move = (Math.random() - 0.48) * 12;
      const close = open + move;
      const high = Math.max(open, close) + Math.random() * 6;
      const low = Math.min(open, close) - Math.random() * 6;
      candles.push({ o: open, h: high, l: low, c: close });
      price = close;
    }

    let frame = 0;
    let animId: number;
    const draw = () => {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const w = canvas.width;
      const h = canvas.height;
      const candleW = w / candles.length;
      const prices = candles.flatMap(c => [c.h, c.l]);
      const minP = Math.min(...prices);
      const maxP = Math.max(...prices);
      const range = maxP - minP || 1;

      const toY = (p: number) => h * 0.2 + (1 - (p - minP) / range) * h * 0.6;

      ctx.globalAlpha = 0.07;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;

      candles.forEach((c, i) => {
        const x = i * candleW + candleW / 2;
        const oY = toY(c.o);
        const cY = toY(c.c);
        const hY = toY(c.h);
        const lY = toY(c.l);

        // Wick
        ctx.beginPath();
        ctx.moveTo(x, hY);
        ctx.lineTo(x, lY);
        ctx.stroke();

        // Body
        ctx.fillStyle = c.c >= c.o ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.05)';
        const bodyH = Math.max(2, Math.abs(cY - oY));
        ctx.fillRect(x - candleW * 0.3, Math.min(oY, cY), candleW * 0.6, bodyH);
      });

      // Moving average line
      ctx.globalAlpha = 0.12;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const period = 20;
      for (let i = period; i < candles.length; i++) {
        const avg = candles.slice(i - period, i).reduce((s, c) => s + c.c, 0) / period;
        const x = i * candleW + candleW / 2;
        const y = toY(avg);
        if (i === period) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();

      ctx.globalAlpha = 1;
      frame++;
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, []);
  return <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />;
}

// ── Ghost pill button ─────────────────────────────────────────────────────────
function GhostButton({ children, href }: { children: React.ReactNode; href?: string }) {
  const style: React.CSSProperties = {
    display: 'inline-block',
    padding: '18px 24px',
    border: '1px solid #ffffff',
    borderRadius: '32px',
    background: 'transparent',
    color: '#ffffff',
    fontFamily: 'inherit',
    fontSize: '13.008px',
    fontWeight: 700,
    lineHeight: 0.94,
    letterSpacing: '1.17px',
    textTransform: 'uppercase',
    textDecoration: 'none',
    cursor: 'pointer',
    transition: 'background 0.2s ease',
  };
  const [hovered, setHovered] = useState(false);
  const hoverStyle = hovered ? { background: 'rgba(255,255,255,0.08)' } : {};
  if (href) return (
    <Link href={href} style={{ ...style, ...hoverStyle }}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
      {children}
    </Link>
  );
  return (
    <button style={{ ...style, ...hoverStyle }}
      onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
      {children}
    </button>
  );
}

// ── Fade-in on scroll ─────────────────────────────────────────────────────────
function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); obs.disconnect(); }
    }, { threshold: 0.15 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(32px)',
      transition: `opacity 0.8s ease ${delay}ms, transform 0.8s ease ${delay}ms`,
    }}>
      {children}
    </div>
  );
}

// ── Risk score SVG gauge ──────────────────────────────────────────────────────
function RiskGauge({ score = 34 }: { score?: number }) {
  const r = 80, cx = 100, cy = 100;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <svg width="200" height="200" viewBox="0 0 200 200">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#3a3a3f" strokeWidth="2" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#ffffff" strokeWidth="2"
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        style={{ transform: 'rotate(-90deg)', transformOrigin: '100px 100px', transition: 'stroke-dasharray 1s ease' }}
      />
      <text x="50%" y="50%" textAnchor="middle" dy="0.35em"
        style={{ fill: '#fff', fontSize: '32px', fontWeight: 700, fontFamily: 'inherit', letterSpacing: '1.6px' }}>
        {score}
      </text>
      <text x="50%" y="62%" textAnchor="middle"
        style={{ fill: '#f0f0fa', fontSize: '11px', fontFamily: 'inherit', letterSpacing: '0.96px', textTransform: 'uppercase' }}>
        RISK SCORE
      </text>
    </svg>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const col: React.CSSProperties = {
    maxWidth: '1200px', margin: '0 auto', padding: '0 32px', width: '100%',
  };
  const eyebrow: React.CSSProperties = {
    fontSize: '12px', fontWeight: 400, lineHeight: 2, letterSpacing: '0.96px',
    textTransform: 'uppercase', color: '#f0f0fa', marginBottom: '24px',
  };
  const displayXXL: React.CSSProperties = {
    fontSize: 'clamp(40px, 6vw, 80px)', fontWeight: 700, lineHeight: 0.95,
    letterSpacing: '1.6px', textTransform: 'uppercase', color: '#ffffff',
    marginBottom: '24px',
  };
  const displayXL: React.CSSProperties = {
    fontSize: 'clamp(32px, 4.5vw, 60px)', fontWeight: 700, lineHeight: 1.2,
    letterSpacing: '1.2px', textTransform: 'uppercase', color: '#ffffff',
    marginBottom: '24px',
  };
  const displayLG: React.CSSProperties = {
    fontSize: 'clamp(28px, 3.5vw, 48px)', fontWeight: 700, lineHeight: 1.25,
    letterSpacing: '0.96px', textTransform: 'uppercase', color: '#ffffff',
    marginBottom: '16px',
  };
  const bodyLG: React.CSSProperties = {
    fontSize: '16px', fontWeight: 400, lineHeight: 1.7,
    letterSpacing: '0.32px', color: 'rgba(255,255,255,0.85)',
  };

  const hairline = '1px solid #3a3a3f';

  return (
    <main style={{ background: '#000000', color: '#ffffff', fontFamily: "'Inter', 'Arial Narrow', Arial, sans-serif" }}>

      {/* ── BAND 1: Hero ──────────────────────────────────────────────────── */}
      <section style={{
        position: 'relative', height: '100vh', minHeight: '600px',
        display: 'flex', alignItems: 'center', overflow: 'hidden', background: '#000',
      }}>
        <CandleBackground />
        <div style={{ ...col, position: 'relative', zIndex: 1 }}>
          <p style={eyebrow}>AI-Powered Trading Intelligence</p>
          <h1 style={displayXXL}>
            TRADE WITH<br />MACHINE PRECISION
          </h1>
          <p style={{ ...bodyLG, maxWidth: '520px', marginBottom: '40px' }}>
            Automated strategies. Real-time risk monitoring. Auto-hedging at the speed of markets.
          </p>
          <GhostButton href="/dashboard">GET STARTED</GhostButton>
        </div>
        {/* Scroll chevron */}
        <div style={{
          position: 'absolute', bottom: '32px', left: '50%', transform: 'translateX(-50%)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
          animation: 'chevronPulse 2s ease-in-out infinite',
        }}>
          <svg width="18" height="10" viewBox="0 0 18 10" fill="none">
            <path d="M1 1l8 8 8-8" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <style>{`
          @keyframes chevronPulse {
            0%,100% { opacity: 0.3; transform: translateX(-50%) translateY(0); }
            50% { opacity: 0.9; transform: translateX(-50%) translateY(6px); }
          }
        `}</style>
      </section>

      {/* ── BAND 2: Metrics strip ─────────────────────────────────────────── */}
      <section style={{ background: '#0a0a0a', borderTop: hairline, borderBottom: hairline }}>
        <div style={{ ...col, display: 'grid', gridTemplateColumns: 'repeat(3,1fr)' }}>
          {[
            { value: '3', label: 'Active Strategies' },
            { value: '< 60S', label: 'Signal Refresh Rate' },
            { value: '5-TRIGGER', label: 'Auto-Hedge Engine' },
          ].map((m, i) => (
            <FadeIn key={m.label} delay={i * 120}>
              <div style={{
                padding: '48px 32px', textAlign: 'center',
                borderRight: i < 2 ? hairline : 'none',
              }}>
                <div style={{ ...displayLG, marginBottom: '8px' }}>{m.value}</div>
                <div style={{ ...eyebrow, marginBottom: 0 }}>{m.label}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── BAND 3: Strategies ────────────────────────────────────────────── */}
      <section style={{ minHeight: '100vh', background: '#000', display: 'flex', alignItems: 'center', padding: '96px 0' }}>
        <div style={col}>
          <FadeIn>
            <p style={eyebrow}>Intelligence Layer</p>
            <h2 style={displayXL}>ENGINEERED TO<br />READ MARKETS</h2>
          </FadeIn>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px,1fr))',
            gap: '1px', background: '#3a3a3f', border: hairline, marginTop: '64px',
          }}>
            {[
              {
                name: 'EMA CROSSOVER', signal: 'TREND',
                desc: 'EMA 20/50 with ADX trend filter. Golden cross signals detected in real-time with look-ahead bias protection.',
                badge: 'TREND FOLLOWING',
              },
              {
                name: 'RSI MOMENTUM', signal: 'MOMENTUM',
                desc: 'RSI crossover at oversold/overbought levels with ROC momentum and ATR-based stop loss calculation.',
                badge: 'MOMENTUM',
              },
              {
                name: 'MEAN REVERSION', signal: 'REGIME',
                desc: 'Bollinger Bands + Z-score entry with ADX regime gate. Only fires in sideways markets — never fades trends.',
                badge: 'MEAN REVERSION',
              },
            ].map((s, i) => (
              <FadeIn key={s.name} delay={i * 150}>
                <div style={{
                  background: '#0a0a0a', padding: '48px 32px',
                  display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '320px',
                }}>
                  <span style={{
                    fontSize: '11px', fontWeight: 400, letterSpacing: '0.96px',
                    textTransform: 'uppercase', color: '#3a3a3f', border: '1px solid #3a3a3f',
                    padding: '4px 12px', borderRadius: '32px', alignSelf: 'flex-start',
                    lineHeight: 2,
                  }}>{s.badge}</span>
                  <h3 style={{ ...displayLG, marginBottom: 0 }}>{s.name}</h3>
                  <p style={{ ...bodyLG, flexGrow: 1 }}>{s.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── BAND 4: Risk / Auto-hedge ─────────────────────────────────────── */}
      <section style={{
        minHeight: '100vh', background: '#0a0a0a',
        borderTop: hairline, display: 'flex', alignItems: 'center', padding: '96px 0',
      }}>
        <div style={{ ...col, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '80px', alignItems: 'center' }}>
          <FadeIn>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <RiskGauge score={34} />
            </div>
          </FadeIn>
          <FadeIn delay={200}>
            <p style={eyebrow}>Auto-Hedging</p>
            <h2 style={displayXL}>RISK MANAGED<br />AT MACHINE SPEED</h2>
            <p style={{ ...bodyLG, marginBottom: '16px' }}>
              Five independent trigger types — VIX threshold, portfolio drawdown, beta cap, position loss, and manual — evaluated every 60 seconds.
            </p>
            <p style={{ ...bodyLG, marginBottom: '40px' }}>
              When a trigger fires, the hedge engine computes the optimal instrument (SH / SDS / PSQ), calculates exact share count using beta math, and executes the order automatically.
            </p>
            <GhostButton href="/risk">VIEW RISK ENGINE</GhostButton>
          </FadeIn>
        </div>
      </section>

      {/* ── BAND 5: Final CTA ─────────────────────────────────────────────── */}
      <section style={{
        height: '100vh', background: '#000', display: 'flex',
        alignItems: 'center', justifyContent: 'center', flexDirection: 'column',
        textAlign: 'center', gap: '40px', borderTop: hairline,
      }}>
        <FadeIn>
          <p style={eyebrow}>Begin</p>
          <h2 style={{ ...displayXXL, marginBottom: '40px' }}>READY<br />TO LAUNCH</h2>
          <GhostButton href="/dashboard">CONNECT ALPACA</GhostButton>
        </FadeIn>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer style={{
        background: '#000', borderTop: hairline,
        padding: '48px 32px 32px',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '32px', marginBottom: '48px' }}>
            <div>
              <p style={{ ...eyebrow, color: '#ffffff', marginBottom: '16px' }}>TradeAI</p>
              <p style={{ fontSize: '13px', color: '#5a5a5f', lineHeight: 1.6 }}>
                AI-powered trading &amp; auto-hedging for systematic investors.
              </p>
            </div>
            {[
              { title: 'Platform', items: ['Dashboard', 'Strategies', 'Risk', 'Signals', 'Orders'] },
              { title: 'Technology', items: ['Alpaca Markets', 'FinBERT', 'LangGraph', 'TimescaleDB', 'Redis'] },
              { title: 'Legal', items: ['Privacy Policy', 'Terms of Use', 'Risk Disclosure'] },
            ].map(col => (
              <div key={col.title}>
                <p style={{ ...eyebrow, color: '#ffffff', marginBottom: '16px' }}>{col.title}</p>
                {col.items.map(item => (
                  <p key={item} style={{ fontSize: '13px', color: '#5a5a5f', lineHeight: 2, cursor: 'pointer' }}>
                    {item}
                  </p>
                ))}
              </div>
            ))}
          </div>
          <div style={{ borderTop: hairline, paddingTop: '24px' }}>
            <p style={{ fontSize: '13px', color: '#5a5a5f', letterSpacing: 0 }}>
              © {new Date().getFullYear()} TradeAI. Paper trading only. Not financial advice. All trading involves risk.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
