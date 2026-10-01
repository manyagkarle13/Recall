/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#f8fafc',
        surface: '#ffffff',
        'surface-elevated': '#f1f5f9',
        border: '#e2e8f0',
        accent: {
          DEFAULT: '#7c3aed',
          hover: '#6d28d9',
          light: '#8b5cf6',
          muted: 'rgba(124, 58, 237, 0.08)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
