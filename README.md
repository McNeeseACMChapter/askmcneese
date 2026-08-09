# AskMcNeese

AskMcNeese is a source-grounded campus assistant and class-planning experience for McNeese State University, built by the McNeese ACM Student Chapter.

> **Release status: Beta sprint completed (2026-08-08).** This release is a beta candidate and is subject to change when production bugs, source gaps, accessibility issues, or operational risks are discovered.

## What is included

- **Ask:** streamed campus answers with visible activity, structured content, and citations.
- **Class Planner:** Fall 2026 course discovery, section comparison, conflict checking, local schedules, and a visual week.
- **Guest onboarding:** anonymous HttpOnly-cookie identity and a mandatory 14-step first-visit walkthrough.
- **Public information pages:** About, Updates, Usage, Settings, and Feedback.
- **Governed retrieval:** indexed McNeese sources, selective live official-page reads, approved companion sources, and optional research providers.
- **ACM Panel:** a separate internal chapter-operations prototype under `acm/`.

No McNeese login is required for the public beta. Conversation history and planned classes remain in the browser. Private student records, Canvas grades, DegreeWorks, Banner writes, and other authenticated data are outside this release.

## System map

```text
knowledge/            governed source registries and search intelligence
    |
crawler/              offline discovery, fetch, clean, chunk, and ingest
    |
ChromaDB              local retrieval index written only by the crawler
    |
backend/              FastAPI: Ask, guest onboarding, Class Planner read API
    |
frontend/             React application at /ask, /class-planner, and public pages

acm/                   separate ACM chapter-operations application
```

Operational boundaries:

- The crawler is the only ChromaDB writer.
- The Ask backend reads evidence and produces cited answers; it does not ingest chunks at request time.
- The Class Planner backend publishes only validated normalized datasets and keeps the prior valid dataset if synchronization fails.
- Guest cookies contain opaque session tokens; only hashes are stored server-side.
- External and companion sources are discovery/evidence channels, not substitutes for official McNeese policy.

## Repository map

| Path | Responsibility |
| --- | --- |
| `frontend/` | React, Vite, TypeScript, responsive public interface |
| `backend/` | FastAPI Ask pipeline, guest state, and Class Planner API |
| `crawler/` | Governed discovery, HTML/PDF ingestion, and index tooling |
| `knowledge/` | Source registries, taxonomy, and search-intelligence artifacts |
| `docs/` | Architecture, release records, implementation notes, and audits |
| `acm/` | Separate internal ACM Panel prototype |

## Requirements

- Python 3.12+
- Node.js 18+
- An Anthropic API key for generated answers
- Optional provider keys for enabled web/research channels
- Playwright Chromium when browser-assisted crawling is required

## Local setup

### 1. Environment

```powershell
Copy-Item .env.example .env
```

Set `ANTHROPIC_API_KEY` and review the feature flags before running. Never commit `.env`.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: <http://127.0.0.1:8000/health>
- OpenAPI: <http://127.0.0.1:8000/docs>
- Ask: `POST /ask`
- Guest bootstrap: `POST /guest/bootstrap`
- Class Planner terms: `GET /class-planner/terms`

If another port is used, set the frontend `VITE_API_BASE_URL` to the same origin.

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

The default development URL is <http://127.0.0.1:5173>.

### 4. Crawler

```powershell
cd crawler
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python ingest.py --all --limit 3
```

See [`crawler/README.md`](crawler/README.md) before running broad discovery or ingestion.

## Validation

```powershell
cd frontend
npm run typecheck
npm run test
npm run build
```

```powershell
cd backend
python -m unittest discover -s tests/unit -p "test_*.py"
```

The beta completion checks and known limitations are recorded in [`docs/BETA_SPRINT_COMPLETION.md`](docs/BETA_SPRINT_COMPLETION.md).

## Important configuration

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Frontend API origin |
| `VITE_CLASS_DATA_MODE` | `mock`, `staging`, or `live` planner data mode |
| `VITE_CLASS_TERM_ID` | Planner term identifier, currently `202660` |
| `CORS_ALLOWED_ORIGINS` | Explicit credentialed frontend origins |
| `ONBOARDING_MODE` | `mandatory`, `optional`, or `disabled` guest tour policy |
| `GUEST_DB_PATH` | Persistent SQLite guest-session, quota, and feedback store |
| `GUEST_QUESTION_LIMIT` | Per-browser beta question allowance (default `10`) |
| `FEEDBACK_ADMIN_TOKEN` | Secret header token for the feedback review endpoint |
| `CLASS_PLANNER_DB_PATH` | SQLite normalized class dataset |
| `CLASS_SYNC_ENABLED` | Enables scheduled class-source synchronization |
| `CHROMA_DB_PATH` | Local retrieval index path |
| `RCCS_ENABLED` | Selective hybrid retrieval controller |
| `WEB_BROWSING_ENABLED` | Live browsing provider gate |
| `PERPLEXITY_AGENTIC_ENABLED` | Optional research provider gate |
| `ASKMCNEESE_DEBUG_TRACE` | Additional diagnostic query fields |

See [`.env.example`](.env.example) for the complete safe template.

## Documentation

Start with [`docs/README.md`](docs/README.md). The current feature guides are:

- [`frontend/README.md`](frontend/README.md)
- [`backend/README.md`](backend/README.md)
- [`crawler/README.md`](crawler/README.md)
- [`docs/onboarding/README.md`](docs/onboarding/README.md)
- [`docs/class-planner/README.md`](docs/class-planner/README.md)
- [`docs/BRAND_LOGO_RULES.md`](docs/BRAND_LOGO_RULES.md)

## Branches

- `main`: reviewed milestones
- `dev`: active integration branch
- `feature/*`: focused work branched from `dev`

Do not push directly to `main`.

## Attribution

AskMcNeese is a student-led McNeese ACM project focused on making campus information easier to find, understand, and verify.
