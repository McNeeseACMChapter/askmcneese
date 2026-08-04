# AskMcNeese Logo Usage Rules

Source of truth: `AskMcNeese_ACM_Authentic_Brand_Guide.psd`, the section labeled **03 / Approved Artwork**.

## Locked rule

Use only the exported files in `frontend/public/assets/brand/`. Do not redraw, regenerate, recolor, stretch, rotate, separate, or rebuild the M, brackets, dots, speech field, wordmark, divider, or ACM label.

## Choose the right asset

- **Website and desktop navigation:** `askmcneese-logo-horizontal.png`. Recommended width: 180 px or larger; absolute minimum: 150 px.
- **Hero, presentation, report, or launch surface:** `askmcneese-logo-stacked.png`.
- **Mobile navigation and compact assistant identity:** `askmcneese-mark.png` beside a plain-text interface title. Do not squeeze the horizontal signature into a narrow header.
- **Browser tabs, shortcuts, and app tiles:** `favicon-16.png`, `favicon-32.png`, `favicon-48.png`, `favicon-192.png`, `favicon.ico`, or `askmcneese-app-icon.png`.
- **Black-and-white output only:** `askmcneese-logo-monochrome.png`.

## Placement

1. Scale proportionally from a corner. Never set width and height independently.
2. Keep at least one conversation-dot diameter of clear space around the mark. More space is preferred on covers and hero surfaces.
3. Use the color logo on white or a very light neutral surface.
4. On dark, photographic, or busy surfaces, place the full logo inside a white holding panel. Do not add glow, tint, gradients, or color overlays to the artwork.
5. Never place controls, labels, or decorative elements inside the logo clear space.
6. Keep the logo quiet: one primary brand signature per surface. Repeated marks are allowed only where they identify distinct assistant messages or browser/app metadata.
7. The word AskMcNeese may remain in body copy and accessible labels; the logo asset replaces improvised visual wordmarks, not ordinary language.

## Implementation

Use `BrandLogo` from `frontend/src/components/brand/BrandLogo.tsx` instead of hardcoding asset paths. This keeps dimensions, loading behavior, and approved variants consistent.
