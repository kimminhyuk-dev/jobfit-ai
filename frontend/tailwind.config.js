/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Pretendard', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'system-ui', 'sans-serif'],
        mono: ['Inter', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Modern palette (사용자 화면)
        m: {
          bg: '#fafafa',
          surface: '#ffffff',
          'surface-alt': '#f5f5f5',
          border: '#eaeaea',
          'border-strong': '#d4d4d4',
          text: '#0a0a0a',
          muted: '#525252',
          subtle: '#a3a3a3',
          primary: '#1d4ed8',
          'primary-hover': '#1e40af',
          'primary-soft': '#eef4ff',
          success: '#15803d',
          'success-soft': '#f0fdf4',
          warn: '#b45309',
          'warn-soft': '#fffbeb',
          danger: '#b91c1c',
          'danger-soft': '#fef2f2',
        },
        // Classic palette (관리자 화면)
        c: {
          bg: '#f6f8fb',
          surface: '#ffffff',
          'surface-alt': '#f1f5f9',
          border: '#e2e8f0',
          'border-strong': '#cbd5e1',
          text: '#0f172a',
          muted: '#475569',
          subtle: '#94a3b8',
          primary: '#2563eb',
          'primary-hover': '#1d4ed8',
          'primary-soft': '#eff6ff',
          success: '#16a34a',
          'success-soft': '#f0fdf4',
          warn: '#d97706',
          'warn-soft': '#fffbeb',
          danger: '#dc2626',
          'danger-soft': '#fef2f2',
        },
      },
    },
  },
  plugins: [],
};
