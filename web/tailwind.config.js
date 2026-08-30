module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  safelist: [
    'bg-red-50', 'bg-red-500', 'text-red-600', 'border-red-200',
    'bg-amber-50', 'bg-amber-500', 'text-amber-600', 'border-amber-200',
    'bg-emerald-50', 'bg-emerald-500', 'text-emerald-600', 'border-emerald-200',
    'bg-slate-50', 'bg-slate-400', 'text-slate-600', 'border-slate-200',
  ],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      colors: {
        brand: {
          indigo: '#5B5BF6',
          'indigo-hover': '#4A4AE0',
          teal: '#00C9A7',
        },
        qc: {
          primary: '#5B5BF6',
          'primary-hover': '#4A4AE0',
          accent: '#00C9A7',
          red: '#D4537E',
          amber: '#EF9F27',
          green: '#00C9A7',
        },
      },
    },
  },
  plugins: [],
};
