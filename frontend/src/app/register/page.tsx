'use client';

import { useState } from 'react';
import Link from 'next/link';

function GhostBtn({ children, type = 'button', onClick, loading }: {
  children: React.ReactNode; type?: 'button' | 'submit'; onClick?: () => void; loading?: boolean;
}) {
  const [hov, setHov] = useState(false);
  return (
    <button type={type} onClick={onClick} disabled={loading}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        width: '100%', padding: '18px 24px', border: '1px solid #ffffff',
        borderRadius: '32px', background: hov ? 'rgba(255,255,255,0.08)' : 'transparent',
        color: '#ffffff', fontFamily: 'inherit', fontSize: '13.008px',
        fontWeight: 700, lineHeight: 0.94, letterSpacing: '1.17px',
        textTransform: 'uppercase', cursor: loading ? 'wait' : 'pointer', transition: 'background 0.2s',
        opacity: loading ? 0.6 : 1,
      }}>
      {loading ? 'REGISTERING...' : children}
    </button>
  );
}

const HL = '1px solid #3a3a3f';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '14px 16px', background: '#0a0a0a',
    border: HL, borderRadius: '4px', color: '#ffffff',
    fontFamily: 'inherit', fontSize: '16px', letterSpacing: '0.32px',
    outline: 'none', transition: 'border-color 0.2s',
  };
  const labelStyle: React.CSSProperties = {
    fontSize: '12px', fontWeight: 400, letterSpacing: '0.96px',
    textTransform: 'uppercase', color: '#f0f0fa', lineHeight: 2,
    display: 'block', marginBottom: '8px',
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setError(null);
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      window.location.href = '/dashboard';
    }, 1000);
  };

  return (
    <main style={{
      minHeight: '100vh', background: '#000', display: 'flex',
      alignItems: 'center', justifyContent: 'center', padding: '32px',
      fontFamily: "'Inter','Arial Narrow',Arial,sans-serif",
    }}>
      <div style={{ width: '100%', maxWidth: '400px' }}>
        {/* Logo */}
        <Link href="/" style={{
          display: 'block', textAlign: 'center', marginBottom: '48px',
          fontSize: '13.008px', fontWeight: 700, letterSpacing: '1.17px',
          textTransform: 'uppercase', color: '#ffffff', textDecoration: 'none',
        }}>
          TRADEAI
        </Link>

        {/* Eyebrow */}
        <p style={{ fontSize: '12px', letterSpacing: '0.96px', textTransform: 'uppercase', color: '#f0f0fa', lineHeight: 2, marginBottom: '8px' }}>
          Create Account
        </p>
        <h1 style={{ fontSize: '48px', fontWeight: 700, lineHeight: 1.25, letterSpacing: '0.96px', textTransform: 'uppercase', color: '#fff', marginBottom: '40px' }}>
          REGISTER
        </h1>

        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={labelStyle}>Full Name</label>
            <input type="text" value={fullName} onChange={e => setFullName(e.target.value)}
              placeholder="John Doe" required style={inputStyle}
              onFocus={e => (e.target.style.borderColor = '#fff')}
              onBlur={e => (e.target.style.borderColor = '#3a3a3f')} />
          </div>
          <div>
            <label style={labelStyle}>Email Address</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com" required style={inputStyle}
              onFocus={e => (e.target.style.borderColor = '#fff')}
              onBlur={e => (e.target.style.borderColor = '#3a3a3f')} />
          </div>
          <div>
            <label style={labelStyle}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" required style={inputStyle}
              onFocus={e => (e.target.style.borderColor = '#fff')}
              onBlur={e => (e.target.style.borderColor = '#3a3a3f')} />
          </div>
          <div>
            <label style={labelStyle}>Confirm Password</label>
            <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
              placeholder="••••••••" required style={inputStyle}
              onFocus={e => (e.target.style.borderColor = '#fff')}
              onBlur={e => (e.target.style.borderColor = '#3a3a3f')} />
          </div>

          {error && (
            <p style={{ fontSize: '12px', color: '#ff6b6b', letterSpacing: '0.96px', textTransform: 'uppercase' }}>
              {error}
            </p>
          )}

          <GhostBtn type="submit" loading={loading}>CREATE ACCOUNT</GhostBtn>
        </form>

        <p style={{ marginTop: '32px', textAlign: 'center', fontSize: '13px', color: '#5a5a5f' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: '#fff', textDecoration: 'underline', textUnderlineOffset: '3px' }}>
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
