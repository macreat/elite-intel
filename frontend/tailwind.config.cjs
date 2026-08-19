/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a0e1a',
          800: '#0f1629',
          700: '#151d35',
          600: '#1c2541',
          500: '#243050',
        },
        mint: {
          400: '#5eead4',
          500: '#2dd4bf',
          600: '#00d4aa',
          700: '#00b894',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
        },
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255,255,255,0.04)',
        glow: '0 0 20px rgba(0, 212, 170, 0.15)',
      },
      backgroundImage: {
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
    },
  },
  plugins: [],
}
