/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        mcneese: {
          blue: "#00549F",
          gold: "#F2A900",
          dark: "#003B6F",
          light: "#4A9FD4",
        },
        surface: "var(--color-surface)",
        background: "var(--color-background)",
        elevated: "var(--color-background-elevated)",
        border: "var(--color-border)",
        "border-focus": "var(--color-border-focus)",
        "text-primary": "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        "text-muted": "var(--color-text-muted)",
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'soft': 'var(--shadow-sm)',
        'card': 'var(--shadow-md)',
        'float': 'var(--shadow-lg)',
      },
      borderRadius: {
        'bubble': '18px',
        'bubble-tail': '4px',
      },
      spacing: {
        'safe': 'env(safe-area-inset-bottom, 0px)',
        'sidebar': 'var(--sidebar-width)',
      },
      transitionDuration: {
        'fast': 'var(--duration-fast)',
        'normal': 'var(--duration-normal)',
        'slow': 'var(--duration-slow)',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'dot-bounce': 'dotBounce 1.4s ease-in-out infinite',
      },
      keyframes: {
        dotBounce: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      maxWidth: {
        'chat': '768px',
        'message': '85%',
      },
    },
  },
  plugins: [],
};
