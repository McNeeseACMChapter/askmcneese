# ACM Panel — Design Audit

**North star:** *Calm institutional operations.*

ACM Panel is the operational sibling of public AskMcNeese — same institutional identity, different job. AskMcNeese answers questions; ACM runs the chapter. The UI should feel like a quiet control room, not a chat product or a generic admin template.

---

## Public AskMcNeese patterns to preserve

These patterns come from the public frontend and define shared brand grammar. ACM inherits them deliberately.

| Pattern | Specification | ACM application |
|---------|---------------|-----------------|
| **Brand palette** | Navy scale (950 → 600) + gold accent | Sidebar, primary actions, identity chrome |
| **Typography roles** | **Source Sans 3** — UI, data, forms, tables | All operational surfaces |
| | **EB Garamond** — identity, page titles, editorial | Panel wordmark, role home headlines, governance prose |
| **Spacing scale** | 4px base (`4, 8, 12, 16, 20, 24, 32, 40, 48, 64`) | Layout, gutters, row heights |
| **Glass levels (3)** | Nav / content / interactive | Top bars, page shells, floating panels — not decorative frosting |
| **Sidebar** | Collapsible dark liquid-glass; **280px expanded / 76px collapsed** | Primary desktop navigation; gold active indicator sparingly |
| **Mobile nav** | **Top capsule** (not bottom bar) | Home, My Work, Meetings, More |
| **Icons** | Lucide; **18px / stroke 1.75** | Nav, actions, status — consistent weight |
| **Motion** | Quiet: 160–280ms standard; no bounce on data UI | Panel open/close, sidebar collapse, row hover |
| **List grammar** | Updates-style **rows**, not card mosaics | Queues, collections, notification feeds |

---

## Chat-specific patterns NOT to copy

AskMcNeese chat is a conversation product. ACM is an operations product. Do not transplant chat UX.

| Pattern | Why it stays in chat |
|---------|----------------------|
| **Composer** (sticky input, send affordance, attachment strip) | ACM uses forms on record pages, not open-ended message entry |
| **Message bubbles** (user/assistant threading, avatars in stream) | ACM uses structured records, audit trails, and comment threads on entities |
| **820px chat width** | Chat optimizes reading line length for prose; ACM uses mode-specific widths (collection / detail / editorial / approval) |
| **Conversation history as primary nav content** | ACM nav is module-based and permission-stable; history lives inside records |

---

## Older / inconsistent patterns NOT to copy

| Pattern | Problem | ACM alternative |
|---------|---------|-----------------|
| Generic bordered secondary cards in grids | Visual noise; hides hierarchy | Row-based collections with inline metadata |
| Bottom navigation bar | Conflicts with mobile top capsule; feels consumer-app | Top capsule + More sheet |
| Gold primary buttons | Reads as marketing CTA | Navy primary buttons; gold for identity accents only |
| Card mosaic dashboards | No scan path for operators | Role home **action queue** + compact metrics |
| Heavy drop shadows on every surface | Feels promotional | Three glass levels + subtle elevation |
| Mixed icon sets or sizes | Breaks institutional calm | Lucide 18px / 1.75 everywhere |

---

## New ACM operational patterns

These are native to the panel and have no AskMcNeese chat equivalent.

### Collection tables

- Primary pattern for Projects, Meetings, Members, Finance requests, Documents, Reports.
- Sticky header row, sortable columns, filter bar above (not buried in modals).
- Row height ~54px; selection and bulk actions appear only when rows are selected.
- Empty states explain *what belongs here* and offer one primary create/import action.

### Approval pages

- Narrow focused layout (680–760px content width).
- Decision block: context summary → evidence links → approve / reject / request changes.
- Immutable audit snippet visible before confirm.
- No sidebar clutter; back link to queue.

### Role home action queue

- Default landing after auth: **My Work** (role-aware).
- Above-the-fold: prioritized **action queue** (what needs a decision now).
- Secondary bands: deadlines, blockers, metrics — never competing with the queue for attention.
- EB Garamond for the page identity line only; queue items in Source Sans 3.

### Context inspector

- Optional right rail (~280px) on detail pages.
- Shows related entities, timeline, assignees, permissions — without leaving the record.
- Collapsible on tablet; sheet on mobile.
- Does not replace the main record body.

---

## Accessibility requirements

| Requirement | Rule |
|-------------|------|
| **Color contrast** | Text primary/secondary/muted on canvas and surface meet WCAG AA (4.5:1 body, 3:1 large type) |
| **Focus** | Visible focus ring (`--focus-ring`); never `outline: none` without replacement |
| **Keyboard** | Full nav, tables, filters, approval actions operable without pointer |
| **Motion** | Honor `prefers-reduced-motion`; no essential information in animation alone |
| **Transparency** | Honor `prefers-reduced-transparency`; glass falls back to solid surfaces |
| **Touch targets** | Minimum 44×44px hit targets on mobile |
| **Tables** | Proper `<th>` scope, sort state announced, row actions reachable |
| **Forms** | Labels, errors linked via `aria-describedby`; required fields marked |
| **Status** | Live regions for async save, approval outcome, queue refresh |

---

## Responsive transformation rules

| Desktop | Mobile / narrow |
|---------|-----------------|
| Dark collapsible sidebar (280 / 76) | Hidden; **top capsule** nav |
| Three-column detail (body + inspector) | Single column; inspector → bottom sheet |
| Inline filter bar | Filter chip row + sheet for advanced filters |
| Multi-column collection table | Horizontal scroll with sticky first column, or card-rows with same data order |
| Hover-revealed row actions | Always-visible action menu (kebab) |
| Page gutter 40px → 32px → 24px → 16px | See `RESPONSIVE_RULES.md` |

Full viewport breakpoints and page width modes: [`RESPONSIVE_RULES.md`](./RESPONSIVE_RULES.md).

Token values and anti-patterns: [`DESIGN_CONTRACT.md`](./DESIGN_CONTRACT.md).  
Information architecture: [`INFORMATION_ARCHITECTURE.md`](./INFORMATION_ARCHITECTURE.md).  
Page templates: [`PAGE_PATTERNS.md`](./PAGE_PATTERNS.md).
