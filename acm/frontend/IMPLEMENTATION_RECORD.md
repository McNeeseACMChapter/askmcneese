# ACM Panel — Corrective implementation record

**Date:** 2026-07-18  
**Pass:** Corrective visual + interaction rebuild  
**Boundary:** `askmcneese/acm/` only

---

## 1. Why the prior implementation failed

It copied AskMcNeese colors, fonts, rounded surfaces, and sidebar, then poured text into identical white cards. It never designed how chapter data becomes a decision interface. Permanent yellow success banners and navigable empty shells made the product feel like a polished wireframe.

See [`CORRECTIVE_VISUAL_AUDIT.md`](./CORRECTIVE_VISUAL_AUDIT.md).

---

## 2. Shell corrections

| Target | Result |
|--------|--------|
| Sidebar 256 / 72 | Token-driven expanded/collapsed |
| Header ~60px | Route header height token |
| Active nav | Translucent surface + 2px gold indicator (not opaque gray slab) |
| Scrollbar | Thin styled scrollbar on sidebar nav |
| Profile | Radix dropdown (role, term, profile, fixtures, sign out) |
| Prototype | Compact badge + popover (fixture explain + reset) |
| Action feedback | Radix toast — does not persist across routes |
| Mobile | Top capsule; More sheet; capsule above sticky header (z-index fix) |
| Hierarchy | Header breadcrumb + tools; one H1 + purpose in content |

---

## 3. Route architecture

`src/routes/manifest.ts` is the source of truth for path, id, nav group, label, breadcrumb, purpose, layout, width, density, permissions, primary action, mobile exposure.

Generates: sidebar, mobile primary/more, route header primary action, page width, purpose copy.

URL search params used for Projects view/filter where applicable.

---

## 4. Data-to-visual pipeline

```
Route → manifest → fixture repository → domain records
  → page selectors → viz components (metric, sparkline, progress, stepper, chart, flow, calendar)
  → mutation → pending → confirmed/failed → toast + dependent views + audit
```

Pages do not mutate raw arrays ad hoc; approvals go through `repository.decideApproval` + TanStack Query mutations.

---

## 5. Action-state architecture

- IDLE → PENDING (button labels / disabled) → CONFIRMED (toast + fixture updates) or FAILED (toast)
- Optimistic paths exist in repository design; full rollback catalog still partial
- Dependent updates on approve: approval status, work items, projects (when applicable), history, audit stream

---

## 6. Module-specific visualizations

| Module | Visual model |
|--------|----------------|
| Home | Command metrics, attention queue, sparkline, agenda, decisions, portfolio health |
| My Work | Now / Upcoming / Waiting / Completed tabs + workload sparkline |
| Projects | TanStack Table + board + timeline; progress, health, trend |
| Project detail | Delivery cockpit tabs (overview/activity/evidence/decisions/access) |
| Meetings | FullCalendar + lifecycle steppers + quorum + agenda progress |
| Events | Readiness rings / checklists |
| Members | Directory + avatars/initials |
| Governance | Quorum ring + read-only React Flow authority map |
| SGA | Funding pipeline |
| Finance | Budget vs actual / variance |
| Communications | Editorial pipeline |
| Documents | Library / classification |
| Reports | ECharts + accessible data table |
| Notifications | Unread/read stream |
| Audit | Dense event rows |
| Admin | Permission / fixture admin surface |

---

## 7. Routes fully meaningful (no placeholder shells)

Home · My Work · Projects · Project detail · Meetings · Events · Members · Governance · SGA · Finance · Communications · Documents · Reports · Notifications · Administration · Audit · Profile · Approvals · Login · Fixture gallery / state fixtures

**Explicit confirmation: no active navigation route is a placeholder shell.**

---

## 8. Dependencies added

TanStack Query, TanStack Table, Radix (toast, tooltip, dropdown, dialog, popover, tabs, alert-dialog), ECharts, FullCalendar, React Flow (`@xyflow/react`), clsx, Storybook 10 (+ docs, a11y).

---

## 9. Storybook results

- Config: `.storybook/`
- Stories: Button, StatusBadge, ProgressRing, LifecycleStepper (default/pending/disabled/empty variants as applicable)
- Build: `npm run build-storybook` → `artifacts/storybook/`
- Interaction play tests and full page-pattern catalog: **incomplete**

---

## 10. Playwright visual results

- Script: `scripts/capture-viewports.mjs`
- Outputs: `artifacts/visual/` (~110 PNGs across 6 viewports × major routes)
- Critique loops: [`VISUAL_QA.md`](./VISUAL_QA.md)
- Pixel baseline CI compare: **not gated**

---

## 11. Accessibility results

- Radix overlays for toast/menu/tooltip/popover
- Chart + tabular alternative on Reports
- Focus-visible styling retained
- Storybook a11y addon available
- Full Playwright+axe automation + keyboard regression suite: **not complete**
- Manual review still required for color-only meaning and 200% zoom

---

## 12. Remaining defects / limitations

1. Shared element list→detail transitions not fully wired.
2. Mutation undo toasts only when reversal is explicitly safe — limited coverage.
3. Storybook does not yet catalog every page pattern / state.
4. Playwright axe + visual baseline CI not automated.
5. Domain density still fixture-scoped; some modules remain thinner than a production ERP.
6. Bundle size large (FullCalendar + ECharts + React Flow); code-splitting deferred.
7. Auto-collapse sidebar at constrained desktop widths not fully productized.

---

## 13. Boundary confirmation

**Nothing outside `askmcneese/acm/` was created, modified, moved, formatted, renamed, or deleted in this corrective pass.**

All data remains fixture-only. No production auth/API/DB.

---

## Critique iterations (summary)

See [`VISUAL_QA.md`](./VISUAL_QA.md) loops 1–4.
