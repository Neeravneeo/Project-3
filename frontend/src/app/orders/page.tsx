'use client';

import { useState } from 'react';
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
      {loading ? 'SUBMITTING...' : children}
    </button>
  );
}

function SideBadge({ side }: { side: 'BUY' | 'SELL' }) {
  const bg = side === 'BUY' ? '#1a2a1a' : '#2a1a1a';
  const border = side === 'BUY' ? '#2a5a2a' : '#5a5a5f';
  return (
    <span style={{
      ...T.micro, padding: '4px 12px', borderRadius: '32px',
      background: bg, border: `1px solid ${border}`, color: T.onPrimary,
      display: 'inline-block',
    }}>
      {side}
    </span>
  );
}

export default function OrdersPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState('10');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState('213.40');
  const [filterTab, setFilterTab] = useState<'ALL' | 'FILLED' | 'REJECTED' | 'CANCELED'>('ALL');
  const [submittedMessage, setSubmittedMessage] = useState<string | null>(null);

  const [activeOrders, setActiveOrders] = useState([
    { id: 'o-101', symbol: 'NVDA', side: 'BUY' as const, qty: 15, type: 'LIMIT', price: '$130.00', status: 'PENDING', time: '10:45 AM' },
    { id: 'o-102', symbol: 'MSFT', side: 'SELL' as const, qty: 10, type: 'LIMIT', price: '$450.00', status: 'OPEN', time: '11:15 AM' },
  ]);

  const [orderHistory] = useState([
    { id: 'o-099', symbol: 'AAPL', side: 'BUY' as const, qty: 50, type: 'MARKET', price: '$213.40', status: 'FILLED', time: 'Yesterday' },
    { id: 'o-098', symbol: 'SH', side: 'BUY' as const, qty: 100, type: 'MARKET', price: '$14.20', status: 'FILLED', time: '2 days ago' },
    { id: 'o-097', symbol: 'TSLA', side: 'BUY' as const, qty: 25, type: 'LIMIT', price: '$240.00', status: 'REJECTED', time: '3 days ago', reason: 'Pre-Trade Gate: Cash limit exceeded' },
    { id: 'o-096', symbol: 'AMZN', side: 'SELL' as const, qty: 30, type: 'LIMIT', price: '$190.00', status: 'CANCELED', time: '4 days ago' },
  ]);

  const handleSubmitOrder = (e: React.FormEvent) => {
    e.preventDefault();
    const newOrder = {
      id: `o-${Date.now().toString().slice(-3)}`,
      symbol: symbol.toUpperCase(),
      side,
      qty: parseInt(quantity) || 1,
      type: orderType,
      price: orderType === 'LIMIT' ? `$${limitPrice}` : 'MARKET',
      status: 'OPEN',
      time: 'Just now',
    };
    setActiveOrders([newOrder, ...activeOrders]);
    setSubmittedMessage(`Order submitted: ${side} ${quantity} ${symbol.toUpperCase()} (Pre-trade checks passed)`);
    setTimeout(() => setSubmittedMessage(null), 4000);
  };

  const handleCancelOrder = (id: string) => {
    setActiveOrders(activeOrders.filter(o => o.id !== id));
  };

  const filteredHistory = filterTab === 'ALL'
    ? orderHistory
    : orderHistory.filter(o => o.status === filterTab);

  return (
    <div style={{ background: T.canvasNight, minHeight: '100vh', color: T.onPrimary, fontFamily: "'Inter','Arial Narrow',Arial,sans-serif" }}>

      {/* Header */}
      <div style={{ borderBottom: HL, padding: '80px 32px 32px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <p style={{ ...T.micro, marginBottom: '8px' }}>Trade Execution &amp; Gate</p>
          <h1 style={{ ...T.displayXL, marginBottom: 0 }}>ORDER MANAGEMENT</h1>
        </div>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>

        {/* 2-Column Row: Order Form + Active Orders */}
        <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: '24px' }}>

          {/* New Order Form */}
          <DataCard>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: '24px' }}>Place New Order</p>
            <form onSubmit={handleSubmitOrder} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Side toggle */}
              <div>
                <label style={{ ...T.micro, display: 'block', marginBottom: '8px' }}>Order Side</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: T.hairline, border: HL }}>
                  <button type="button" onClick={() => setSide('BUY')} style={{
                    padding: '12px', background: side === 'BUY' ? '#1a2a1a' : T.canvasNight,
                    color: '#fff', border: 'none', cursor: 'pointer', ...T.buttonCap,
                  }}>
                    BUY
                  </button>
                  <button type="button" onClick={() => setSide('SELL')} style={{
                    padding: '12px', background: side === 'SELL' ? '#2a1a1a' : T.canvasNight,
                    color: '#fff', border: 'none', cursor: 'pointer', ...T.buttonCap,
                  }}>
                    SELL
                  </button>
                </div>
              </div>

              {/* Ticker & Quantity */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '6px' }}>Ticker Symbol</label>
                  <input type="text" value={symbol} onChange={e => setSymbol(e.target.value)} required
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none', ...T.buttonCap }} />
                </div>
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '6px' }}>Quantity</label>
                  <input type="number" min="1" value={quantity} onChange={e => setQuantity(e.target.value)} required
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none', ...T.body }} />
                </div>
              </div>

              {/* Order Type */}
              <div>
                <label style={{ ...T.micro, display: 'block', marginBottom: '6px' }}>Order Type</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: T.hairline, border: HL }}>
                  <button type="button" onClick={() => setOrderType('MARKET')} style={{
                    padding: '12px', background: orderType === 'MARKET' ? T.canvasNightSoft : T.canvasNight,
                    color: '#fff', border: 'none', cursor: 'pointer', ...T.micro,
                  }}>
                    MARKET
                  </button>
                  <button type="button" onClick={() => setOrderType('LIMIT')} style={{
                    padding: '12px', background: orderType === 'LIMIT' ? T.canvasNightSoft : T.canvasNight,
                    color: '#fff', border: 'none', cursor: 'pointer', ...T.micro,
                  }}>
                    LIMIT
                  </button>
                </div>
              </div>

              {/* Limit price input */}
              {orderType === 'LIMIT' && (
                <div>
                  <label style={{ ...T.micro, display: 'block', marginBottom: '6px' }}>Limit Price ($)</label>
                  <input type="text" value={limitPrice} onChange={e => setLimitPrice(e.target.value)}
                    style={{ width: '100%', padding: '12px', background: T.canvasNight, border: HL, color: '#fff', outline: 'none', ...T.body }} />
                </div>
              )}

              {/* Pre-trade gate note */}
              <div style={{ padding: '12px', background: T.canvasNight, border: HL }}>
                <p style={{ ...T.caption, fontSize: '12px', color: T.onPrimaryMute }}>
                  ✓ Pre-trade risk gate will auto-validate market hours, cash availability, and portfolio beta caps.
                </p>
              </div>

              <GhostBtn type="submit">SUBMIT ORDER</GhostBtn>
              {submittedMessage && (
                <p style={{ ...T.micro, color: '#ffffff', textAlign: 'center', marginTop: '8px' }}>
                  {submittedMessage}
                </p>
              )}
            </form>
          </DataCard>

          {/* Active Orders Panel */}
          <DataCard style={{ padding: 0 }}>
            <div style={{ padding: '24px 32px', borderBottom: HL }}>
              <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: 0 }}>Active &amp; Pending Orders</p>
            </div>
            {activeOrders.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: HL }}>
                    {['SYMBOL', 'SIDE', 'QTY', 'TYPE', 'PRICE', 'STATUS', ''].map(h => (
                      <th key={h} style={{ ...T.micro, color: T.onPrimaryMute, padding: '16px 24px', textAlign: 'left' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {activeOrders.map((o, i) => (
                    <tr key={o.id} style={{ borderBottom: i < activeOrders.length - 1 ? HL : 'none' }}>
                      <td style={{ padding: '16px 24px', ...T.buttonCap }}>{o.symbol}</td>
                      <td style={{ padding: '16px 24px' }}><SideBadge side={o.side} /></td>
                      <td style={{ padding: '16px 24px', ...T.body }}>{o.qty}</td>
                      <td style={{ padding: '16px 24px', ...T.caption, color: T.onPrimaryMute }}>{o.type}</td>
                      <td style={{ padding: '16px 24px', ...T.body }}>{o.price}</td>
                      <td style={{ padding: '16px 24px', ...T.micro }}>{o.status}</td>
                      <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                        <button onClick={() => handleCancelOrder(o.id)} style={{
                          background: 'transparent', border: HL, padding: '6px 14px', borderRadius: '32px',
                          color: '#fff', cursor: 'pointer', ...T.micro, fontSize: '10px',
                        }}>
                          CANCEL
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ padding: '48px 32px', textAlign: 'center' }}>
                <p style={{ ...T.body, color: T.inkMute }}>No active or pending orders.</p>
              </div>
            )}
          </DataCard>
        </div>

        {/* Order History Table with Filter Tabs */}
        <DataCard style={{ padding: 0 }}>
          <div style={{ padding: '24px 32px', borderBottom: HL, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <p style={{ ...T.micro, color: T.onPrimaryMute, marginBottom: 0 }}>Order History Log</p>

            {/* Filter Tabs */}
            <div style={{ display: 'flex', gap: '1px', background: T.hairline, border: HL }}>
              {(['ALL', 'FILLED', 'REJECTED', 'CANCELED'] as const).map(tab => (
                <button key={tab} onClick={() => setFilterTab(tab)} style={{
                  padding: '8px 16px', background: filterTab === tab ? T.canvasNightSoft : T.canvasNight,
                  color: filterTab === tab ? T.onPrimary : T.inkMute, border: 'none', cursor: 'pointer', ...T.micro,
                }}>
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: HL }}>
                {['ORDER ID', 'SYMBOL', 'SIDE', 'QTY', 'TYPE', 'PRICE', 'STATUS', 'TIMESTAMP'].map(h => (
                  <th key={h} style={{ ...T.micro, color: T.onPrimaryMute, padding: '16px 24px', textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((o, i) => (
                <tr key={o.id} style={{ borderBottom: i < filteredHistory.length - 1 ? HL : 'none' }}>
                  <td style={{ padding: '16px 24px', ...T.caption, color: T.inkMute }}>{o.id}</td>
                  <td style={{ padding: '16px 24px', ...T.buttonCap }}>{o.symbol}</td>
                  <td style={{ padding: '16px 24px' }}><SideBadge side={o.side} /></td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{o.qty}</td>
                  <td style={{ padding: '16px 24px', ...T.caption, color: T.onPrimaryMute }}>{o.type}</td>
                  <td style={{ padding: '16px 24px', ...T.body }}>{o.price}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <span style={{
                      ...T.micro, padding: '2px 8px', borderRadius: '32px',
                      background: o.status === 'FILLED' ? '#1a2a1a' : o.status === 'REJECTED' ? '#2a1a1a' : '#1a1a1a',
                      border: `1px solid ${o.status === 'FILLED' ? '#2a5a2a' : o.status === 'REJECTED' ? '#5a2a2a' : T.hairline}`,
                    }}>
                      {o.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px 24px', ...T.caption }}>{o.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </DataCard>

      </div>
    </div>
  );
}
