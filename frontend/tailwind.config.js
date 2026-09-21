/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          navy: '#0f172a',
          blue: '#1e3a8a',
          accent: '#2563eb',
          light: '#f8fafc',
          card: '#ffffff',
          border: '#e2e8f0',
        },
        metrology: {
          pass: '#16a34a',
          fail: '#dc2626',
          warning: '#d97706',
          info: '#0284c7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'Noto Sans Telugu', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace']
      }
    },
  },
  plugins: [],
}
