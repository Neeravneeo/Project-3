import type { Config } from 'tailwindcss';
import animate from 'tailwindcss-animate';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // ── Design System Colors (DESIGN.md) ───────────────────
      colors: {
        'canvas-night':      '#000000',
        'canvas-night-soft': '#0a0a0a',
        'canvas-light':      '#ffffff',
        'canvas-cool':       '#f0f0fa',
        'hairline-dark':     '#3a3a3f',
        'hairline-light':    '#e0e0e8',
        'on-primary':        '#ffffff',
        'on-primary-mute':   '#f0f0fa',
        ink:                 '#000000',
        'ink-mute':          '#5a5a5f',
        // Signal surface tints (NOT accent colors)
        'buy-tint':          '#1a2a1a',
        'sell-tint':         '#2a1a1a',
      },

      // ── Font Family ─────────────────────────────────────────
      fontFamily: {
        din: ['Inter', 'Arial Narrow', 'Arial', 'sans-serif'],
        sans: ['Inter', 'Arial Narrow', 'Arial', 'sans-serif'],
      },

      // ── Typography (display hierarchy from DESIGN.md) ──────
      fontSize: {
        'display-xxl': ['80px', { lineHeight: '0.95', letterSpacing: '1.6px'  }],
        'display-xl':  ['60px', { lineHeight: '1.2',  letterSpacing: '1.2px'  }],
        'display-lg':  ['48px', { lineHeight: '1.25', letterSpacing: '0.96px' }],
        'body-lg':     ['16px', { lineHeight: '1.7',  letterSpacing: '0.32px' }],
        'body-md':     ['16px', { lineHeight: '1.5',  letterSpacing: '0.32px' }],
        'button-cap':  ['13.008px', { lineHeight: '0.94', letterSpacing: '1.17px' }],
        'micro-cap':   ['12px', { lineHeight: '2.0',  letterSpacing: '0.96px' }],
        caption:       ['13.008px', { lineHeight: '1.5', letterSpacing: '0' }],
      },

      // ── Spacing (DESIGN.md base-8 system) ──────────────────
      spacing: {
        xxs:  '4px',
        xs:   '8px',
        sm:   '12px',
        md:   '16px',
        lg:   '18px',
        xl:   '24px',
        xxl:  '32px',
        huge: '48px',
      },

      // ── Border Radius ───────────────────────────────────────
      borderRadius: {
        xs:   '4px',
        sm:   '8px',
        md:   '16px',
        pill: '32px',
        full: '9999px',
      },

      // ── Breakpoints (DESIGN.md) ─────────────────────────────
      screens: {
        'sm-mobile': '600px',
        mobile:      '768px',
        tablet:      '960px',
        laptop:      '1280px',
        desktop:     '1500px',
      },

      // ── Keyframes ───────────────────────────────────────────
      keyframes: {
        'chevron-pulse': {
          '0%, 100%': { opacity: '0.3', transform: 'translateY(0)' },
          '50%':       { opacity: '0.9', transform: 'translateY(6px)' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(28px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'draw-line': {
          from: { strokeDashoffset: '1000' },
          to:   { strokeDashoffset: '0' },
        },
      },
      animation: {
        'chevron-pulse': 'chevron-pulse 2s ease-in-out infinite',
        'fade-up':       'fade-up 0.8s ease forwards',
        'draw-line':     'draw-line 2s ease forwards',
      },
    },
  },
  plugins: [animate],
};

export default config;
