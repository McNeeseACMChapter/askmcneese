# Week 1 Smoke Tests — AskMcNeese (DQ-03)

Manual smoke tests that prove Sprint 1 foundation works. Run these **before marking Sprint 1 Done**
or **before starting Sprint 2** on a fresh clone.

**Tester:** _______________  
**Date:** _______________  
**Branch:** `dev`  
**OS:** _______________

---

## 1. Repo & setup (DQ-01)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 1.1 | Clone succeeds | `git clone … && cd askmcneese` | No errors | ☐ |
| 1.2 | Env template exists | `copy .env.example .env` | File created | ☐ |
| 1.3 | Setup doc readable | Open `docs/setup.md` | Steps are followable | ☐ |

## 2. Backend — `GET /health` (PM-03)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 2.1 | API starts | `cd backend && uvicorn app.main:app --reload` | Server on :8000 | ☐ |
| 2.2 | Health JSON | `curl http://127.0.0.1:8000/health` | `status: ok`, `version: 0.1.0` | ☐ |
| 2.3 | OpenAPI docs | Browser → `/docs` | Swagger UI loads | ☐ |

## 3. Crawler pipeline (BE-01..BE-05)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 3.1 | Ingest catalog | `cd crawler && python ingest.py --url https://catalog.mcneese.edu/` | `chunks=N`, `stored_total=N` | ☐ |
| 3.2 | Samples exist | Check `docs/samples/chunks_sample.json` | Valid JSON with metadata | ☐ |
| 3.3 | Registry gate | Try unlisted URL in `ingest.py` | Rejected / not in registry | ☐ |

## 4. Frontend shell (FE-01..FE-05)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 4.1 | Install + build | `cd frontend && npm install && npm run build` | Exit 0 | ☐ |
| 4.2 | Dev server | `npm run dev` | UI at :5173 | ☐ |
| 4.3 | Health badge | Backend running + frontend open | Header shows **Online** | ☐ |
| 4.4 | Screenshots on file | `docs/screenshots/week1_frontend/` | mobile + desktop PNGs | ☐ |

## 5. Content (CK-01..CK-04)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 5.1 | Registry exists | `knowledge/source_registry_seed.csv` | 30 rows | ☐ |
| 5.2 | PM approvals | Filter `Approval Status = Approved` | ≥ 10 approved sources | ☐ |
| 5.3 | Test questions | `knowledge/test_questions_week1.md` | ≥ 15 questions with categories | ☐ |

## 6. Sprint 2 readiness (not implemented yet)

| # | Test | Command / action | Expected | Pass? |
|---|------|------------------|----------|-------|
| 6.1 | `/ask` endpoint | `POST /ask` with a test question | **Not required in Sprint 1** — Sprint 2 | N/A |
| 6.2 | Frontend real answers | Send in chat UI | **Not required in Sprint 1** — Sprint 2 | N/A |

---

## Result summary

| Area | Status |
|------|--------|
| Setup | ☐ Pass ☐ Fail |
| Backend `/health` | ☐ Pass ☐ Fail |
| Crawler | ☐ Pass ☐ Fail |
| Frontend shell | ☐ Pass ☐ Fail |
| Content | ☐ Pass ☐ Fail |

**Blockers found:** _______________________________________________

**Signed off by PM:** _______________  **Date:** _______________
