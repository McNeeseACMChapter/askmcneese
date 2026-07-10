# AskMcNeese

AskMcNeese is a campus AI assistant and ingestion system for McNeese State
University. Students ask questions in plain language ("What scholarships can a
transfer student get?") and get a source-grounded answer built only from public
McNeese information.

The project has two halves:

- an **ingestion system** that fetches approved public McNeese pages and PDFs,
  cleans them, splits them into chunks, and stores them as text embeddings; and
- a **question-answering API + web UI** that retrieves the most relevant chunks
  for a question and uses Claude to write a cited answer.

## How the pieces fit together

```text
knowledge/        approved source registry (allow-list of public URLs)
   │
crawler/          OFFLINE: fetch → clean → chunk → embed  (writes ChromaDB)
   │
ChromaDB          local vector store (the shared handoff point)
   │
backend/          ONLINE: FastAPI /ask → retrieve → Claude → cited answer
   │
frontend/         React + Vite + Tailwind chat UI (calls /ask and /health)
```

The rule that keeps this safe and predictable:

- **The crawler is the only writer** to ChromaDB.
- **The backend is the only reader** at request time; it never writes.
- **Everything a student sees originated from an approved URL** in
  `knowledge/`.

The backend also supports a **live web search** mode that fetches
`mcneese.edu` pages in real time, in addition to the pre-indexed knowledge base.

### Components

| Folder      | What it does |
|-------------|--------------|
| `backend/`  | FastAPI app. Routers (`/health`, `/ask`) and services (retrieval, LLM, intent, persona, query expansion, rerank, web search, query logging). |
| `crawler/`  | Offline ingestion pipeline: `crawler.py` (fetch), `clean_text.py` (strip nav/scripts, keep tables/lists), `chunker.py` (chunk + metadata), `ingest.py` / `ingest_pdf.py` (write to ChromaDB). |
| `frontend/` | React + Vite + Tailwind chat interface. Streams answers from `/ask`. |
| `knowledge/`| Approved source registry (public McNeese URLs, categories, trust tiers). |
| `docs/`     | Architecture notes, developer guide, sprint records, and the dev log. |

## The vector database (ChromaDB)

We use ChromaDB, a lightweight local vector database, to store text embeddings.
When a user asks a question, we embed the question and compare it to these
stored vectors to retrieve relevant text chunks. Currently, ChromaDB runs
locally and is not the long-term production solution; it serves as our
prototype's data store.

The store lives on disk at `CHROMA_DB_PATH` (default `crawler/chroma_db`) in the
collection named by `CHROMA_COLLECTION` (default `askmcneese_sources`).

## Requirements

- Python 3.12+
- Node.js 18+ (for the frontend)
- An Anthropic API key for LLM answer generation (retrieval works without it,
  but answers fall back to a plain source summary)

## Setup and running

### 1. Configure environment

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Edit `.env` and set at least `ANTHROPIC_API_KEY`. `.env` is git-ignored — never
commit a real key.

### 2. Backend API

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health check: <http://127.0.0.1:8000/health>
- Interactive docs: <http://127.0.0.1:8000/docs>
- Ask endpoint: `POST /ask` with `{"question": "..."}`

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the admission requirements for transfer students?"}'
```

### 3. Ingestion CLI (crawler)

```bash
cd crawler
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
python -m playwright install chromium   # only needed for Cloudflare-blocked pages

python ingest.py                        # ingest the first approved source
python ingest.py --url https://www.mcneese.edu/
python ingest.py --all --limit 3        # ingest the first 3 approved sources
```

Ingestion writes chunks into the local ChromaDB store that the backend reads.

### 4. Frontend

```bash
cd frontend
cp .env.example .env      # Windows: copy .env.example .env
npm install
npm run dev               # http://localhost:5173
```

With the backend running, the header badge shows the API status.

## Tests and build

Backend unit tests use Python's `unittest` and run offline (no network or LLM):

```bash
cd backend
python -m unittest discover -s tests/unit -p "test_*.py"
```

Verify the backend still imports:

```bash
cd backend
python -c "from app.main import app"
```

Frontend build (type-check + production bundle):

```bash
cd frontend
npm run build
```

## Environment variables

Configuration lives in `.env` (copied from `.env.example`). The most important:

| Variable | Used by | Meaning |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | backend | Claude API key for answer generation |
| `CLAUDE_MODEL` | backend | Claude model name (e.g. `claude-sonnet-4-20250514`) |
| `CLAUDE_MAX_TOKENS` | backend | Max tokens per generated answer |
| `CHROMA_DB_PATH` | crawler + backend | On-disk location of the ChromaDB store |
| `CHROMA_COLLECTION` | crawler + backend | ChromaDB collection name |
| `RETRIEVAL_TOP_K` | backend | Chunks returned per `/ask` question |
| `QUERY_LOG_PATH` | backend | JSONL file for per-request query logs |
| `ASKMCNEESE_DEBUG_TRACE` | backend | `1` adds pipeline debug fields (intent, persona, expanded queries, rerank scores, mode) to each query log; default `0` |
| `SOURCE_REGISTRY_PATH` | crawler | Path to the approved source list |
| `CHUNK_SIZE_TOKENS`, `CHUNK_OVERLAP_TOKENS` | crawler | Chunking parameters |

## Branches

- `main` — stable, reviewed milestones.
- `dev` — the active working/integration branch.
- `feature/*` — focused task work, branched off `dev`.

Never push directly to `main`; it is reserved for milestones.

## Attribution

AskMcNeese is built by the McNeese ACM Student Chapter as a student-led software
project focused on trusted campus information access.
