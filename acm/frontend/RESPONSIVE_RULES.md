# ACM Panel — Responsive Rules

**North star:** *Calm institutional operations.*

ACM shares AskMcNeese's institutional identity but uses **mode-specific page widths**, not chat's fixed 820px column. All layouts must degrade calmly from desktop operations to mobile field use.

---

## Reference viewports

Test and sign off at these widths (CSS pixels):

| Token | Width | Typical device |
|-------|-------|----------------|
| `xs` | **375** | iPhone SE / narrow phone |
| `sm` | **430** | iPhone Pro / large phone |
| `md` | **768** | Tablet portrait |
| `lg` | **1024** | Tablet landscape / small laptop |
| `xl` | **1440** | Standard desktop |
| `2xl` | **1920** | Large desktop |

Breakpoints align with token gutters in `src/styles/tokens.css`.

---

## Page width modes

Content max-width is chosen by **page pattern**, not viewport alone. Center on canvas with horizontal auto margins.

| Mode | Min–max | Patterns | Token |
|------|---------|----------|-------|
| **Collection** | 1360–1440px | B — Collection | `--page-collection-max: 1400px` |
| **Detail** | 1120–1240px | A (secondary), C — Record detail | `--page-detail-max: 1180px` |
| **Editorial** | 880–960px | E — Editorial governance | `--page-editorial-max: 920px` |
| **Approval** | 680–760px | D — Approval | `--page-approval-max: 720px` |

Below the mode max-width, content fills available width minus gutters — never introduce a chat-style 820px cap.

---

## Gutters & chrome by viewport

| Viewport | Page gutter | Sidebar | Mobile top capsule |
|----------|-------------|---------|-------------------|
| ≥1440 | 40px | Expanded 280px default | Hidden |
| 1024–1439 | 32px | Expanded or collapsed user pref | Hidden |
| 768–1023 | 24px | Collapsed 76px or overlay | Hidden |
| <768 | 16px | Hidden | **Visible** (56px + safe area) |

Mobile top offset: `safe-area-inset-top + 8px + nav height + 8px`.

---

## Desktop → mobile transformations

### Global chrome

| Desktop | ≤767px |
|---------|--------|
| Dark collapsible sidebar (280 / 76) | Hidden |
| Module nav in sidebar groups | Top capsule: Home, My Work, Meetings, More |
| Footer: Notifications, Admin, Audit, Profile | More sheet + notification badge on capsule |

**Never** use a bottom tab bar.

### Pattern A — Role home

| Desktop | Mobile |
|---------|--------|
| Queue + side-by-side secondary bands | Single column; queue first |
| Hover row actions | Kebab menu per row |

### Pattern B — Collection

| Desktop | Mobile |
|---------|--------|
| Full filter bar inline | Search + chip row; advanced filters in sheet |
| Multi-column table | Horizontal scroll, **sticky first column**, or equivalent card-rows |
| Bulk action bar | Sticky bottom bar when rows selected (above safe area) |

### Pattern C — Record detail

| Desktop | Mobile |
|---------|--------|
| Body + 280px inspector rail | Single column body |
| Inspector visible | Inspector → **bottom sheet** or full-screen panel |
| Tabbed sections | Same tabs, scroll horizontally if needed |

### Pattern D — Approval

| Desktop | Mobile |
|---------|--------|
| Centered 680–760px column | Full width minus 16px gutter |
| Side-by-side actions | Stacked full-width buttons; destructive last |

### Pattern E — Editorial

| Desktop | Mobile |
|---------|--------|
| 880–960px prose measure | Full width; maintain ~65ch via padding |
| EB Garamond titles | Same; no size reduction below readable minimum |

---

## Touch & pointer

| Rule | Value |
|------|-------|
| Minimum hit target | 44×44px |
| Row height (collections) | 54px |
| Sidebar row height | 44px |
| Spacing scale | 4px base only |

Pointer hover states are enhancements — mobile layouts must not depend on hover to reveal critical actions.

---

## Motion & accessibility at breakpoints

- Sidebar collapse: 280ms panel motion; disabled under `prefers-reduced-motion`.
- More sheet / inspector sheet: slide up on mobile; instant open under reduced motion.
- Glass blur: disabled under `prefers-reduced-transparency` at all viewports.

---

## Related documents

- Transformation rationale: [`DESIGN_AUDIT.md`](./DESIGN_AUDIT.md)
- Page structures: [`PAGE_PATTERNS.md`](./PAGE_PATTERNS.md)
- Visual sign-off: [`VISUAL_QA.md`](./VISUAL_QA.md)
