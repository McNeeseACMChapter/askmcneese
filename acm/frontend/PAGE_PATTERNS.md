# ACM Panel — Page Patterns

**North star:** *Calm institutional operations.*

Five layout patterns cover all ACM modules. Pick one primary pattern per route; do not hybridize (e.g., approval layout inside a wide collection table page).

Width modes: [`RESPONSIVE_RULES.md`](./RESPONSIVE_RULES.md).

---

## Pattern A — Role home

**Used by:** My Work (default after auth); optional chapter Home highlights.

**Purpose:** Surface *what needs a decision now* for the signed-in role.

### Structure

```text
┌─────────────────────────────────────────────────────────┐
│ Route header: identity line (EB Garamond) + role context │
├─────────────────────────────────────────────────────────┤
│ ACTION QUEUE (primary)                                   │
│   row → row → row  (Updates-style, 54px, priority sort)  │
├─────────────────────────────────────────────────────────┤
│ Secondary bands (optional, collapsed if empty)           │
│   Deadlines │ Blockers │ Compact metrics (1 row each)    │
└─────────────────────────────────────────────────────────┘
```

### Rules

- Action queue is always above the fold on desktop and mobile.
- Queue rows: title, module badge, deadline, single primary action — no card grids.
- EB Garamond for page identity only; queue in Source Sans 3.
- Empty queue: explain calm state + link to relevant module.
- Role content definitions: [`../roles/homes.md`](../roles/homes.md).

**Width mode:** Detail (1120–1240px) or full canvas with centered content.

---

## Pattern B — Collection

**Used by:** Projects, Meetings, Events, Members, Finance lists, Documents, Reports.

**Purpose:** Scan, filter, sort, and open records at scale.

### Structure

```text
┌─────────────────────────────────────────────────────────┐
│ Page title + primary create action (navy button)       │
├─────────────────────────────────────────────────────────┤
│ Filter bar: search, status chips, sort, saved views      │
├─────────────────────────────────────────────────────────┤
│ TABLE / ROW LIST (sticky header)                         │
│   col headers │ sort indicators │ row actions (kebab)  │
│   ... rows ...                                           │
├─────────────────────────────────────────────────────────┤
│ Pagination or infinite scroll (consistent per module)    │
└─────────────────────────────────────────────────────────┘
```

### Rules

- Row-based — not card mosaic.
- Bulk actions appear in a bar only when rows are selected.
- Empty state: one sentence + one primary action.
- Mobile: sticky first column or stacked row cards preserving column order.

**Width mode:** Collection (1360–1440px).

---

## Pattern C — Record detail

**Used by:** Single project, meeting, member, request, document, etc.

**Purpose:** Read and edit one entity with related context.

### Structure

```text
┌──────────────────────────────────────────┬──────────────┐
│ Breadcrumb                               │              │
├──────────────────────────────────────────┤  INSPECTOR   │
│ Record header: title, status, actions    │  (280px)     │
├──────────────────────────────────────────┤  related     │
│ Tabbed or stacked sections               │  timeline    │
│   Details │ Activity │ Attachments       │  people      │
│                                          │  permissions │
└──────────────────────────────────────────┴──────────────┘
```

### Rules

- Primary actions in header (Save, Submit, Assign) — navy primary.
- Inspector is supplementary; main body must stand alone if collapsed.
- Activity log is chronological rows, not chat bubbles.
- Tablet: inspector collapses to toggle; mobile: bottom sheet.

**Width mode:** Detail (1120–1240px) including inspector, or body-only when inspector hidden.

---

## Pattern D — Approval

**Used by:** Financial approvals, event sign-off, comms review, governance confirmations.

**Purpose:** Focused decision with evidence and audit trail.

### Structure

```text
┌─────────────────────────────────────┐
│ Back link → queue                   │
├─────────────────────────────────────┤
│ Context summary (read-only)         │
│   requester, amount, dates, status  │
├─────────────────────────────────────┤
│ Evidence links / attachments        │
├─────────────────────────────────────┤
│ Decision block                      │
│   [ Approve ]  [ Request changes ]  │
│   [ Reject ]                        │
├─────────────────────────────────────┤
│ Audit snippet (immutable preview)   │
└─────────────────────────────────────┘
```

### Rules

- No sidebar distraction; minimal chrome.
- Reject and request-changes require reason text.
- Confirm step for irreversible approve/reject.
- No gold buttons; navy primary on Approve only if single clear forward action.

**Width mode:** Approval (680–760px), centered on canvas.

---

## Pattern E — Editorial governance

**Used by:** Governance charter sections, election notices, SGA correspondence, long-form policy.

**Purpose:** Readable institutional prose with operational metadata.

### Structure

```text
┌─────────────────────────────────────┐
│ EB Garamond title + effective date│
├─────────────────────────────────────┤
│ Metadata strip (Source Sans 3)    │
│   status, owner, version, links     │
├─────────────────────────────────────┤
│ Prose body (EB Garamond, generous   │
│   line-height, max measure ~65ch)   │
├─────────────────────────────────────┤
│ Operational footer: signatures,     │
│   vote results, related records     │
└─────────────────────────────────────┘
```

### Rules

- EB Garamond for prose; all controls and meta in Source Sans 3.
- Side-by-side edit/preview only when explicitly editing — default is read.
- Print-friendly spacing; avoid glass behind long text blocks.

**Width mode:** Editorial (880–960px).

---

## Pattern selection matrix

| Need | Pattern |
|------|---------|
| Role inbox / priorities | A |
| List many records | B |
| One record with related context | C |
| Binary or ternary decision | D |
| Long-form institutional document | E |

---

## Related documents

- IA & nav: [`INFORMATION_ARCHITECTURE.md`](./INFORMATION_ARCHITECTURE.md)
- Tokens: [`DESIGN_CONTRACT.md`](./DESIGN_CONTRACT.md)
- QA: [`VISUAL_QA.md`](./VISUAL_QA.md)
