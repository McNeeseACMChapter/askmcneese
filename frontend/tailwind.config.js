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
          dark: "#003D73",
          light: "#4A9FD4",
        },
        surface: "var(--color-surface)",
        "surface-raised": "var(--color-surface-raised)",
        "surface-sunken": "var(--color-surface-sunken)",
        background: "var(--color-background)",
        "bg-secondary": "var(--color-background-secondary)",
        "bg-tertiary": "var(--color-background-tertiary)",
        elevated: "var(--color-background-elevated)",
        border: "var(--color-border)",
        "border-subtle": "var(--color-border-subtle)",
        "border-focus": "var(--color-border-focus)",
        "text-primary": "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        "text-muted": "var(--color-text-muted)",
        "primary-subtle": "var(--color-primary-subtle)",
        "accent-subtle": "var(--color-accent-subtle)",
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        error: "var(--color-error)",
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'xs': 'var(--shadow-xs)',
        'soft': 'var(--shadow-sm)',
        'card': 'var(--shadow-md)',
        'float': 'var(--shadow-lg)',
        'focus': 'var(--shadow-focus)',
      },
      borderRadius: {
        'bubble': '18px',
        'bubble-tail': '4px',
      },
      height: {
        'header': 'var(--header-height)',
        'screen-safe': '100dvh',
      },
      minHeight: {
        'composer': 'var(--composer-min-height)',
      },
      width: {
        'sidebar': 'var(--sidebar-width)',
      },
      maxWidth: {
        'chat': 'var(--chat-max-width)',
        'message': 'var(--message-max-width)',
      },
      spacing: {
        'safe': 'env(safe-area-inset-bottom, 0px)',
        'sidebar': 'var(--sidebar-width)',
        'header': 'var(--header-height)',
      },
      transitionDuration: {
        'instant': 'var(--duration-instant)',
        'fast': 'var(--duration-fast)',
        'normal': 'var(--duration-normal)',
        'slow': 'var(--duration-slow)',
      },
      zIndex: {
        'dropdown': 'var(--z-dropdown)',
        'sticky': 'var(--z-sticky)',
        'header': 'var(--z-header)',
        'overlay': 'var(--z-overlay)',
        'modal': 'var(--z-modal)',
        'splash': 'var(--z-splash)',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'dot-bounce': 'dotBounce 1.4s ease-in-out infinite',
        'glow': 'glow 4s ease-in-out infinite',
      },
      keyframes: {
        dotBounce: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        glow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(1.05)' },
        },
      },
    },
  },
  plugins: [],
};
