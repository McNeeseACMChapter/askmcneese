# Sprint 3 — AskMcNeese

**Sprint Period:** June 30, 2026 – July 7, 2026 (1 week)  
**PM:** Prince Pudasaini  
**Theme:** Integration Testing + Documentation + Sprint 4 Planning

---

## Sprint 2 Status: COMPLETE

**Sprint 2 was completed on June 30, 2026** with the following PRs merged to `dev`:

| PR | Title | Status |
|----|-------|--------|
| #14 | BE-06/BE-07: POST /ask endpoint with full RAG pipeline | ✅ MERGED |
| #15 | FE-06+: Frontend UI refactor with design system | ✅ MERGED |

**Total PRs merged:** 15

---

## Team Reassignment Notice

**IMPORTANT:** As of June 30, 2026, all Backend tasks previously assigned to Landon have been **reassigned to PM (Prince)**.

**Reason:** Landon did not deliver any work in 15 days (June 15–30). He refused to adopt Cursor IDE for development and has not pushed any code to GitHub. Local development without pushing does not count toward sprint completion.

**Recognition:** Evan Weber (Frontend) completed his assigned task (FE-06) on time and pushed to GitHub on June 25, 2026.

---

## Current System Capability

With Sprint 2 complete, AskMcNeese now has:

| Layer | Capability | Status |
|-------|------------|--------|
| **Backend** | Full RAG pipeline: ChromaDB retrieval → Claude LLM generation → Streaming | ✅ Working |
| **Frontend** | Production-ready UI with conversation history, citations, animations | ✅ Working |
| **Integration** | End-to-end: User asks question → AI answers with McNeese sources | ✅ Working |

**Current Version:** v0.2.0 — Fully functional AI assistant with citations

---

## Sprint 3 Documents

| Document | Purpose |
|----------|---------|
| [pm_local_work_record.md](./pm_local_work_record.md) | Complete record of PM's local development work |
| [team_reassignment.md](./team_reassignment.md) | Official reassignment of Backend duties |
| [sprint3_tasks.md](./sprint3_tasks.md) | Micro-step task breakdown |
| [notebooklm_prompt.md](./notebooklm_prompt.md) | Design tokens and progress tracker prompt |
| [meeting_agenda_july3.md](./meeting_agenda_july3.md) | Thursday meeting agenda |

---

## Sprint 3 Task Assignments

### PM Tasks (Prince) — 50 pts
| ID | Task | Points | Due |
|----|------|--------|-----|
| PM-S3-01 | Expand crawler to 5 more sources | 15 | Jul 3 |
| PM-S3-02 | Write API documentation | 10 | Jul 2 |
| PM-S3-03 | Update setup guide | 10 | Jul 2 |
| PM-S3-04 | Create Sprint 4 plan | 10 | Jul 3 |
| PM-S3-05 | Run full integration test | 5 | Jul 1 |

### Frontend Tasks (Evan Weber) — 40 pts
| ID | Task | Points | Due |
|----|------|--------|-----|
| FE-S3-01 | Add dark mode toggle | 15 | Jul 5 |
| FE-S3-02 | Add loading skeletons for citations | 10 | Jul 4 |
| FE-S3-03 | Add error boundary | 10 | Jul 5 |
| FE-S3-04 | Mobile input improvements | 5 | Jul 4 |

### Backend Tasks (PM until Landon returns) — 40 pts
| ID | Task | Points | Due |
|----|------|--------|-----|
| BE-S3-01 | Add rate limiting to /ask | 10 | Jul 5 |
| BE-S3-02 | Add response caching | 10 | Jul 6 |
| BE-S3-03 | Add health check details | 10 | Jul 4 |
| BE-S3-04 | Add query analytics endpoint | 10 | Jul 6 |

**Total: 13 tasks, 130 points**

---

## Meeting: Thursday, July 3rd

**Time:** 1:00 PM – 3:00 PM  
**Location:** Drew Hall, McNeese State University

**Agenda:**
1. Sprint 3 progress review (all merged work)
2. Live demo of AskMcNeese
3. Sprint 4 planning and task assignment

---

*Created: June 30, 2026*
