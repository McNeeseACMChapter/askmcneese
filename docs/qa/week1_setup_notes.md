# Week 1 Setup Validation Notes — AskMcNeese (DQ-01)

Log of issues found when validating a **clean clone** against `docs/setup.md`.
Update this file when a new teammate hits setup friction.

**Last validated:** June 14, 2026  
**Validator:** PM (reference implementation path)

---

## What worked

| Step | Notes |
|------|-------|
| Clone + `.env` copy | Straightforward |
| Backend venv + `uvicorn` | `/health` returns 200 on default port 8000 |
| Crawler ingest on `catalog.mcneese.edu` | 3+ chunks stored in ChromaDB |
| Frontend `npm run build` | Type-check + bundle pass |
| Frontend + backend together | Health badge shows **Online · v0.1.0** |

---

## Known issues & workarounds

### 1. `www.mcneese.edu` Cloudflare block

**Symptom:** Plain HTTP returned 403 ("Just a moment…").  
**Resolved:** Playwright browser fallback in crawler (PR #9).  
**Doc:** `docs/crawler_403_strategy.md`

### 2. Windows may block port 8000

**Symptom:** `uvicorn` bind error on `127.0.0.1:8000` (WinError 10013).  
**Workaround:** Run on another port, e.g. `uvicorn app.main:app --port 8123`, and set `VITE_API_BASE_URL=http://127.0.0.1:8123` in `frontend/.env`.

### 3. ChromaDB first-run download

**Symptom:** First `ingest.py` run downloads an embedding model (one-time, needs network).  
**Workaround:** Wait for download to finish; subsequent runs are offline.

### 4. Two separate Python venvs

**Symptom:** Confusion about one venv for backend vs crawler.  
**Workaround:** `backend/.venv` and `crawler/.venv` are intentional — different `requirements.txt` files.

### 5. Frontend env var location

**Symptom:** `VITE_API_BASE_URL` not found.  
**Workaround:** Copy `frontend/.env.example` → `frontend/.env` (not the repo-root `.env`).

---

## CI (DQ-04)

GitHub Actions runs on every **push** and **pull request** to `dev`:

- **Backend import check** — `pip install` + `from app.main import app`
- **Frontend build** — `npm ci` + `npm run build`

Workflow file: `.github/workflows/ci.yml`

---

## Suggested improvements (backlog)

- [ ] Add `scripts/validate_setup.ps1` one-command smoke runner (Sprint 2)
- [x] GitHub Actions CI: backend import check + frontend build (DQ-04)
- [ ] Document port 8000 Windows reserved-range check in `docs/setup.md`
