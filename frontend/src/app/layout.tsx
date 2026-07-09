import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import NavOverlay from '@/components/NavOverlay';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '700'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'TradeAI — Algorithmic Trading Platform',
  description:
    'AI-powered trading intelligence. Automated strategies, real-time risk monitoring, and auto-hedging at the speed of markets.',
  keywords: 'algorithmic trading, AI trading, auto-hedging, risk management, Alpaca',
  openGraph: {
    title: 'TradeAI — Algorithmic Trading Platform',
    description: 'Automated strategies. Real-time risk. Auto-hedging at machine speed.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} style={{ background: '#000', color: '#fff' }}>
      <body style={{ background: '#000', minHeight: '100vh' }}>
        <NavOverlay />
        {children}
      </body>
    </html>
  );
}
