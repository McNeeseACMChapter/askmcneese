# Backend - AskMcNeese

FastAPI application for the AskMcNeese campus assistant.

## What it provides

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness, version, and retrieval capabilities |
| `POST /ask` | Campus Q&A (streams when `stream: true`) |
| `GET /ask/stats` | Knowledge-base, pipeline, and model status |

## Retrieval modes

- Default: saved McNeese knowledge base (`use_web_search: false`)
- Optional live official pages (`use_web_search: true`)
- Selective hybrid retrieval when `RCCS_ENABLED=1`
- Optional research helper channel when Perplexity flags are enabled

Answers are written from retrieved evidence with citations. There is no authentication
in this version. Personal or login-only student data is out of scope.

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If port 8000 is busy, use `--port 8001` and point the frontend at the same port.

- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs

## Tests

```bash
python -m unittest discover -s tests/unit -p "test_*.py"
```

## Structure

```
backend/app/
├── main.py
├── routers/          # health, ask
└── services/         # retrieval, llm, web search, RCCS, activity, structured answers
```

The crawler writes ChromaDB. This backend reads it at request time and never writes chunks.

## Useful docs

- `docs/rccs/` for selective hybrid retrieval
- `docs/LIVE_ACTIVITY_EVENTS.md` for streaming activity events
- `docs/RESPONSE_SCHEMA.md` for answer shape
- `docs/developer_guide_backend.md` for onboarding notes
