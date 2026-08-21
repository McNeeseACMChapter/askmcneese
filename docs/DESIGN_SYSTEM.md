# AskMcNeese Design System

The source of truth is `frontend/src/styles/variables.css`.  
`frontend/tailwind.config.js` maps those CSS variables into utilities.  
If the three disagree, **fix Tailwind and this document to match `variables.css`**.

**Product category:** institutional campus information and decision-support assistant.  
**Personality:** official, calm, intelligent, transparent, approachable — not loud, magical, or athletics-landing.

---

## Visual identity (contract)

Signature appearance:

- cool blue-white canvas
- highly readable white answer surfaces
- official Midnight Blue actions (`#002F87` via `--blue-800` / `--action-primary`)
- subtle blue borders
- one controlled Sunflower Gold active nav state (`#FFCE00`, ~5–8% of the UI)
- glass for chrome and composer only
- solid information content (answers, citations, forms, tables)
- visible sources and freshness; restrained motion

Gold marks **primary navigation identity** (active icon/label capsule). It is never ordinary body text, never warning, and never the default send button.

---

## Token roles

### Brand primitives

Official anchors:

| Primitive | Value | Role |
|---|---|---|
| `--blue-800` | `#002F87` | Official McNeese Midnight Blue |
| `--gold-300` | `#FFCE00` | Official McNeese Sunflower Gold |

Interface tones are derived around those anchors (`--blue-50`…`--blue-950`, `--gold-50`…`--gold-700`). Do not paint large areas with official gold. Neutrals are an independent scale — do not copy athletics-guide gray columns that accidentally reuse blue RGB.

### Brand roles (use these in UI)

- `--brand-800` / `--action-primary` — primary actions, institutional emphasis  
- `--brand-700` / `--text-link` — links and application blue  
- `--brand-900` / `--brand-950` — hover/pressed and text on gold  
- `--accent-gold` + `--text-on-gold` — active navigation capsule only  
- `--accent-gold-soft` / `--surface-accent-subtle` — rare soft gold wash  

### Surfaces

| Token | Use |
|---|---|
| `--canvas` | Page and chat background |
| `--canvas-elevated` | Welcome / large sections |
| `--surface` | Answers, cards, forms |
| `--surface-subtle` | Nested neutral regions |
| `--surface-hover` | Hover |
| `--surface-selected` | Selected history / nav items (blue-tinted, **not** gold) |
| `--surface-brand-subtle` | Important info cards, official citations |

Decorative page wash may use a weak blue radial only. No yellow gradient behind answer text.

### Text and borders

- `--text-primary` / `--text-secondary` / `--text-muted` / `--text-disabled` / `--text-inverse`
- `--text-link` / `--text-link-hover`
- `--border-default` / `--border-subtle` / `--border-interactive` / `--border-active`
- `--focus-ring` + `--focus-ring-outer` for dual-ring keyboard focus

### Interaction

- Primary: `--action-primary` (+ hover/pressed/text) — blue send and CTAs  
- Secondary: white + blue border (`--action-secondary-*`)  
- Accent: gold fill only when the action *is* identity (active nav), not routine submit  

### Semantic state

`--success`, `--warning`, `--danger`, `--info` (+ `*-soft`).  
Green means verified success — not “a citation exists.”  
Warning uses amber semantic tokens — never gold.

### Layout (unchanged roles)

| Token | Role |
|---|---|
| `--header-height` | Desktop sticky header |
| `--mobile-top-nav-height` | Phone top capsule |
| `--nav-rail-width` / `--sidebar-width` / `--sidebar-collapsed-width` | Shell widths |
| `--chat-max-width` / `--answer-reading-max` / `--composer-max-width` | Reading columns |

At **375 px and below**: chat max width 100%, sidebar `min(280px, 88vw)`, page gutter 16px.

---

## Glass (chrome only)

Three roles — prefer these names; legacy `glass-navigation` / `glass-interactive` map to chrome / control:

| Role | Use |
|---|---|
| **Chrome** (`--glass-chrome-*`) | Header, mobile capsule, sidebar chrome |
| **Control** (`--glass-control-*`) | Composer, dropdowns, floating menus |
| **Content** (`--glass-content-*`) | Rare overlays only — never normal answer prose |

Rules:

1. One component, one surface role.  
2. No raw hex in components — variables or Tailwind semantic utilities only.  
3. At most two simultaneous glass layers.  
4. Answer readability outranks glass aesthetics.  
5. Under `prefers-reduced-transparency: reduce`, glass backgrounds become solid and blur is `0`.

`GlassSurface` levels: `chrome` | `control` | `content` (plus legacy `navigation` | `interactive`).

---

## Component color contract (summary)

| Surface | Treatment |
|---|---|
| App canvas | `--canvas` + optional weak blue radial |
| Header / mobile nav | Glass chrome |
| Active primary nav | Gold fill + `--text-on-gold` on icon/label only |
| Selected conversation | `--surface-selected` (blue), not gold |
| Composer | Glass control; send = `--action-primary` |
| User message | `--surface-selected`, solid |
| Assistant answer | Solid `--surface` or transparent prose; structured details in cards |
| Official citation | `--surface-brand-subtle` |
| External citation | `--surface-subtle` |
| Caution / deadline card | `--warning-soft` + left border `--warning` |

---

## Dark theme

A `.dark { … }` block exists in `variables.css` and remaps surface/text/border/action/glass roles.  
Tailwind `darkMode: "class"` is enabled. Do not invent a second dark palette in components.

---

## Typography

Fonts load from Google Fonts in `frontend/index.html` (EB Garamond, Source Sans 3).

| Token | Use |
|---|---|
| `--assistant-answer-font` (serif) | Long assistant prose |
| `--answer-operational-font` / `--font-sans` | Cards, sources, controls |
| `--user-message-font` | User bubbles |

Answer body: `--answer-body-size` / `--answer-body-line-height` / `--answer-reading-max` (720px).

---

## Spacing, radius, shadows, z-index, motion

Unchanged structure: 4px spacing scale, radius sm→2xl, shadow xs→lg + focus, z-index base→splash, motion instant→emphasis with reduced-motion kill switch (`0ms`).

---

## Consistency rules (non-negotiable)

1. **One component, one surface role.**  
2. **No raw hex in components.**  
3. **≤ two glass layers** at once.  
4. **Gold ≠ body text, ≠ warning, ≠ default primary CTA.**  
5. **Hover, active, and selected are distinct.**  
6. **Color is never the only state indicator** (icons, labels, borders).  
7. **Ask / About / Updates / history / settings / mobile share the same role tokens.**  
8. **Trust signals are evidence labels**, not invented confidence percentages.

---

## Compatibility aliases

`variables.css` keeps `--color-*`, `--glass-nav-*`, `--composer-*`, and McNeese yellow aliases for older CSS. New work should prefer role tokens (`canvas`, `surface`, `action-primary`, `glass-chrome`, `danger`).
