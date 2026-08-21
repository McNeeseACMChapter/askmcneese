/** @type {import('tailwindcss').Config} */
/**
 * Maps ACM Panel tokens from src/styles/tokens.css.
 * tokens.css is the versioned design contract snapshot.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          950: "var(--brand-950)",
          900: "var(--brand-900)",
          800: "var(--brand-800)",
          700: "var(--brand-700)",
          600: "var(--brand-600)",
          100: "var(--brand-100)",
          50: "var(--brand-50)",
        },
        accent: {
          gold: "var(--accent-gold)",
          "gold-soft": "var(--accent-gold-soft)",
          "gold-text": "var(--accent-gold-text)",
        },
        canvas: "var(--canvas)",
        "canvas-elevated": "var(--canvas-elevated)",
        surface: "var(--surface)",
        "surface-subtle": "var(--surface-subtle)",
        "surface-hover": "var(--surface-hover)",
        "surface-selected": "var(--surface-selected)",
        "text-primary": "var(--text-primary)",
        "text-secondary": "var(--text-secondary)",
        "text-muted": "var(--text-muted)",
        "text-inverse": "var(--text-inverse)",
        success: "var(--success)",
        "success-soft": "var(--success-soft)",
        warning: "var(--warning)",
        "warning-soft": "var(--warning-soft)",
        danger: "var(--danger)",
        "danger-soft": "var(--danger-soft)",
        info: "var(--info)",
        "info-soft": "var(--info-soft)",
        action: {
          primary: "var(--action-primary)",
          "primary-hover": "var(--action-primary-hover)",
          "primary-text": "var(--action-primary-text)",
        },
      },
      fontFamily: {
        ui: ["var(--font-ui)"],
        editorial: ["var(--font-editorial)"],
        sans: ["var(--font-ui)"],
        serif: ["var(--font-editorial)"],
      },
      boxShadow: {
        xs: "var(--shadow-xs)",
        soft: "var(--shadow-sm)",
        card: "var(--shadow-md)",
        float: "var(--shadow-lg)",
        focus: "var(--shadow-focus)",
        glass: "var(--glass-shadow)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        10: "var(--space-10)",
        12: "var(--space-12)",
        16: "var(--space-16)",
      },
      maxWidth: {
        collection: "var(--page-collection-max)",
        detail: "var(--page-detail-max)",
        editorial: "var(--page-editorial-max)",
        approval: "var(--page-approval-max)",
      },
      width: {
        sidebar: "var(--sidebar-expanded)",
        "sidebar-collapsed": "var(--sidebar-collapsed)",
        inspector: "var(--inspector-width)",
      },
      height: {
        header: "var(--route-header-height)",
        row: "var(--list-row-height)",
      },
      minHeight: {
        hit: "var(--hit-target)",
      },
      transitionDuration: {
        fast: "var(--motion-fast)",
        panel: "var(--motion-panel)",
        title: "var(--motion-title)",
      },
    },
  },
  plugins: [],
};
