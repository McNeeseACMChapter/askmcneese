# ACM Panel — chapter operating system

> **Subsystem status:** separate internal prototype. The public AskMcNeese beta completion does not make this panel production-ready.

This folder is the **only** home for the ACM chapter internal system: governance, work, finance, communications, and institutional memory.

AskMcNeese Q&A lives outside this tree. Do not mix Ask chat UI or campus RAG into ACM Panel domains.

## What this system protects and enables

The chapter produces seven objects. The program must manage them reliably:

| Object | Meaning |
|--------|---------|
| **Authority** | Who is allowed to act |
| **Decisions** | What the organization officially approved |
| **Commitments** | Who promised to do what |
| **Work** | Projects, events, operational tasks |
| **Money** | Budgets, purchases, reimbursements, funding |
| **Communication** | Official notices and public content |
| **Evidence** | Minutes, receipts, documents, approvals, history |

A useful system always answers:

- Who currently has authority, and why?
- What requires attention today?
- What decisions were officially made?
- Who owns each commitment?
- What money has been approved and spent?
- What work is blocked?
- What evidence proves completion?
- What happens when current officers graduate?

## Final program definition

```
Identity + Governance + Work + Finance + Communication + Institutional memory
```

**Central principle:** every person sees what they are responsible for; every action follows an approved workflow; every important decision has evidence; no leadership transition destroys institutional knowledge.

## Folder map

| Path | Purpose |
|------|---------|
| [`PROGRAM.md`](./PROGRAM.md) | First-principles program plan (index) |
| [`laws/`](./laws/) | Non-negotiable architectural laws |
| [`domain/`](./domain/) | Core domain model |
| [`workflows/`](./workflows/) | State machines for org processes |
| [`modules/`](./modules/) | Product modules (My Work, Finance, …) |
| [`roles/`](./roles/) | Role-specific home screens |
| [`notifications/`](./notifications/) | Notification architecture |
| [`audit/`](./audit/) | Audit architecture |
| [`architecture/`](./architecture/) | Technical architecture |
| [`policy/`](./policy/) | Phase 0 governance specification (versioned) |
| [`phases/`](./phases/) | Build order Phase 0–7 + MVP |
| [`backend/`](./backend/) | Modular monolith (ACM-only backend) |
| [`frontend/`](./frontend/) | ACM Panel UI (ACM-only frontend) |
| [`auth/`](./auth/) | Demo credentials / auth notes |
| [`panel/`](./panel/) | Panel UX notes |

## Build discipline

1. Do **not** start with sidebar pages or officer cards.
2. Do **not** ship finance before authorization + audit are solid.
3. Backend is the authority; frontend hiding is not security.
4. Prefer soft-delete / archive / reverse / supersede — never erase history.

## Demo login (local only)

See [`auth/demo-credentials.json`](./auth/demo-credentials.json).
