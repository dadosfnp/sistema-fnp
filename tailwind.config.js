/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './aplicacoes/**/templates/**/*.html',
    './aplicacoes/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        fnp: {
          50:  '#f0f5ff',
          100: '#e0ebff',
          200: '#c2d6ff',
          300: '#94b8ff',
          400: '#5a8fd4',
          500: '#1e3a5f',
          600: '#17304f',
          700: '#112640',
          800: '#0b1c30',
          900: '#061220',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    }
  },
  plugins: [],
}
