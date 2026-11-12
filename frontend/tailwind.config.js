/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        shield: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        trust: {
          blue: '#0284c7',
          blueHover: '#0369a1',
          blueLight: '#f0f9ff',
          low: '#047857',
          lowBg: '#ecfdf5',
          lowBorder: '#a7f3d0',
          medium: '#b45309',
          mediumBg: '#fffbeb',
          mediumBorder: '#fde68a',
          high: '#be123c',
          highBg: '#fff1f2',
          highBorder: '#fecdd3',
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Noto Sans Devanagari"',
          'sans-serif'
        ]
      }
    },
  },
  plugins: [],
}

