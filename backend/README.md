# AskMcNeese Backend

FastAPI service for source-grounded Ask responses, anonymous guest onboarding, and the read-only Class Planner API.

> **Beta sprint completed 2026-08-08.** Contracts may change to address production bugs, security findings, source changes, or operational requirements.

## API surface

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Service version, health, and retrieval capabilities |
| `POST /ask` | Non-streaming or SSE campus answer pipeline |
| `GET /ask/stats` | Knowledge, model, and pipeline status |
| `POST /guest/bootstrap` | Create or resume an anonymous guest session |
| `PATCH /guest/tour` | Persist tour progress |
| `POST /guest/tour` | Compatibility alias for progress persistence |
| `POST /guest/tour/replay` | Restart the tour for the same guest |
| `POST /guest/dev-reset` | Development-only progress reset |
| `GET /class-planner/terms` | Published terms |
| `GET /class-planner/courses` | Search and filter normalized courses |
| `GET /class-planner/courses/{course_id}` | Course and section detail |
| `GET /class-planner/sections/{section_id}` | Normalized section detail |
| `GET /class-planner/freshness` | Current published source metadata |

OpenAPI documentation is available at `/docs` while the server is running.

## Ask pipeline

The request path combines intent classification, query planning, governed retrieval, evidence ranking, optional official-page browsing, optional companion research, answer generation, structured presentation, and citation validation. Streaming clients receive activity, answer chunks, citations, completion metadata, and errors through Server-Sent Events.

The backend must not claim an unsupported fact. Official decisions should remain tied to official evidence even when external sources help discovery or context.

## Data ownership

| Store | Writer | Reader | Purpose |
| --- | --- | --- | --- |
| ChromaDB | crawler | Ask backend | Indexed source chunks |
| Guest SQLite | guest service | guest service | Hashed anonymous identity and tour state |
| Class Planner PostgreSQL (SQLite local/test) | protected sync pipeline | planner routes | Last validated normalized class dataset and availability overlay |
| Browser local storage | frontend | frontend | Conversations and planned schedule |

The Class Planner publisher is transactional. Failed or suspicious synchronization does not replace the last validated dataset. GitHub Actions owns recurring sync; the web process has no scheduler loop, and live mode requires PostgreSQL.

## CORS and cookies

Guest progress uses explicit credentialed origins, never `*`, and accepts both `POST` and `PATCH` tour writes. The browser persists the anonymous bootstrap token locally and sends `X-Guest-Token`, so a cross-origin production frontend does not depend on a third-party cookie. The API still sets an HttpOnly cookie as a same-site fallback. Configure `CORS_ALLOWED_ORIGINS`; `CORS_ALLOW_ORIGINS` remains a legacy alias.

Production HTTPS should set `GUEST_COOKIE_SECURE=true`. `GUEST_DB_PATH` must point to persistent storage or guest numbers, quota usage, and feedback will reset when the service filesystem is replaced.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: <http://127.0.0.1:8000/health>
- OpenAPI: <http://127.0.0.1:8000/docs>

## Tests

```powershell
cd backend
python -m unittest discover -s tests/unit -p "test_*.py"
```

Focused beta features:

```powershell
python -m unittest tests.unit.test_guest_onboarding tests.unit.test_class_planner_data -v
```

## Structure

```text
backend/app/
|-- main.py
|-- routers/
|   |-- ask.py
|   |-- class_planner.py
|   |-- guest.py
|   `-- health.py
`-- services/
    |-- class_planner/
    |-- guest/
    |-- retrieval and ranking services
    |-- web and companion research services
    `-- answer, activity, and citation services
```

## Production checklist

- Set explicit HTTPS frontend origins.
- Set `GUEST_COOKIE_SECURE=true`.
- Put `GUEST_DB_PATH` on persistent storage and set `GUEST_QUESTION_LIMIT=10`.
- Set a long random `FEEDBACK_ADMIN_TOKEN`.
- Disable `ONBOARDING_DEV_RESET`.
- Keep secrets outside the repository.
- Validate and publish a Class Planner dataset before selecting staging/live mode.
- Confirm ChromaDB collection and source-registry versions.
- Review provider timeouts, quotas, and fallback policy.
- Run unit, contract, security, and representative question evaluations.
- Monitor latency, failed retrieval, citation mismatch, and guest persistence errors.

## Related documentation

- [`../docs/BETA_SPRINT_COMPLETION.md`](../docs/BETA_SPRINT_COMPLETION.md)
- [`../docs/onboarding/ARCHITECTURE.md`](../docs/onboarding/ARCHITECTURE.md)
- [`../docs/class-planner/ARCHITECTURE.md`](../docs/class-planner/ARCHITECTURE.md)
- [`../docs/rccs/`](../docs/rccs/)
