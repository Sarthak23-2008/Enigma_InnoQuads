/** SafeBite design tokens. Risk colours are always paired with an icon + word (never colour alone). */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: 'rgb(var(--paper) / <alpha-value>)',
        surface: 'rgb(var(--surface) / <alpha-value>)',
        ink: 'rgb(var(--ink) / <alpha-value>)',
        muted: 'rgb(var(--muted) / <alpha-value>)',
        line: 'rgb(var(--line) / <alpha-value>)',
        brand: { DEFAULT: 'rgb(var(--brand) / <alpha-value>)', soft: 'rgb(var(--brand-soft) / <alpha-value>)', ink: 'rgb(var(--brand-ink) / <alpha-value>)' },
        low: { DEFAULT: 'rgb(var(--low) / <alpha-value>)', soft: 'rgb(var(--low-soft) / <alpha-value>)' },
        caution: { DEFAULT: 'rgb(var(--caution) / <alpha-value>)', soft: 'rgb(var(--caution-soft) / <alpha-value>)' },
        high: { DEFAULT: 'rgb(var(--high) / <alpha-value>)', soft: 'rgb(var(--high-soft) / <alpha-value>)' },
      },
      fontFamily: {
        sans: ['"Archivo Variable"', 'Archivo', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: { panel: '14px' },
      boxShadow: { lift: '0 1px 2px rgb(20 35 42 / 0.06), 0 8px 24px -12px rgb(20 35 42 / 0.18)' },
      maxWidth: { page: '72rem' },
    },
  },
  plugins: [],
}
