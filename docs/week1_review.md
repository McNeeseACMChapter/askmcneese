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
| **Content & Knowledge** | ⚠️ Partial | Registry seed exists (30 URLs); approval + test questions pending |
| **DevOps / QA** | ⚠️ Partial | Setup docs exist; formal QA checklist/smoke tests not yet filed |

**Bottom line:** The **foundation is buildable and provable** on open PRs. Sprint 1 code goals are met via reference implementations. Assigned Backend and Content tracks need catch-up / sign-off before Sprint 2 work starts on `dev`.

---

## Open pull requests (merge order)

Merge in this order so `dev` stays clean:

| Order | PR | Branch | What it adds |
|-------|-----|--------|--------------|
| 1 | [#4](https://github.com/McNeeseACMChapter/askmcneese/pull/4) | `feature/pm-sprint1` | FastAPI `/health`, `docs/db_schema.md`, `.env.example`, `docs/setup.md` |
| 2 | [#5](https://github.com/McNeeseACMChapter/askmcneese/pull/5) | `feature/frontend-shell` | React chat shell (FE-01..FE-05), frontend rulebook, screenshots |
| 3 | [#6](https://github.com/McNeeseACMChapter/askmcneese/pull/6) | `feature/pm-week1-review` | This review doc + backlog status update (PM-06) |
| 4 | [#3](https://github.com/McNeeseACMChapter/askmcneese/pull/3) | `feature/backend-pipeline` | Crawler → cleaner → chunker → ChromaDB (BE-01..BE-05) |

> PR #5 stacks on #4. Merge #4 first.

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
| CK-04 | 15 starter test questions | ⬜ Not done | `knowledge/test_questions_week1.md` missing |
| CK-05 | Handoff to Backend | ⚠️ Partial | CSV readable by crawler; **all rows still `Pending` approval** |

**Blockers:**
- PM must formally approve sources (`approval_status` still Pending on all 30 rows).
- CK-04 test questions still needed for QA smoke tests in Sprint 2.

---

### DevOps / QA

| Ticket | Task | Status | Proof |
|--------|------|--------|-------|
| DQ-01 | Validate repo setup | ⚠️ Partial | `docs/setup.md` exists (PM-05); no `docs/qa/week1_setup_notes.md` |
| DQ-02 | PR checklist | ⬜ Not done | `docs/qa/pr_checklist.md` missing |
| DQ-03 | Week 1 smoke tests | ⚠️ Partial | Manually proven (health, frontend, crawler); not formalized in `docs/qa/` |
| DQ-04 | Simple CI | ⬜ Not done | No CI workflow yet |
| DQ-05 | Sprint review proof | ⚠️ Partial | Screenshots + samples exist; QA evidence folder not consolidated |

**Blockers:** DevOps/QA teammate should file formal checklists in Sprint 2 Week 1 carry-over.

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
| 1 | PRs #3–#5 not merged to `dev` | PM | Merge in order (#4 → #5 → #6 → #3) |
| 2 | Backend dev realignment (Django → FastAPI) | PM + Backend | Use PR #3 as reference; schedule sync |
| 3 | `www.mcneese.edu` 403 bot protection | PM + Backend | Decide: alternate fetch, sitemap, or contact web team |
| 4 | Source registry approval (30 Pending) | PM | Review CSV and set `approval_status` |
| 5 | CK-04 test questions missing | Content | Create `knowledge/test_questions_week1.md` |
| 6 | Formal QA docs missing | DevOps/QA | `docs/qa/pr_checklist.md`, `week1_smoke_tests.md` |

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

**Ready to start when:**
1. PRs #4 and #5 are merged to `dev`.
2. Backend developer acknowledges FastAPI + crawler realignment plan.
3. PM approves at least the first batch of registry URLs.

**Suggested Sprint 2 focus:** wire `/ask` endpoint (retrieval only), connect frontend send button to API, expand approved sources, formalize QA smoke tests.

---

*Generated as part of PM-06. Internal PM timeline: Ticket #21.*
