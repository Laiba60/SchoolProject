/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#1e3a8a', dark: '#14275f', soft: '#e8ecf8' },
        gold: { DEFAULT: '#fbbf24', dark: '#b7860b' },
        ink: '#14213d',
        paper: '#f6f7fb',
        line: '#dfe3ee',
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['"Source Sans 3"', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
