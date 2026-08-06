# AskMcNeese

AskMcNeese is a campus AI assistant for McNeese State University, built by the
McNeese ACM Student Chapter. Students ask ordinary questions about scholarships,
admissions, programs, and campus services, and get answers grounded in approved
public McNeese sources.

There is no student login in this version. Chat history stays in the browser.
Private systems such as Canvas grades or personal records are out of scope.

## How the pieces fit together

```text
knowledge/        approved source lists (official campus + gated companions)
   │
crawler/          OFFLINE: fetch → clean → chunk → embed  (writes ChromaDB)
   │
ChromaDB          local vector store (shared handoff point)
   │
backend/          ONLINE: FastAPI /ask → retrieve → write a cited answer
   │
frontend/         React chat UI (streams live activity + the answer)
```

Safety rules that keep the product predictable:

- The crawler is the only writer to ChromaDB.
- The backend is the only reader at request time; it never writes chunks.
- Answers are meant to come from approved sources in `knowledge/`, not from open-web guessing.

## What works in this version

- Public chat UI with markdown answers and clickable sources
- Knowledge-base mode (saved campus pages) and optional live `mcneese.edu` web mode
- Selective hybrid retrieval (RCCS) that can mix saved knowledge and live official pages
- Optional research helper channel (Perplexity), controlled by feature flags
- Live “what we are doing” activity trail while an answer is building
- Structured answer sections when the model can extract them (facts, steps, warnings)
- About, Updates, Usage, Settings, and Feedback screens
- Companion source registry kept separate from official campus sources

## Folder map

| Folder | What it does |
|--------|--------------|
| `backend/` | FastAPI app. `/health`, `/ask`, retrieval, answer writing, web search, RCCS |
| `crawler/` | Offline ingestion: fetch, clean, chunk, embed into ChromaDB |
| `frontend/` | React + Vite + Tailwind chat interface |
| `knowledge/` | Approved official sources and companion allow-lists |
| `docs/` | Architecture notes, design records, RCCS reports, and public guides |

## The vector database (ChromaDB)

We use ChromaDB as a local store for text embeddings. When a user asks a question,
we embed the question and compare it to stored vectors to find relevant text.
This is a prototype store, not the long-term production database.

Default path: `CHROMA_DB_PATH` (`crawler/chroma_db`)  
Default collection: `CHROMA_COLLECTION` (`askmcneese_sources`)

## Requirements

- Python 3.12+
- Node.js 18+ (frontend)
- An Anthropic API key for answer writing (retrieval still works without it)
- Optional provider keys if you turn on live research helpers (see `.env.example`)

## Setup and running

### 1. Configure environment

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Edit `.env` and set at least `ANTHROPIC_API_KEY`. Never commit a real `.env`.

### 2. Backend API

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health
- Docs: http://127.0.0.1:8000/docs
- Ask: `POST /ask` with `{"question": "..."}`

If port 8000 is busy, use 8001 and point the frontend at the same port.

### 3. Ingestion CLI (crawler)

```bash
cd crawler
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium   # only for Cloudflare-blocked pages

python ingest.py
python ingest.py --url https://www.mcneese.edu/
python ingest.py --all --limit 3
```

### 4. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev               # http://localhost:5173
```

Set `VITE_API_BASE_URL` to match the backend host and port.

## Tests and build

```bash
cd backend
python -m unittest discover -s tests/unit -p "test_*.py"
```

```bash
cd frontend
npm run test
npm run build
```

## Important environment variables

| Variable | Used by | Meaning |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | backend | Answer writing key |
| `CLAUDE_MODEL` | backend | Model name for answers |
| `CHROMA_DB_PATH` | crawler + backend | On-disk ChromaDB location |
| `CHROMA_COLLECTION` | crawler + backend | Collection name |
| `RCCS_ENABLED` | backend | Turn selective hybrid retrieval on or off |
| `PERPLEXITY_AGENTIC_ENABLED` | backend | Optional research helper channel |
| `WEB_BROWSING_ENABLED` | backend | Allow live browsing providers |
| `ASKMCNEESE_DEBUG_TRACE` | backend | Extra pipeline fields in query logs |

See `.env.example` for the full list and safe defaults.

## Branches

- `main` is for stable reviewed milestones
- `dev` is the active working branch
- `feature/*` is for focused task work off `dev`

Do not push directly to `main`.

## Attribution

AskMcNeese is built by the McNeese ACM Student Chapter as a student-led software
project focused on trusted campus information access.
