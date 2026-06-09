# Backend — AskMcNeese (Sprint 1)

> Owner: **Landon Peutera**
> Status: **Not implemented yet — left intentionally for the Backend role.**

This folder is reserved for the FastAPI application that powers AskMcNeese.

## Sprint 1 deliverables for this folder

Per `README.md` and the Sprint 1 plan, the Backend role is responsible for:

1. Bootstrapping a FastAPI app.
2. Exposing a `GET /health` endpoint that returns a simple JSON status.
3. Establishing a clean folder structure for future services (routers, models, services, etc.).
4. Wiring backend logic that the retrieval pipeline (`crawler/`) and frontend (`frontend/`) will later use.

## Suggested starting structure (not yet created)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI entrypoint
│   ├── routers/
│   │   └── health.py      # GET /health
│   ├── models/
│   └── services/
├── requirements.txt
└── README.md              # (this file)
```

## Notes

- Keep `GET /health` lightweight — it is what the frontend pings on load.
- Do NOT add any private, authenticated, or student-record data handling in Sprint 1.
- All retrieval logic that touches public McNeese pages lives in `crawler/`, not here.

---

*This README is a placeholder so the folder exists in git and the Backend teammate has a clear starting point.*
