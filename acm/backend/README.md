# ACM backend — modular monolith

All ACM API code lives under this tree (not under `askmcneese/backend` AskMcNeese RAG).

```text
backend/
├── identity/
├── memberships/
├── authorization/
├── governance/
├── meetings/
├── projects/
├── events/
├── finance/
├── sga/
├── communications/
├── documents/
├── notifications/
├── reporting/
└── audit/
```

Each module should eventually contain:

```text
models/
schemas/
repository/
service/
policy/
workflow/
routes/
events/
tests/
```

Business rules belong in **services** and **policies**, not route handlers.

## Implementation status

| Module | Phase | Status |
|--------|-------|--------|
| identity | 1 | Scaffold only |
| memberships | 1 | Scaffold only |
| authorization | 1 | Project-management policy slice live |
| audit | 1 | Project mutation events live; broader module scaffold |
| notifications | 1 | Scaffold only |
| governance | 2 | Scaffold only |
| meetings | 2 | Scaffold only |
| documents | 2 | Scaffold only |
| projects | 3 | Persistent managed-edit slice live |
| events | 4 | Scaffold only |
| finance | 5 | Scaffold only — blocked until auth+audit proven |
| sga | 5 | Scaffold only |
| communications | 6 | Scaffold only |
| reporting | 7 | Scaffold only |

See module `README.md` files in each subdirectory.

## Implemented persistence foundation

The first durable vertical slice now lives in `app/main.py`.

- FastAPI boundary at `http://127.0.0.1:3101`
- SQLite development adapter at `data/acm.sqlite3` (ignored by Git)
- Project reads and managed project-field updates
- Owner/role policy enforcement for `project.manage`
- Required change reason and append-only audit event
- Whole-platform data/access contract endpoint

Run locally from the repository root:

    backend\.venv\Scripts\python.exe -m uvicorn acm.backend.app.main:app --host 127.0.0.1 --port 3101

SQLite is a local adapter, not the production authority. The production target remains PostgreSQL plus object storage, with institutional identity replacing the fixture identity headers.