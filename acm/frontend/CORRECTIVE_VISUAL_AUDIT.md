# Corrective visual audit — ACM Panel (pre-rebuild)

**Date:** 2026-07-18  
**Verdict:** Polished static wireframe. Shell/tokens are coherent; operational translation failed.

Central failure: designed shell first, poured text second. Did not design how chapter data becomes a decision interface.

---

## Defect catalog

| ID | Route / area | Observed | Harm | Correction | Likely file | Validation |
|----|--------------|----------|------|------------|-------------|------------|
| D01 | Global | Approve success becomes permanent yellow banner via `localFeedback` in shell | Stale action chrome; confuses system status with toast | Delete; real toast with auto-dismiss; mutate related fixture views | `PrototypeContext.tsx`, `AcmAppShell.tsx`, `ApprovalDetailPage.tsx` | Action → toast gone after dismiss; Home/My Work counts update |
| D02 | All routes | Full-width prototype banner + optional feedback banner | Burns first viewport; product feels unfinished | One compact Prototype badge in identity/profile | `PrototypeDataNotice.tsx`, pages | Screenshots: no dual yellow banners |
| D03 | Header + body | Route header title + page H1 duplicate | Generated hierarchy | Header: breadcrumb + tools only; one H1 in content | `AcmRouteHeader.tsx`, `PageHeader.tsx` | One H1 per page axe/DOM |
| D04 | Home / My Work | Same “Needs your attention” queue | Roles of pages collapse | Home = command center; My Work = personal execution tabs | `HomePage.tsx`, `MyWorkPage.tsx` | Content differ by screenshot + tests |
| D05 | Modules | Same serif + paragraph + white card sentence | Domains indistinguishable | Domain-specific layouts per route manifest | `PlaceholderPage.tsx`, pages | Visual QA loop 2 |
| D06 | Meetings, Reports, etc. | “Module shell reserved for a later pass.” | Navigable emptiness | Meaningful workspace or hide from nav | `App.tsx`, `PlaceholderPage.tsx` | No placeholder copy in active nav |
| D07 | Projects | Table only; little health/progress/trend | Portfolio not scannable | Progress, health strip, sparkline, board/timeline views | `ProjectsPage.tsx` | Columns + view switch |
| D08 | Project detail | Stacked text cards | Not a delivery cockpit | Stepper, risk matrix, evidence ring, tabs with content | `ProjectDetailPage.tsx` | Tabs have content |
| D09 | Sidebar | 280px; native scrollbar; heavy gray+gold active slab; equal weight footer | Chrome dominates work | 256/72; styled scroll; 2px gold rail; translucent active; profile menu | `shell.css`, `AcmSidebar.tsx` | Screenshots |
| D10 | Actions | Only normal/selected; approve doesn’t update dependents | Fake success | IDLE→PENDING→OPTIMISTIC→CONFIRMED/FAILED/REVERTED + repo | fixture repository + Query | Mutation tests |
| D11 | Visual encoding | Badges/sentences only | No operational glance | Sparklines, steppers, calendars, variance bars, etc. | new `components/viz/` | Domain screenshots |
| D12 | Mobile | Capsule OK; modules still text-card stacks | Squeeze of desktop template | Domain mobile alternatives | pages + CSS | 375/430 captures |
| D13 | Fixture arch | Pages mutate via `setLocalFeedback` only | No API-shaped state | Async fixture repository + TanStack Query | `src/data/` | Query DevTools / tests |
| D14 | A11y | Focus ok-ish; color-only risks; no toast a11y | Incomplete trust | Radix overlays; chart text summaries; axe | primitives + Playwright | axe report |

---

## Per-route snapshot (before)

| Route | Status |
|-------|--------|
| Login | UI-only form — OK as prototype entry |
| Home | Text queue + secondary cards — not command center |
| My Work | Duplicate of Home queue |
| Projects | Basic table — weak viz |
| Project detail | Text cards |
| Approval | Text + permanent success banner bug |
| Meetings…Reports, Notifications, Admin, Audit, Profile | Placeholder shells |
| Fixtures gallery | Dev-only — keep but not primary nav |

---

## Stop conditions (this pass)

Pass fails if D01–D06 remain, or any active nav route shows placeholder text, or Home ≡ My Work.
