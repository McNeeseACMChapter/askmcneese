# AskMcNeese Class Planner

Class Planner helps students search McNeese's published classes, compare sections, detect schedule conflicts, and prepare a week before registering in the official student system. It never registers a student and never writes to Banner.

The visual product is locked. The production-data work changes the source, storage, freshness, and loading behavior without redesigning the approved Week Pulse, timeline, desktop calendar, mobile tabs, color system, or motion.

## Data contract

- Authority: `https://schedule.mcneese.edu/`
- Production database: same-region managed PostgreSQL
- Local/test database: SQLite only
- Published scope: current term and the next term when McNeese publishes it
- Normal reads: PostgreSQL/SQLite only; search never scrapes McNeese
- Full sync: protected GitHub Actions trigger, bounded to four workers by default
- Availability: recently opened courses refresh every five minutes, stale course opens queue a targeted refresh, and Add attempts a targeted verification
- Planning boundary: seat counts and closed status are registration context only; zero-seat and closed sections remain addable because Class Planner never registers a student
- Failure rule: retain the last-known-good snapshot; Add may continue with an explicit unable-to-reverify disclosure
- Large courses: course summaries load first and section detail is paged six at a time
- Registration prose: stored as notes/restrictions/corequisites, never as instructor identity
- Production failure: HTTP 503 when no validated dataset exists; no mock or SQLite fallback

## Local bootstrap

From `backend`:

```powershell
Copy-Item ..\.env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.services.class_planner.pipeline --term 202660
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

For local SQLite, leave `DATABASE_URL` empty, set `CLASS_DATA_MODE=staging`, and set `CLASS_PLANNER_DB_PATH=class_planner_v2.sqlite3`.

From `frontend`:

```powershell
npm ci
npm run dev
```

Use `VITE_CLASS_DATA_MODE=staging`, `VITE_API_BASE_URL=http://127.0.0.1:8000`, and the published source term ID.

## Production bootstrap gate

1. Create the Render Blueprint resources from `render.yaml`.
2. Confirm the API and PostgreSQL are in the same Render region.
3. Set `CLASS_SYNC_ADMIN_TOKEN` and the frontend `VITE_API_BASE_URL`.
4. Apply `python -m alembic upgrade head`.
5. Set GitHub secrets `CLASS_PLANNER_BACKEND_URL` and `CLASS_SYNC_ADMIN_TOKEN`.
6. Set GitHub variable `CLASS_PLANNER_TERM_IDS` to the published current term and, once available, next term (comma-separated).
7. Trigger **Class Planner full sync** manually.
8. Verify `/class-planner/terms`, `/class-planner/freshness`, search, section paging, and direct section lookup.
9. Verify zero rejected records or investigate every rejection.
10. Change `VITE_CLASS_DATA_MODE` from `staging` to `live` only after the database and API smoke gates pass.

Rollback is an operator action through `ClassPlannerStore.rollback(term_id, dataset_id)` using a retained dataset. Four snapshots per term are retained by default.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system model and [IMPLEMENTATION_RECORD.md](IMPLEMENTATION_RECORD.md) for measured results and production readiness.
