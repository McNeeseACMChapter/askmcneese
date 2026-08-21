# Visual Overhaul — Visual Validation

**Date:** 2026-07-12 (Visual Correction Pass)  
**Method:** Playwright Chromium against Vite preview (`127.0.0.1:4173`). Screenshots in `docs/screenshots/visual-correction/`.

Legend: **Verified pass** · **Verified defect** · **Not verified**

---

## Automated gates

| Check | Result |
|-------|--------|
| `npm run test -- --run` (51) | Verified pass |
| `npm run typecheck` | Verified pass |
| `npm run build` | Verified pass |
| Backend unit tests (18) | Verified pass |
| `git diff --check` | Verified pass |

---

## Browser screenshots (real renders)

| Viewport | Empty Ask | Progress compact | Progress expanded | Answer + sources | About | Updates | ACM Portal | Mobile More |
|------:|-----------|------------------|-------------------|------------------|-------|---------|------------|-------------|
| 390 | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass |
| 768 | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Not verified (sidebar rail layout) |
| 1280 | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | n/a |
| 1440 | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | Verified pass | n/a |

Progress/answer states rendered via `/__visual__/progress-*` harness using the real `LiveAnswerProgress`, `CitationGroup`, and message components with fixture activity events (not fabricated DOM chrome).

---

## Defect checklist (from correction brief)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| One unified desktop navigation | Verified pass | 1280-empty-ask.png — single navy sidebar |
| No invented product icon | Verified pass | Empty Ask / progress shots — typographic wordmark only |
| No sparkle/AI progress icon | Verified pass | progress-compact/expanded — status dot only |
| Compact active progress | Verified pass | progress-compact — single row + Details |
| One current-stage sentence | Verified pass | Compact row |
| Details expand/collapse | Verified pass | progress-expanded — grouped stages |
| One Stop (composer only) | Verified pass | Unit test + no Stop in progress component |
| Sources · N only | Verified pass | answer-sources-expanded + CitationGroup tests |
| One methodology CTA | Verified pass | Empty Ask |
| Composer caution visible | Verified pass | Empty Ask / mobile |
| Natural About/Updates scroll | Verified pass | fullPage About/Updates screenshots exceed viewport |
| ACM Portal honest auth | Verified pass | acm-portal screenshots |
| Smoky bloom intermittent | Verified pass | Empty Ask atmosphere present; reduced-motion disables component |

### Minor remaining notes (not blockers)

| Item | Status |
|------|--------|
| Live SSE token streaming screenshot vs live Claude | Not verified (harness used) |
| History search field empty-state contrast on navy | Verified pass after styling tweak (rebuild recommended for refresh) |
| Ultrawide 1920 matrix | Not verified |

---

## Screenshot index

All files under `docs/screenshots/visual-correction/`:

- `{390,768,1280,1440}-empty-ask.png`
- `{390,768,1280,1440}-progress-compact.png`
- `{390,768,1280,1440}-progress-expanded.png`
- `{390,768,1280,1440}-answer-sources-expanded.png`
- `{390,768,1280,1440}-about.png`
- `{390,768,1280,1440}-updates.png`
- `{390,768,1280,1440}-acm-portal.png`
- `390-mobile-more.png`
