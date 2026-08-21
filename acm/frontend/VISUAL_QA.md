# Visual QA — Corrective pass critique loops

**Date:** 2026-07-18  
**Artifacts:** `artifacts/visual/`  
**Command:** `npm run build && npm run preview` then `npm run capture:viewports`

---

## Loop 1 — Shell and hierarchy

| Defect | Screenshot | Correction | Result |
|--------|------------|------------|--------|
| Dual yellow banners (action + prototype) | Prior wireframe | Removed; Prototype badge + toast | `home-1440x900.png` — badge only |
| Duplicate page title in header + body | Prior | Header breadcrumb + tools; one H1 in content | Confirmed on Home/My Work/Meetings |
| Breadcrumb also under H1 | `meetings-1440x900.png` (pre-fix) | Removed `page-chrome__crumb` | Single hierarchy |
| Heavy gray active nav | Prior | Translucent + 2px gold rail | Visible on Home/My Work/Meetings |
| Mobile More blocked by sticky header | Capture failure | Mobile nav `z-overlay`; header `top` offset | Re-capture shell states |

---

## Loop 2 — Domain visualization

| Defect | Screenshot | Correction | Result |
|--------|------------|------------|--------|
| Meetings empty shell | Prior | FullCalendar + lifecycle steppers | `meetings-1440x900.png` |
| Reports empty shell | Prior | ECharts + accessible table | `reports-1440x900.png` |
| Home ≡ My Work | Prior | Home metrics/agenda/portfolio vs My Work tabs | Distinct in `home-*` vs `my-work-*` |
| Projects text-only | Prior | Table/board/timeline + progress/trend | `projects-1440x900.png` |
| Governance text-only | Prior | Read-only React Flow authority map | `governance-1440x900.png` |

---

## Loop 3 — Interaction state

| Defect | Screenshot | Correction | Result |
|--------|------------|------------|--------|
| Approve → permanent banner | Prior | Radix toast; fixture mutation updates dependents | Vitest + Approval page |
| Duplicate primary actions | `meetings-1440x900.png` | Primary action only in route header | Fixed Meetings/Events/Projects |
| Missing pending labels | Approval | Approving… / pending evidence attach | Approval detail |

---

## Loop 4 — Responsive and accessibility

| Defect | Screenshot | Correction | Result |
|--------|------------|------------|--------|
| Dual scroll / hit conflict mobile | Capture error | Capsule above header; offset sticky header | Shell CSS fix |
| Chart without table alt | Reports | Accessible table under chart | `reports-*` |
| Touch targets | Mobile captures | Capsule items ≥48px | `*-375x812.png` |

**Automated axe:** Storybook addon-a11y installed; full Playwright+axe CI suite not gated this pass.

---

## Remaining visual issues (honest)

1. Sidebar still scrolls for full module list at ordinary heights (Reports may sit below fold).
2. Several modules still share metric-strip + surface grammar; domain depth varies.
3. Toast / pending / failed mutation screenshots not isolated as dedicated captures.
4. Shared list→detail motion not fully implemented.
5. Storybook covers Button, StatusBadge, ProgressRing, LifecycleStepper — not every page pattern.
