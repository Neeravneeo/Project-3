'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_LINKS = [
  { label: 'Dashboard',  href: '/dashboard' },
  { label: 'Strategies', href: '/strategies' },
  { label: 'Risk',       href: '/risk' },
  { label: 'Signals',    href: '/signals' },
  { label: 'Orders',     href: '/orders' },
];

export default function NavOverlay() {
  const pathname  = usePathname();
  const [open,    setOpen]    = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => { setOpen(false); }, [pathname]);

  const isLanding = pathname === '/';

  return (
    <>
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        padding: '24px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: scrolled ? 'rgba(0,0,0,0.92)' : 'transparent',
        borderBottom: scrolled ? '1px solid #3a3a3f' : 'none',
        backdropFilter: scrolled ? 'blur(0px)' : 'none',
        transition: 'background 0.3s ease, border-color 0.3s ease',
      }}>
        {/* Logo */}
        <Link href="/" style={{
          fontSize: '13.008px', fontWeight: 700, letterSpacing: '1.17px',
          textTransform: 'uppercase', color: '#ffffff', textDecoration: 'none',
          lineHeight: 0.94,
        }}>
          TRADEAI
        </Link>

        {/* Desktop nav links */}
        <div style={{ display: 'flex', gap: '32px', alignItems: 'center' }}
          className="nav-desktop">
          {NAV_LINKS.map(link => (
            <Link key={link.href} href={link.href} style={{
              fontSize: '12px', fontWeight: 400, letterSpacing: '0.96px',
              textTransform: 'uppercase', lineHeight: 2,
              color: pathname === link.href ? '#ffffff' : 'rgba(255,255,255,0.6)',
              textDecoration: 'none',
              transition: 'color 0.15s ease',
              borderBottom: pathname === link.href ? '1px solid #ffffff' : '1px solid transparent',
              paddingBottom: '2px',
            }}>
              {link.label}
            </Link>
          ))}
          {!isLanding && (
            <Link href="/login" style={{
              padding: '10px 20px', border: '1px solid #ffffff',
              borderRadius: '32px', background: 'transparent', color: '#ffffff',
              fontSize: '13.008px', fontWeight: 700, letterSpacing: '1.17px',
              textTransform: 'uppercase', textDecoration: 'none', lineHeight: 0.94,
              transition: 'background 0.2s',
            }}>
              SIGN IN
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button onClick={() => setOpen(o => !o)}
          className="nav-mobile-toggle"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            display: 'none', padding: '8px', color: '#ffffff',
          }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            {open
              ? <><path d="M18 6L6 18M6 6l12 12" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" /></>
              : <><path d="M3 8h18M3 16h18" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" /></>
            }
          </svg>
        </button>
      </nav>

      {/* Mobile dropdown menu */}
      {open && (
        <div style={{
          position: 'fixed', top: '72px', left: 0, right: 0, zIndex: 49,
          background: '#000', borderBottom: '1px solid #3a3a3f',
          padding: '16px 32px 24px',
          display: 'flex', flexDirection: 'column', gap: '0',
        }}>
          {NAV_LINKS.map(link => (
            <Link key={link.href} href={link.href} style={{
              fontSize: '12px', fontWeight: 400, letterSpacing: '0.96px',
              textTransform: 'uppercase', lineHeight: 2, padding: '12px 0',
              color: pathname === link.href ? '#ffffff' : 'rgba(255,255,255,0.6)',
              textDecoration: 'none', borderBottom: '1px solid #3a3a3f',
            }}>
              {link.label}
            </Link>
          ))}
          <Link href="/login" style={{
            marginTop: '16px', padding: '14px 24px', border: '1px solid #ffffff',
            borderRadius: '32px', textAlign: 'center', color: '#ffffff',
            fontSize: '13.008px', fontWeight: 700, letterSpacing: '1.17px',
            textTransform: 'uppercase', textDecoration: 'none',
          }}>
            SIGN IN
          </Link>
        </div>
      )}

      {/* Responsive: hide/show nav items */}
      <style>{`
        @media (max-width: 768px) {
          .nav-desktop { display: none !important; }
          .nav-mobile-toggle { display: flex !important; }
        }
      `}</style>
    </>
  );
}
