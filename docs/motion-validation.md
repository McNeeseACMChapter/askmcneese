# Motion — Validation

**Date:** 2026-07-12  
**Method:** Playwright Chromium against Vite preview (`127.0.0.1:4173`). Screenshots in `docs/screenshots/motion/`.

## Commands

| Command | Result |
|---------|--------|
| `npm run test` | Pass — 64 tests |
| `npm run typecheck` | Pass |
| `npm run build` | Pass |
| `python -m unittest discover -s tests/unit -p "test_*.py"` (from `backend/`) | Pass — 18 tests |
| `git diff --check` | Pass |

## Route matrix (390 / 768 / 1280 / 1440)

| Route | Evidence | Result |
|-------|----------|--------|
| `/about` | `*-about.png` | Verified pass |
| `/about/methodology` | `*-methodology.png` + before/mid/final @1280/1440 | Verified pass |
| `/about/team` | `*-team.png` + reduced-motion | Verified pass |
| `/about/advisor` | `*-advisor.png` | Verified pass |
| `/about/roadmap` | `*-roadmap.png` + initial/mid | Verified pass |
| `/updates` | `*-updates.png` | Verified pass |
| `/status` | `*-status.png` | Verified pass |
| `/settings` | `*-settings.png` | Verified pass |
| `/feedback` | `*-feedback.png` | Verified pass |
| `/acm/login` | `*-acm-login.png` | Verified pass |

## Behavior checks

| Check | Result | Notes |
|-------|--------|-------|
| Native scrolling | Verified pass | No Lenis / wheel hijack |
| No scroll traps | Verified pass | Footer reachable in fullPage captures |
| No blank pinned gaps | Verified pass | Sticky visual only; no multi-VH pin |
| Methodology mobile stacked | Verified pass | `390-methodology.png` |
| Methodology mid/final stages | Verified pass | `1280-methodology-mid/final.png` |
| Roadmap mid-progress | Verified pass | `1280-roadmap-mid.png` |
| Reduced motion content visible | Verified pass | `1280-*-reduced-motion.png` |
| Horizontal overflow | Verified pass | Captures within viewport width |
| Sticky header mid fullPage | Not verified as defect | Playwright fullPage may duplicate sticky chrome; live sticky header expected |
| Live Ask SSE motion regression | Not verified | Out of scope; no Ask lifecycle code changes |
| Lottie playback | Not verified | Asset blocked by design |

## Accessibility

| Check | Result |
|-------|--------|
| `prefers-reduced-motion` disables scrub/pin/stagger/number tween | Verified pass (code + reduced-motion screenshots) |
| Methodology steps in semantic order without animation | Verified pass (unit + DOM) |
| AnimatedMetric announces final value | Verified pass (unit) |
| AppIcon / no banned icon libs | Verified pass (unit) |

## Criticism loop

Recorded in `docs/motion-change-log.md` — excess TextReveal stacking removed; page pin avoided; mobile pin removed; ownership wrappers enforced.
