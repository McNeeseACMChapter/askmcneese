# AskMcNeese Design System

The source of truth is `frontend/src/styles/variables.css`. `frontend/tailwind.config.js` maps these CSS variables into utilities so components do not need to repeat raw values.

## Token roles

### Layout

| Token | Value | Role |
|---|---:|---|
| `--header-height` | `56px` | Sticky application header. |
| `--nav-rail-width` | `64px` | Desktop primary navigation rail. |
| `--sidebar-width` | `280px` | Expanded conversation sidebar. |
| `--sidebar-collapsed-width` | `64px` | Compact conversation sidebar. |
| `--composer-min-height` | `88px` | Composer reservation. |
| `--chat-max-width` | `760px` | Main reading/composer column. |
| `--message-max-width` | `85%` | Message bubble maximum width. |

At 375 px and below, the chat maximum becomes 100% and the sidebar is limited to `min(280px, 88vw)`.

### Brand and accent

- `--brand-950`, `900`, `800`, `700`, and `600` are the dark-to-light McNeese blue range used for navigation, actions, links, and emphasis.
- `--brand-100` and `--brand-50` are pale selected/subtle backgrounds.
- `--accent-gold` (`#f2b134`) is the McNeese accent; `--accent-gold-soft` is its quiet background.

Gold is an accent, not a default text color or large-area background. Blue communicates primary product identity and action.

### Surfaces

- `--canvas` is the page/chat background.
- `--surface` is the primary card, panel, input, and header surface.
- `--surface-subtle` separates nested or low-emphasis regions.
- `--surface-hover` is the neutral interactive hover state.
- `--surface-selected` marks selected navigation/history items.

### Text and borders

- `--text-primary` is body and heading text.
- `--text-secondary` is supporting copy.
- `--text-muted` is metadata and tertiary labels.
- `--text-disabled` is unavailable control text.
- `--text-inverse` is text on dark brand surfaces.
- `--border-default` separates ordinary surfaces.
- `--border-strong` is available for stronger boundaries.
- `--focus-ring` is the global keyboard-focus color.

### Semantic state

`--success`, `--warning`, and `--danger` represent status, caution, and failure. Each has a matching soft background. Semantic colors should describe state, not decorate neutral content.

### Compatibility aliases

`variables.css` retains `--color-*` aliases for existing component/Tailwind names. They resolve to the current brand, surface, text, border, and semantic tokens. New work should prefer role-based current tokens while aliases remain available during migration.

## Typography

The application loads **EB Garamond** and **Source Sans 3** from Google Fonts in `frontend/index.html`, with system fallbacks in the CSS variables.

### EB Garamond — editorial

Use `--font-serif`, Tailwind `font-serif`, or `.font-editorial` for:

- answer prose and markdown headings;
- prominent page/panel headings;
- answer titles and summaries;
- values or narrative content intended for sustained reading;
- display/welcome typography.

The `.type-display` utility uses responsive 1.75–2.25 rem serif type with tight leading. `.type-prose` and `.prose-answer` use responsive 1.05–1.125 rem serif type with `1.75` line height.

### Source Sans 3 — interface

Use `--font-sans`, Tailwind `font-sans`, or `.type-ui` for:

- buttons, inputs, selects, navigation, tabs, and menus;
- labels, badges, status messages, metadata, timestamps, and helper text;
- compact data tables and operational content;
- the application body default.

In short: serif communicates “read this answer”; sans communicates “use or understand this interface.” Do not use serif for dense controls or small uppercase labels, and do not default long answer prose to sans.

### Scale and leading

The scale is `xs` 0.75 rem, `sm` 0.875 rem, `base` 1 rem, `lg` 1.125 rem, `xl` 1.25 rem, `2xl` 1.5 rem, and `3xl` 1.875 rem. Leading tokens are `tight` 1.25, `snug` 1.375, `normal` 1.5, `relaxed` 1.65, and `prose` 1.75.

Monospace (`--font-mono`) is reserved for code.

## Spacing

Spacing follows a 4 px base:

| Token | Value |
|---|---:|
| `--space-1` | 4 px |
| `--space-2` | 8 px |
| `--space-3` | 12 px |
| `--space-4` | 16 px |
| `--space-5` | 20 px |
| `--space-6` | 24 px |
| `--space-8` | 32 px |
| `--space-10` | 40 px |
| `--space-12` | 48 px |
| `--space-16` | 64 px |

Prefer this scale for component padding and gaps. Use smaller values within controls, 16–24 px for cards/panels, and larger values for page-level separation.

## Radius

- `--radius-sm` 6 px: code chips and compact details.
- `--radius-md` 8 px: standard controls.
- `--radius-lg` 12 px: cards and panels.
- `--radius-xl` 16 px and `--radius-2xl` 20 px: prominent answer/composer surfaces.
- `--radius-full` 9999 px: status dots, pills, and circular elements.

Tailwind also defines 18 px `bubble` and 4 px `bubble-tail` radii for chat shapes.

## Shadows

- `--shadow-xs`: minimal separation for small brand/icon surfaces.
- `--shadow-sm` (`shadow-soft`): quiet cards such as activity and answer surfaces.
- `--shadow-md` (`shadow-card`): controls and elevated cards such as the composer/menu.
- `--shadow-lg` (`shadow-float`): mobile drawers and floating overlays.
- `--shadow-focus`: optional three-pixel focus halo; the global focus style also uses a two-pixel outline.

Use borders before increasing elevation. Shadows communicate layer, not importance.

## Z-index

| Token | Value | Intended layer |
|---|---:|---|
| `--z-base` | 0 | Normal content |
| `--z-dropdown` | 100 | Menus |
| `--z-sticky` | 200 | Sticky content |
| `--z-header` | 300 | Header and mobile nav |
| `--z-overlay` | 400 | Drawer backdrop/sidebar |
| `--z-modal` | 500 | Modal dialogs |
| `--z-toast` | 600 | Notifications |
| `--z-splash` | 1000 | Startup splash |

Use the named layer rather than arbitrary z-index values.

## Motion

Durations are 50 ms (`instant`), 150 ms (`fast`), 250 ms (`normal`), and 400 ms (`slow`), with default, out, and spring easing tokens. Under `prefers-reduced-motion: reduce`, all duration variables become 0 ms. New motion must inherit that behavior.
