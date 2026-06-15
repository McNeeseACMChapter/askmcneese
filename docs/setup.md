# Local Setup Guide — AskMcNeese (PM-05)

How to clone the project and run the Sprint 1 pieces locally: the **backend API** (`/health`)
and the **crawler pipeline** (ingest one approved page). No secrets are required this sprint.

## 0. Prerequisites

- **Python 3.12+**
- **git**
- (Frontend later) Node.js 18+ — not needed for the steps below

## 1. Clone and configure

```bash
git clone https://github.com/McNeeseACMChapter/askmcneese.git
cd askmcneese
cp .env.example .env      # Windows: copy .env.example .env
```

`.env` is git-ignored. `.env.example` lists every variable — there are no secrets in Sprint 1.

## 2. Run the backend API (`/health`) — PM-03

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then check it:

- Open <http://127.0.0.1:8000/health> → expect:

```json
{ "status": "ok", "service": "askmcneese-api", "version": "0.1.0" }
```

- Interactive docs: <http://127.0.0.1:8000/docs>

This `/health` endpoint is what the frontend pings on load.

## 3. Run the crawler pipeline — (Backend BE-01..BE-05)

```bash
cd crawler
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python ingest.py --url https://catalog.mcneese.edu/
```

Expect a line like `INGESTED ... chunks=3 ... stored_total=3`. See `crawler/README.md` for
how to verify the data and search it.

> Note: `www.mcneese.edu` currently returns **403** to programmatic requests (bot protection).
> Use a reachable approved source (e.g. `catalog.mcneese.edu`) until that's resolved.

## 4. Required environment variables

All configuration lives in `.env` (copied from `.env.example`). Summary:

| Variable | Used by | Meaning |
|----------|---------|---------|
| `API_HOST`, `API_PORT` | backend | Where the API binds |
| `CORS_ALLOW_ORIGINS` | backend | Frontend origin(s) allowed to call the API |
| `SOURCE_REGISTRY_PATH` | crawler | Path to the approved source list |
| `CRAWLER_USER_AGENT`, `REQUEST_TIMEOUT_SECONDS` | crawler | Fetch behavior |
| `ALLOW_PENDING_SOURCES` | crawler | Allow crawling not-yet-approved sources (Week 1 proof) |
| `CHUNK_SIZE_TOKENS`, `CHUNK_OVERLAP_TOKENS` | crawler | Chunking parameters |
| `CHROMA_DB_PATH`, `CHROMA_COLLECTION` | crawler | Where chunks are stored |

## 5. Branch & contribution rules

- Branch off `dev` as `feature/<name>`. **Never push directly to `main`** (reserved for milestones).
- No secrets in commits. No private/login-only/student data. No production deploy in Week 1.
