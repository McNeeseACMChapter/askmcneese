# Team Reassignment Notice — Sprint 3

**Date:** June 30, 2026  
**Issued by:** Prince Pudasaini (PM)

---

## Backend Role Reassignment

**Effective immediately, all Backend Developer responsibilities previously assigned to Landon are reassigned to PM (Prince Pudasaini).**

---

## Reason for Reassignment

### Timeline of Non-Delivery

| Date | Expected | Actual |
|------|----------|--------|
| June 15, 2026 | Sprint 1 complete (dev merged) | ✅ Sprint 1 merged |
| June 15–30 | Sprint 2 Backend work (BE-06, BE-07, BE-08) | ❌ No commits from Landon |
| June 25, 2026 | — | Evan completed FE-06, pushed to GitHub |
| June 30, 2026 | Sprint 2 should be complete | ❌ Backend not delivered |

**15 days elapsed with zero backend commits from Landon.**

### Specific Issues

1. **Refused to use Cursor IDE** — Landon declined to adopt the team's development tool, which provides AI assistance and was agreed upon for the project

2. **No code pushed to GitHub** — Local development does not count toward sprint completion; the project tracks progress through GitHub commits and PRs

3. **Blocked teammate** — Evan Weber completed his frontend work (FE-06) on June 25 but cannot merge because the `/ask` endpoint doesn't exist

4. **No communication** — No status updates, blockers reported, or requests for help

---

## Recognition: Evan Weber

**Evan Weber (Frontend Developer) performed well.**

- Completed FE-06 on time (June 25, 2026)
- Pushed code to GitHub on branch `frontend-code/evan-weber`
- Commit: `792ed5c` — "FE-06: Wire /ask hook and render retrieved citations"
- Delivered:
  - `useAsk.ts` hook for API calls
  - Updated `App.tsx` with real API integration
  - `MessageBubble.tsx` with citation rendering
  - Proper TypeScript types for API response

Evan's work is ready to merge once the backend endpoint exists.

---

## PM's Response

To prevent further project delays, PM has completed all backend work locally:

| Original Ticket | Completed By | Status |
|-----------------|--------------|--------|
| BE-06: `POST /ask` endpoint | PM (Prince) | ✅ Done locally |
| BE-07: Query logging | PM (Prince) | ✅ Done locally |
| BE-08: Expand ingest | Pending | To be done in Sprint 3 |
| Beyond scope: LLM integration | PM (Prince) | ✅ Done locally |
| Beyond scope: SSE streaming | PM (Prince) | ✅ Done locally |

Additionally, PM enhanced the frontend with:
- Complete UI refactor
- Design system with CSS variables
- Framer Motion animations
- Conversation history management
- Splash screen

---

## Going Forward

### Sprint 3 Ownership

| Area | Owner |
|------|-------|
| Backend development | PM (Prince) |
| Frontend development | PM (Prince) + Evan Weber |
| Content & Knowledge | As assigned |
| DevOps/QA | As assigned |

### Policy Reminder

For all team members:

1. **Push your work** — Local code that isn't pushed doesn't exist for the project
2. **Use agreed tools** — Cursor IDE is the team standard
3. **Communicate blockers** — If stuck, ask for help immediately
4. **Meet deadlines** — Or communicate early if you can't

---

## Landon's Path Forward

If Landon wishes to re-engage with the project:

1. Acknowledge the current state of `dev` branch
2. Learn the existing codebase (FastAPI, ChromaDB, React)
3. Request specific tasks from PM
4. Push work within agreed timelines

Until then, Backend responsibilities remain with PM.

---

*This document serves as the official record of the Backend role reassignment.*
