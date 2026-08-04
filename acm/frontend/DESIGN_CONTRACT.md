# ACM Panel — Design Contract

**North star:** *Calm institutional operations.*

This document is the authoritative token and usage contract for ACM Panel UI. Values align with `src/styles/tokens.css` (v0.1.0-prototype snapshot). When code and this file diverge, update both in the same change.

---

## Brand colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--brand-950` | `#071f46` | Sidebar solid fallback, pressed primary, text-on-gold |
| `--brand-900` | `#0b2c5e` | Primary hover |
| `--brand-800` | `#0c3c7a` | **Primary button default** |
| `--brand-700` | `#0e4c92` | Links, active borders, info |
| `--brand-600` | `#1261a6` | Charts, secondary emphasis |
| `--brand-100` | `#ddeaf7` | Selected row tint |
| `--brand-50` | `#f2f7fc` | Approval surface tint |

### Gold (scarce)

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent-gold` | `#f2b134` | Sidebar active accent, role identity line, rare highlights |
| `--accent-gold-soft` | `#fff6df` | Soft highlight backgrounds |
| `--accent-gold-text` | `#6a4e00` | Text on gold-soft |
| `--text-on-gold` | `#071f46` | Text on solid gold (avoid large gold fills) |

**Gold scarcity rule:** Gold appears in ≤5% of any viewport. Never on primary buttons, never as page background, never on body text.

---

## Neutrals & surfaces

| Token | Hex | Usage |
|-------|-----|-------|
| `--canvas` | `#f0f3f8` | App background |
| `--canvas-elevated` | `#f7f9fc` | Subtle lift behind main content |
| `--surface` | `#ffffff` | Cards, tables, panels |
| `--surface-subtle` | `#eef3f8` | Alternating rows, inset areas |
| `--surface-hover` | `#e5edf6` | Row / control hover |
| `--text-primary` | `#172033` | Headings, primary labels |
| `--text-secondary` | `#425168` | Supporting text, table cells |
| `--text-muted` | `#738096` | Timestamps, placeholders, meta |
| `--text-disabled` | `#a9b4c3` | Disabled controls |
| `--text-inverse` | `#ffffff` | On navy / dark sidebar |

### Semantic

| Role | Default | Soft background |
|------|---------|-----------------|
| Success | `#1f6f4a` | `#eaf6f0` |
| Warning | `#8a5a00` | `#fff5d6` |
| Danger | `#a63333` | `#fff0f0` |
| Info | `#0e4c92` | `#eaf2fb` |

---

## Typography

| Role | Family | Examples |
|------|--------|----------|
| **Operational UI** | Source Sans 3 | Tables, forms, buttons, nav labels, body copy, metrics |
| **Identity / editorial** | EB Garamond | Panel wordmark, page titles, governance charter excerpts, election notices |

### Rules

- **EB Garamond only** for identity, titles, and long-form editorial — never for table data, form labels, or button text.
- **Source Sans 3** for all operational UI.
- Page title: `--type-page-title` (clamp 1.75rem → 2.35rem), EB Garamond.
- Section title: `--type-section-title` (clamp 1.35rem → 1.75rem), Source Sans 3 semibold.
- Body: `--text-base` (16px) default; `--text-sm` (14px) for dense tables and meta.
- Mono: system monospace for IDs, audit hashes, API keys — sparingly.

---

## Spacing & layout

- **Base unit:** 4px. Use token steps only (`--space-1` through `--space-16`).
- **Page gutter:** 40px (1440+), 32px (1024–1439), 24px (768–1023), 16px (<768).
- **Sidebar:** 280px expanded / 76px collapsed; row height 44px; radius 12px.
- **Route header:** 64px.
- **List row:** 54px default for collections.
- **Inspector rail:** 280px when present.
- **Hit target:** 44px minimum.

---

## Surface levels (3 glass tiers)

| Level | Token prefix | Use |
|-------|--------------|-----|
| **Nav glass** | `--glass-nav-*` | Top bars, mobile capsule |
| **Content glass** | `--glass-content-*` | Page shells, table containers |
| **Interactive glass** | `--glass-interactive-*` | Dropdowns, popovers, command surfaces |

Fallbacks are opaque white/navy when blur is reduced or unsupported.

---

## Icons & motion

| Property | Value |
|----------|-------|
| Icon set | Lucide |
| Size | 18px (`--icon-size`) |
| Stroke | 1.75 (`--icon-stroke`) |

| Duration | Token | Use |
|----------|-------|-----|
| 100ms | `--motion-instant` | Opacity toggles |
| 160ms | `--motion-fast` | Hover, chip select |
| 220ms | `--motion-standard` | Expand/collapse |
| 280ms | `--motion-panel` | Inspector, sheets |

No spring/bounce on data tables or approval flows.

---

## Buttons & actions

| Variant | Style |
|---------|-------|
| **Primary** | Navy (`--action-primary` / brand-800); white text — **not gold** |
| **Secondary** | Surface + border; navy text |
| **Ghost** | Transparent; navy text; hover surface-subtle |
| **Destructive** | Danger on soft background; confirm on irreversible actions |

Gold is never a button fill. Link style uses `--text-link` (brand-700).

---

## Borders, focus, shadows

- Default border: `#cbd6e3`; strong: `#a9b4c3`; subtle: 10% brand-800 mix.
- Focus ring: `#2c69b7` with 3px shadow mix; outer ring white on dark backgrounds.
- Shadows: xs–lg scale; prefer elevation via surface level, not stacked shadows.

---

## Anti-patterns (do not ship)

1. Gold primary buttons or gold page backgrounds.
2. EB Garamond in tables, forms, or navigation labels.
3. Card mosaic layouts where a row list is appropriate.
4. Bottom navigation bar on mobile.
5. Chat composer or message bubbles for operational workflows.
6. 820px chat-width constraint on ACM pages.
7. Conversation history replacing module navigation.
8. Generic bordered secondary-card grids with no scan hierarchy.
9. Icon sizes or stroke weights other than 18px / 1.75.
10. Decorative glass on every element (max 3 levels, purposeful placement).
11. Animations that block or delay approval decisions.
12. Hiding actions the user lacks permission for **without** also enforcing server-side (UI hide ≠ security).

---

## Related documents

- Audit & rationale: [`DESIGN_AUDIT.md`](./DESIGN_AUDIT.md)
- Navigation structure: [`INFORMATION_ARCHITECTURE.md`](./INFORMATION_ARCHITECTURE.md)
- Page templates: [`PAGE_PATTERNS.md`](./PAGE_PATTERNS.md)
- Breakpoints: [`RESPONSIVE_RULES.md`](./RESPONSIVE_RULES.md)
- QA checklist: [`VISUAL_QA.md`](./VISUAL_QA.md)
