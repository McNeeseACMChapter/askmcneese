# Sprint 2 Readiness — AskMcNeese

**Purpose:** Confirm Sprint 1 is complete enough for the team to start Sprint 2 work.
**Sprint 2 theme:** Retrieval + `/ask` wiring (no LLM answer generation yet).

---

## Sprint 1 closure checklist

| Item | Status | Where |
|------|--------|-------|
| Repo + branches on `dev` | ✅ | GitHub |
| PM-01 → PM-06 | ✅ | `docs/week1_review.md` |
| FE-01 → FE-05 (shell + `/health`) | ✅ | `frontend/` |
| BE-01 → BE-05 (crawler pipeline) | ✅ | `crawler/` |
| CK-01 → CK-03 (registry seed) | ✅ | `knowledge/source_registry_seed.csv` |
| CK-04 (test questions) | ✅ | `knowledge/test_questions_week1.md` |
| CK-05 (PM source approval) | ✅ | 12 sources `Approved` in registry |
| DQ-01..DQ-03 (QA docs) | ✅ | `docs/qa/` |
| DQ-04 (CI) | ✅ Done | `.github/workflows/ci.yml` |
| 403 strategy documented | ✅ | `docs/crawler_403_strategy.md` |
| Backend dev realignment | ⏳ Human conversation | PM + Landon |

**Verdict:** System is **ready for Sprint 2 development** on `dev`. Assigned Backend developer
still needs a sync meeting — the reference code on `dev` is the target.

---

## What Sprint 2 will build (not started yet)

| Ticket | Owner | Deliverable | Branch |
|--------|-------|-------------|--------|
| BE-06 | Backend | `POST /ask` — retrieve top chunks from ChromaDB, return citations | `feature/backend-ask` |
| BE-07 | Backend | Query logging (`query_logs` JSONL) | `feature/backend-ask` |
| FE-06 | Frontend | Wire Send button → `POST /ask`, show cited snippets | `feature/frontend-ask` |
| BE-08 | Backend | Expand ingest to more **Approved** sources | `feature/crawler-expand` |

**Still out of scope:** LLM generation, Canvas, SSO, production deploy, citation UI polish.

---

## Before your first Sprint 2 branch

```bash
git checkout dev
git pull origin dev

# 1. Backend health
cd backend && uvicorn app.main:app --reload

# 2. Ingest at least one approved source (if chroma_db empty)
cd ../crawler && python ingest.py --url https://catalog.mcneese.edu/

# 3. Frontend shell
cd ../frontend && npm install && npm run dev
```

Confirm: health badge **Online**, ingest shows chunks stored, `npm run build` passes.

---

## Environment variables (Sprint 2 additions)

Add to your local `.env` when implementing `/ask` (placeholders in `.env.example`):

| Variable | Used by | Purpose |
|----------|---------|---------|
| `CHROMA_DB_PATH` | backend + crawler | Shared ChromaDB path (must match) |
| `CHROMA_COLLECTION` | backend + crawler | Collection name (must match) |
| `RETRIEVAL_TOP_K` | backend | Number of chunks to return per question |
| `VITE_API_BASE_URL` | frontend | Backend URL (`frontend/.env`) |

---

## Test questions for Sprint 2 QA

Use `knowledge/test_questions_week1.md` — 15+ questions mapped to expected sources.
A Sprint 2 `/ask` response passes when returned chunks cite the expected registry URL.

---

## Open human blockers (not code)

1. **Backend developer sync** — acknowledge FastAPI + `crawler/` on `dev`
2. **403 on www.mcneese.edu** — PM picks long-term option in `docs/crawler_403_strategy.md`
3. **Sensitive sources** (Emergency, Title IX) — remain Pending until PM explicitly approves

---

*Updated when Sprint 1 carry-over work landed on `dev`.*
