# Sprint 1 — Week 1 Review

**Project:** AskMcNeese  
**Sprint:** Foundation (Week 1)  
**Review date:** June 14, 2026  
**Facilitator:** Prince Pudasaini (PM)

This is the **PM-06** deliverable: a single place to see what each role finished, what proof exists, and what is still blocked before Sprint 2.

---

## Executive summary

| Area | Verdict | Notes |
|------|---------|-------|
| **Repo & structure** | ✅ Done | `main` / `dev` / `feature/*` in place; Sprint 1 folders merged |
| **PM / Full-Stack** | ✅ Done | PM-01 → PM-06 complete; open PR #4 |
| **Frontend** | ✅ Done | FE-01 → FE-05 complete; open PR #5 |
| **Backend (reference)** | ✅ Done (PM-built) | BE-01 → BE-05 pipeline proven; open PR #3 |
| **Backend (assigned dev)** | ⚠️ Partial | Django submission reviewed; realignment needed |
| **Content & Knowledge** | ✅ Ready | Registry + 12 PM approvals + test questions |
| **DevOps / QA** | ✅ Done | `docs/qa/` + CI on `dev` |

**Bottom line:** Sprint 1 foundation is **merged to `dev`**. Carry-over gaps are closed in
`docs/sprint2_readiness.md`. Sprint 2 development can start.

---

## Merged pull requests (Sprint 1)

All Sprint 1 work is on **`dev`**:

