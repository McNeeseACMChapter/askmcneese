# Sprint 2 Report — AskMcNeese

**Project:** AskMcNeese  
**Sprint:** 2 — Retrieval + `/ask` Wiring  
**Report date:** June 30, 2026  
**Facilitator:** Prince Pudasaini (PM)

---

## Executive Summary

| Area | Status | Notes |
|------|--------|-------|
| **Sprint 1** | ✅ Complete | 16/16 tickets merged to `dev` |
| **Sprint 2** | ❌ INCOMPLETE | Backend work not delivered |
| **FE-06** | ✅ Done | Evan Weber completed on June 25 |
| **BE-06, BE-07, BE-08** | ❌ Not Done | Landon's backend tasks pending |
| **GitHub** | 13 PRs merged to dev | Evan's branch ready but blocked |

**Bottom line:** Sprint 2 is **NOT COMPLETE**. Evan delivered FE-06 on June 25 but the backend endpoints (BE-06, BE-07, BE-08) have not been delivered by Landon. Evan's frontend work cannot be merged until the `POST /ask` endpoint exists.

---

## Sprint 2 Ticket Status

| Ticket | Task | Owner | Actual Status | Location |
|--------|------|-------|---------------|----------|
| **BE-06** | `POST /ask` — retrieve chunks, return citations | Landon | ❌ NOT DONE | Needs `backend/app/routers/ask.py` |
| **BE-07** | Query logging (`query_logs` JSONL) | Landon | ❌ NOT DONE | Needs `backend/app/services/` |
| **FE-06** | Wire Send → `POST /ask`, show citations | Evan Weber | ✅ DONE (GitHub) | `frontend-code/evan-weber` branch |
| **BE-08** | Expand ingest to more Approved sources | Landon | ❌ NOT DONE | Needs crawler expansion |

### Evan Weber's Completed Work (FE-06)

**Branch:** `frontend-code/evan-weber`  
**Commit:** `792ed5c` — "FE-06: Wire /ask hook and render retrieved citations"  
**Date:** June 25, 2026

**Files delivered:**
- `frontend/src/hooks/useAsk.ts` — Hook for `POST /ask` API calls
- `frontend/src/App.tsx` — Wired to useAsk hook, removed demo simulation
- `frontend/src/components/MessageBubble.tsx` — Added CitationBlock for displaying sources
- `frontend/src/types.ts` — Added `RetrievedChunk`, `AskCommand`, `AskResponse` types
- Deleted `frontend/src/data/sampleMessages.ts` (no more demo data)

**Status:** Ready to merge once BE-06 endpoint exists

---

## GitHub Repository Status

**Remote:** https://github.com/McNeeseACMChapter/askmcneese.git  
**Branch:** `dev` (up to date with origin/dev)  
**Last pushed commit:** `d5ba2f1` — "Close DQ-04: CI on dev and Sprint 1 backlog 16/16" (June 15, 2026)

### Merged PRs (All Time)

| PR # | Title | Status | Date |
|------|-------|--------|------|
| #13 | Close DQ-04: CI on dev and Sprint 1 backlog complete (16/16) | Merged | Jun 15, 2026 |
| #12 | Add lightweight CI for Backend import and frontend build (DQ-04) | Merged | Jun 15, 2026 |
| #11 | Merge Cloudflare browser fallback for www.mcneese.edu crawling | Merged | Jun 15, 2026 |
| #10 | Feature/cloudflare browser fetch | Merged | Jun 15, 2026 |
| #9 | Fix Cloudflare 403 on www.mcneese.edu with Playwright browser fallback | Merged | Jun 15, 2026 |
| #8 | Sprint 2 readiness: close Sprint 1 gaps | Merged | Jun 15, 2026 |
| #7 | Remove .cursor from GitHub | Merged | Jun 15, 2026 |
| #6 | PM-06: Sprint 1 week review + backlog status | Merged | Jun 15, 2026 |
| #5 | Complete Frontend Sprint 1: AskMcNeese chat shell | Merged | Jun 15, 2026 |
| #4 | Complete PM Sprint 1 tickets | Merged | Jun 15, 2026 |
| #3 | Sprint 1 backend retrieval pipeline | Merged | Jun 15, 2026 |
| #2 | Add Week 1 sprint backlog | Merged | Jun 9, 2026 |
| #1 | Create the Sprint 1 foundation files | Merged | Jun 9, 2026 |

## Sprint 2 Verdict

### Is Sprint 2 Complete?

| Criterion | Answer |
|-----------|--------|
| BE-06 (`POST /ask`) | ❌ NOT DONE — Landon's responsibility |
| BE-07 (Query logging) | ❌ NOT DONE — Landon's responsibility |
| FE-06 (Frontend wiring) | ✅ DONE by Evan Weber on GitHub |
| BE-08 (Expand ingest) | ❌ NOT DONE — Landon's responsibility |

### Conclusion

**Sprint 2 is NOT COMPLETE.**

**What's done:**
- FE-06: Evan Weber completed frontend wiring on `frontend-code/evan-weber` branch (June 25, 2026)

**What's blocking:**
- BE-06, BE-07, BE-08: Backend work not delivered by Landon
- Evan's frontend cannot be merged until `POST /ask` endpoint exists
- 5 days since Evan completed his work, no backend to connect to

**Action Required:**
- Landon must deliver BE-06 (`POST /ask`) immediately
- See `docs/landon_backend_tasks.md` for detailed requirements

---

## Blockers & Open Items

| # | Item | Owner | Action Needed |
|---|------|-------|---------------|
| 1 | BE-06 not delivered | Landon | Create `POST /ask` endpoint ASAP |
| 2 | BE-07 not delivered | Landon | Add query logging |
| 3 | BE-08 not delivered | Landon | Expand crawler to more sources |
| 4 | FE-06 branch waiting | Evan | Blocked until BE-06 exists |
| 5 | No backend PR created | Landon | Create `feature/backend-ask` branch |

---

## Recommendations

1. **Immediate Priority:** Landon must deliver BE-06 (`POST /ask`) so Evan's work can be merged

2. **Landon's Branch:** Create `feature/backend-ask` for BE-06, BE-07

3. **Merge Order:**
   - BE-06 PR merged first
   - Then FE-06 PR (`frontend-code/evan-weber`)

4. **Reference:** See `docs/landon_backend_tasks.md` for detailed requirements

---

*Generated: June 30, 2026*  
*Sprint 2 local work verified against git status and file inspection*
