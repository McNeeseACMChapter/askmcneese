# Backend Developer Guide

Welcome, Zyan. This guide gets you productive on the AskMcNeese backend quickly.
Read it alongside `docs/architecture/SPRINT3_ARCHITECTURE_DECISIONS.txt`, which
explains the choices already made and why — start there before changing anything
structural, so you don't re-open decisions the team already settled.

## What the backend does

The backend answers a student question by running a retrieval-augmented
generation (RAG) pipeline: find the most relevant McNeese text, then ask Claude
to write a grounded, cited answer from that text.

```text
question
  → intent check        (greeting/thanks/etc. answered directly, no LLM)
  → persona detection   (freshman / transfer / continuing / graduate / international)
  → retrieval           (ChromaDB knowledge base OR live web search)
  → generation          (Claude writes the answer from retrieved context)
  → cited answer + query log
```

## Architecture

### Routers (`backend/app/routers/`)

- `health.py` — `GET /health` liveness check.
- `ask.py` — `POST /ask`, the full pipeline. Supports a normal JSON response and
  an SSE streaming response (`stream=true`). Two retrieval modes:
  `use_web_search=false` (default) uses the ChromaDB knowledge base;
  `use_web_search=true` fetches `mcneese.edu` pages live.

### Services (`backend/app/services/`)

- `intent.py` — classifies greetings/thanks/goodbye/identity vs. a real
  question, so small talk never triggers retrieval or the LLM.
- `persona.py` — detects the applicant category from the question and history.
- `query_expansion.py` — turns one question into 2–4 focused sub-queries so
  persona-specific pages all get retrieved.
- `retrieval.py` — reads from ChromaDB. Expands the query, retrieves candidates
  per sub-query, merges/dedups, reranks against the original question, returns
  the top `RETRIEVAL_TOP_K` chunks. **Read-only**: the backend never writes to
  ChromaDB.
- `rerank.py` — reorders merged candidates by true relevance (cross-encoder if
  available, otherwise an offline heuristic; always works offline for CI).
- `web_search.py` — live search + fetch of `mcneese.edu`, with structure-aware
  HTML extraction (tables/lists → Markdown).
- `llm.py` — Claude answer generation (sync and streaming) and the system
  prompt.
- `answer_format.py` — fallback formatting used when the LLM is unavailable.
- `query_logger.py` — appends each `/ask` request to a JSONL log.

### Ingestion pipeline (`crawler/`)

The crawler is a separate, offline component owned by the backend role. It
writes the ChromaDB store that the backend reads. Key modules:

- `ingest.py` — orchestrates fetch → clean → chunk → store for a webpage.
- `ingest_pdf.py` — the same, for PDFs.
- `clean_text.py` — strips nav/scripts and preserves tables/lists as Markdown.
- `chunker.py` — splits clean text into ~300-token chunks with metadata.

### Vector store

We use ChromaDB, a lightweight local vector database, to store text embeddings.
When a user asks a question, we embed the question and compare it to these
stored vectors to retrieve relevant text chunks. Currently, ChromaDB runs
locally and is not the long-term production solution; it serves as our
prototype's data store. Location: `CHROMA_DB_PATH` / `CHROMA_COLLECTION`.

## Running things

### Tests

All backend unit tests are offline (no network, no LLM):

```bash
cd backend
python -m unittest discover -s tests/unit -p "test_*.py"
```

Confirm the app still imports:

```bash
cd backend
python -c "from app.main import app"
```

### Ingestion CLI

```bash
cd crawler
pip install -r requirements.txt
python ingest.py --url https://www.mcneese.edu/admissions/
```

### Querying the API

Start the API (`uvicorn app.main:app --reload` from `backend/`), then:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What GPA do I need for a transfer scholarship?"}'
```

Add `"use_web_search": true` to search `mcneese.edu` live instead of the
knowledge base, or `"stream": true` for a streamed (SSE) response.

## Your Sprint 4 tasks

1. **Debug-trace logging.** The flag `ASKMCNEESE_DEBUG_TRACE` is now wired up
   (`query_logger.py` + `ask.py`). When set to `1`, each query log entry also
   records `intent`, `persona`, `expanded_queries`, `rerank_scores`, and `mode`;
   when off, those keys are omitted. Understand this path — you'll extend it as
   the pipeline grows.
2. **HTML-extraction contract tests.** There are two copies of the
   table/list → Markdown converters (`web_search.py` and `crawler/clean_text.py`).
   `backend/tests/unit/test_html_extraction.py` feeds both the same snippets and
   reports differences. Grow this harness with more real-world snippets. **Do not
   change the extraction functions yet** — the harness is observational so a
   future sprint can decide whether to unify them.
3. **Documentation.** Keep this guide and the README accurate as you work.

## Conventions

- Tests must run offline. Never make network or Anthropic calls in tests.
- The backend never writes to ChromaDB.
- Prefer small, targeted changes. Record notable changes in
  `docs/devlog/DEVELOPMENT_LOG.md`.
- Branch off `dev`; `main` is stable only.