| PR | What |
|----|------|
| [#3](https://github.com/McNeeseACMChapter/askmcneese/pull/3) | Backend crawler pipeline (BE-01..BE-05) |
| [#4](https://github.com/McNeeseACMChapter/askmcneese/pull/4) | PM tickets (`/health`, schema, setup) |
| [#5](https://github.com/McNeeseACMChapter/askmcneese/pull/5) | Frontend shell (FE-01..FE-05) |
| [#6](https://github.com/McNeeseACMChapter/askmcneese/pull/6) | Week 1 review (PM-06) |
| [#7](https://github.com/McNeeseACMChapter/askmcneese/pull/7) | Remove `.cursor` from repo |

---

## Role scorecards

### PM / Full-Stack — Prince

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| PM-01 | Repo + branch strategy | ✅ Done | GitHub repo, team access |
| PM-02 | Folder structure | ✅ Done | PR #1 merged to `dev` |
| PM-03 | FastAPI `/health` | ✅ Done | `backend/app/routers/health.py` — PR #4 |
| PM-04 | DB schema draft | ✅ Done | `docs/db_schema.md` — PR #4 |
| PM-05 | `.env.example` + setup | ✅ Done | `.env.example`, `docs/setup.md` — PR #4 |
| PM-06 | Sprint review | ✅ Done | This file |

**Blockers:** None on PM track.

---

### Frontend — Evan Weber (reference implementation shipped by PM)

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| FE-01 | React + Vite + Tailwind shell | ✅ Done | `npm run build` passes — PR #5 |
| FE-02 | Chat UI shell | ✅ Done | `frontend/src/App.tsx` |
| FE-03 | Reusable components | ✅ Done | `frontend/src/components/` |
| FE-04 | Wire to `/health` | ✅ Done | Header shows **Online · v0.1.0** when API runs |
| FE-05 | Responsive + screenshots | ✅ Done | `docs/screenshots/week1_frontend/` |

**Blockers:** None for Sprint 1 shell. Real `/ask` answers are intentionally out of scope until a later sprint.

**Handoff note:** Use `VITE_API_BASE_URL` (see `frontend/.env.example`). Follow `docs/frontend_guidelines.md`.

---

### Backend — assigned developer

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| BE-01 | Crawler fetch | ⚠️ Partial | Submitted Django skeleton only; reference in PR #3 |
| BE-02 | HTML cleaner | ⚠️ Partial | Reference: `crawler/clean_text.py` — PR #3 |
| BE-03 | Chunker (~300 tokens) | ⚠️ Partial | Reference: `crawler/chunker.py` — PR #3 |
| BE-04 | ChromaDB ingest | ⚠️ Partial | Reference: `crawler/ingest.py` — PR #3 |
| BE-05 | Sample output | ⚠️ Partial | `docs/samples/` — PR #3 |

**Verdict:** Submission reviewed June 14 (Ticket #17). Framework mismatch (Django vs agreed FastAPI) and missing pipeline. PM reference implementation on PR #3 is the realignment target.

**Blockers:**
- Developer must realign to FastAPI + `crawler/` pipeline pattern.
- `www.mcneese.edu` returns **403** to programmatic requests — team decision needed.

---

### Content & Knowledge

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| CK-01 | Source registry seed CSV | ✅ Done | `knowledge/source_registry_seed.csv` (30 URLs) — PR #3 |
| CK-02 | First 3 seed pages | ✅ Done | Included in registry |
| CK-03 | Categorize + trust tier | ✅ Done | Columns populated in CSV |
| CK-04 | 15 starter test questions | ✅ Done | `knowledge/test_questions_week1.md` |
| CK-05 | Handoff to Backend | ✅ Done | 12 PM-approved sources; crawler reads CSV |

**Blockers:** 18 sources remain `Pending` (sensitive or `www.mcneese.edu` 403). See `docs/crawler_403_strategy.md`.

---

### DevOps / QA

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| DQ-01 | Validate repo setup | ✅ Done | `docs/qa/week1_setup_notes.md` |
| DQ-02 | PR checklist | ✅ Done | `docs/qa/pr_checklist.md` |
| DQ-03 | Week 1 smoke tests | ✅ Done | `docs/qa/week1_smoke_tests.md` |
| DQ-04 | Simple CI | ✅ Done | `.github/workflows/ci.yml` — PR #13 |
| DQ-05 | Sprint review proof | ✅ Done | Screenshots + samples + smoke test doc |

**Blockers:** None on DevOps/QA track for Sprint 1.

---

## Proof inventory (no verbal explanation needed)

| Evidence | Location |
|----------|----------|
| Backend health JSON | `GET /health` → `{ status, service, version }` |
| Frontend mobile screenshot | `docs/screenshots/week1_frontend/mobile_chat.png` |
| Frontend desktop screenshot | `docs/screenshots/week1_frontend/desktop_chat.png` |
| Crawler clean-text sample | `docs/samples/clean_text_sample.md` |
| Chunk JSON sample | `docs/samples/chunks_sample.json` |
| Source registry | `knowledge/source_registry_seed.csv` |
| DB schema draft | `docs/db_schema.md` |
| Local setup guide | `docs/setup.md` |

---

## Blockers & decisions (PM action list)

| # | Blocker | Owner | Action |
|---|---------|-------|--------|
| 1 | Backend dev realignment (Django → FastAPI) | PM + Backend | Use `dev` as reference; schedule sync |
| 2 | `www.mcneese.edu` 403 bot protection | PM + Backend | See `docs/crawler_403_strategy.md` |
| 3 | 18 registry URLs still Pending | PM | Approve in batches as crawl strategy allows |
| 4 | CI not set up (DQ-04) | DevOps/QA | ✅ Done — `.github/workflows/ci.yml` on `dev` |

---

## Scope boundaries (honored)

- ✅ No Canvas integration
- ✅ No Microsoft SSO
- ✅ No LLM answer generation
- ✅ No full-site crawling
- ✅ No production deployment
- ✅ No private / login-only data in registry

---

## Sprint 2 readiness

See **`docs/sprint2_readiness.md`** for the full handoff. System is ready when:

1. ✅ All Sprint 1 PRs merged to `dev`
2. ⏳ Backend developer acknowledges FastAPI + crawler realignment plan
3. ✅ PM approved first batch of registry URLs (12 sources)

**Sprint 2 focus:** `POST /ask` retrieval endpoint, frontend Send → API, expand approved ingests.

---

*Generated as part of PM-06. Internal PM timeline: Ticket #21.*
