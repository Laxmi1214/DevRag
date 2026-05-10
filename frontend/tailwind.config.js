/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#111827',
        panel: '#f8fafc',
        brand: '#2563eb',
      },
    },
  },
  plugins: [],
};
