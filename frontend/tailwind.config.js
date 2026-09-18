/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        railnavy: {
          950: '#070C18',
          900: '#0B132B',
          850: '#0F172A',
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
          100: '#F1F5F9',
          50: '#F8FAFC',
        },
        railblue: {
          900: '#1E3A8A',
          800: '#1E40AF',
          700: '#1D4ED8',
          600: '#2563EB',
          500: '#3B82F6',
          400: '#60A5FA',
          100: '#DBEAFE',
          50: '#EFF6FF',
        },
        railcyan: {
          600: '#0284C7',
          500: '#0EA5E9',
          100: '#E0F2FE',
        },
        railrisk: {
          safe: '#059669',
          safebg: '#ECFDF5',
          safeborder: '#A7F3D0',
          risk: '#D97706',
          riskbg: '#FFFBEB',
          riskborder: '#FDE68A',
          missed: '#DC2626',
          missedbg: '#FEF2F2',
          missedborder: '#FECACA',
          info: '#2563EB',
          infobg: '#EFF6FF',
          infoborder: '#BFDBFE',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace']
      }
    },
  },
  plugins: [],
}
