/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        ice: {
          500: '#AFDDFF',
          400: '#AFDDFF',
          300: '#C8E8FF',
          600: '#8AC8F5',
        },
        lumen: {
          bg: '#050607',
          dark1: '#050607',
          dark2: '#080B10',
          dark3: '#0B1017',
          dark4: '#101722',
          dark5: '#151D27',
          card: 'rgba(255, 255, 255, 0.025)',
          border: 'rgba(255, 255, 255, 0.12)',
          grid: 'rgba(255, 255, 255, 0.04)',
          muted: 'rgba(255, 255, 255, 0.50)',
          secondary: 'rgba(255, 255, 255, 0.65)',
          accent: '#AFDDFF',
          silver: '#C0C7D0',
          mutedBlue: '#6B8CAE',
          lavender: '#8D88A6',
          champagne: '#F2EFE9',
        },
        status: {
          green: '#9FE6C1',
          amber: '#F4C46B',
          red: '#E68A8A',
        }
      },
      transitionTimingFunction: {
        'lumen-entrance': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'lumen-interactive': 'cubic-bezier(0.76, 0, 0.24, 1)',
      }
    },
  },
  plugins: [],
}
