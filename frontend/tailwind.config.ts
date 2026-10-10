import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f1117',
        card: '#1a1d27',
        accent: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
        },
        danger: {
          DEFAULT: '#ef4444',
          soft: 'rgba(239,68,68,0.15)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          soft: 'rgba(245,158,11,0.15)',
        },
        success: {
          DEFAULT: '#22c55e',
          soft: 'rgba(34,197,94,0.15)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
      },
      animation: {
        fadeIn: 'fadeIn 0.3s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.6)',
        glow: '0 0 20px rgba(99,102,241,0.35)',
        'glow-red': '0 0 20px rgba(239,68,68,0.35)',
      },
    },
  },
  plugins: [],
}

export default config
