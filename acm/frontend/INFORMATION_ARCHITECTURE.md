# ACM Panel — Information Architecture

**North star:** *Calm institutional operations.*

Stable, permission-aware navigation. Order is fixed — do not reorder items by role or recency. Role affects **home content** and **visible destinations**, not nav sequence.

**Product name:** ACM Panel  
**Default route after auth:** My Work

---

## Desktop sidebar

Collapsible dark sidebar (280px / 76px). Groups and items appear in this **exact order**.

### Overview

| Item | Route purpose |
|------|---------------|
| **Home** | Chapter snapshot; links into modules (not a role queue — see My Work) |
| **My Work** | Role-aware action queue and personal operational inbox |

### Operations

| Item | Route purpose |
|------|---------------|
| **Projects** | Portfolio, milestones, tasks, blockers |
| **Meetings** | Agendas, minutes, decisions, votes |
| **Events** | Chapter events lifecycle and approvals |

### Organization

| Item | Route purpose |
|------|---------------|
| **Members** | Roster, roles, assignments, terms |
| **Governance** | Bylaws, policies, elections, appointments |
| **SGA** | University SGA interface, deadlines, reports |

### Resources

| Item | Route purpose |
|------|---------------|
| **Finance** | Budgets, requests, reimbursements, receipts |
| **Communications** | Internal and public comms workflows |
| **Documents** | Repository, templates, retention |
| **Reports** | Operational and compliance reporting |

### Footer (sidebar bottom)

| Item | Route purpose | Visibility |
|------|---------------|------------|
| **Notifications** | Actionable inbox; deep links to records | All authenticated users |
| **Administration** | User/role config, module settings | Permission-gated |
| **Audit** | Immutable activity log, exports | Permission-gated |
| **Profile** | Identity, preferences, session | All authenticated users |

**Administration** and **Audit** render only when the user holds the required permissions. Hidden items leave no gap — adjacent items stay in order.

---

## Mobile top capsule

Bottom bar is **not used**. Primary mobile nav is a **top capsule** with four slots, fixed order:

| Slot | Maps to |
|------|---------|
| **Home** | Overview → Home |
| **My Work** | Overview → My Work |
| **Meetings** | Operations → Meetings |
| **More** | Sheet/drawer with remaining modules |

### More sheet contents (stable order)

1. Projects  
2. Events  
3. Members  
4. Governance  
5. SGA  
6. Finance  
7. Communications  
8. Documents  
9. Reports  
10. Notifications  
11. Administration *(if permitted)*  
12. Audit *(if permitted)*  
13. Profile  

Same permission rules as desktop. Administration and Audit omitted entirely when unauthorized — not shown disabled.

---

## Navigation behavior

| Rule | Detail |
|------|--------|
| **Stable order** | Never sort nav by usage, alerts, or role |
| **Badges** | Counts on Notifications and My Work only; subtle, not red unless urgent |
| **Deep links** | Notifications and email links land on record/approval pages, not chat |
| **Breadcrumbs** | Module → collection → record; mirror URL |
| **Search** | Global command palette (future); modules keep local filter bars |

---

## Module ↔ pattern mapping

| Module | Primary page pattern |
|--------|---------------------|
| My Work | A — Role home |
| Projects, Meetings, Events, Members, Finance, Documents, Reports | B — Collection |
| Record views across modules | C — Record detail |
| Finance, Events, Communications, Governance (workflows) | D — Approval |
| Governance, SGA (charters, notices) | E — Editorial governance |

Pattern definitions: [`PAGE_PATTERNS.md`](./PAGE_PATTERNS.md).

---

## Related documents

- Design audit: [`DESIGN_AUDIT.md`](./DESIGN_AUDIT.md)
- Tokens: [`DESIGN_CONTRACT.md`](./DESIGN_CONTRACT.md)
- Responsive behavior: [`RESPONSIVE_RULES.md`](./RESPONSIVE_RULES.md)
