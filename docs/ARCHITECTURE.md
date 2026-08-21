# AskMcNeese Architecture

This document is the source of truth for **where code belongs** and **how modules may
depend on each other**. Read this before adding a new module. Some sections below
describe a target layout (such as a shared `common/` package) that is not fully
landed yet; prefer the current folders in the repository when they disagree.

Core principle: **depth over length.** Prefer many small, single-purpose modules
(100–300 LoC) organized in folders over a few large files. Split anything > 400 LoC.

---

## 1. Top-level layout

```
askmcneese/
├── common/     # shared, dependency-light helpers used by BOTH backend and crawler
├── backend/    # FastAPI app + services (serves /ask, /health) — READ-ONLY on ChromaDB
├── crawler/    # data ingestion pipeline (fetch → clean → chunk → write ChromaDB)
├── frontend/   # React + Vite + Tailwind chat UI
├── knowledge/  # source-registry CSVs (pipeline inputs, see §6)
└── docs/       # documentation (this file, audit, PM, design)
```

The **backend reads** ChromaDB; the **crawler writes** ChromaDB. They never call each
other at runtime. Anything both need lives in `common/`.

---

## 2. What belongs where

### `common/` — shared utilities (no business logic, no framework)
Pure functions and constants used by more than one top-level package.
- `html_markdown.py` — the **single** HTML `<table>`/`<ul>`/`<ol>` → Markdown implementation.
- `http.py` — `USER_AGENT`, request headers, Cloudflare-challenge detection.
- `text.py` — stopwords, `normalize()`, tokenization helpers.
- `registry.py` — canonical source-registry CSV loader + row schema.

**Rule:** If two packages implement the same helper, it belongs here — do not copy-paste.
`common/` may import only the standard library + light third-party libs (bs4). It must
**never** import `backend`, `crawler`, or `frontend`.

### `backend/app/` — API + business logic

| Folder | Contains | May import |
|--------|----------|-----------|
| `main.py` | app factory, CORS, router registration | routers, `__init__` |
| `routers/` | HTTP endpoints. **Thin** — orchestration only, no formatting logic | `services`, models |
| `services/` | Business logic: LLM, retrieval, RCCS, web search, activity events, structured answers, logging | other `services`, `common`, stdlib |

**Rules:**
- Routes orchestrate; they do not format answers or build prompts. Keep routes small.
  Answer formatting lives in `services/answer_format.py` (extracted pre–Sprint 3).
- `services/` must not import `routers/`.
- `web_search/` is a folder, not a 465-line file: `extract.py` (HTML→text),
  `search.py` (DDG + fetch), `__init__.py` (public `search_and_fetch`, `pages_to_context`).
- The backend is **read-only** on ChromaDB. It never writes chunks.

### `crawler/` — ingestion pipeline (flat-module CLI, package migration deferred)
`fetch → clean → chunk → store`. Each step is an independent module:
`fetch.py`, `browser_fetch.py`, `clean_text.py`, `chunker.py`, `tokenizer_util.py`,
`ingest.py`, `ingest_pdf.py`, `source_registry.py`, plus one-shot CLIs in `scripts/`.

**Current state (pre–Sprint 3):**
- The crawler preserves its existing **flat-module** execution model for CLI compatibility;
  there is no `crawler/__init__.py`, and modules use flat imports (`from config import ...`).
- Shared Chroma configuration was extracted to `crawler/config.py` so `ingest.py` and
  `ingest_pdf.py` no longer depend on each other for `CHROMA_DIR` and `COLLECTION`.
- Scripts under `scripts/` still use `sys.path.insert` to reach crawler modules.
- `crawler/` must not import `backend/app`.

**Target (deferred to a separate controlled migration):**
- Convert to a formal Python package with **relative imports** (`from .chunker import chunk_text`)
  and removal of `sys.path.insert` manipulation.

### `frontend/src/` — React UI
Already well-structured. Keep it that way.
- `hooks/` — data/state (`useAsk`, `useConversations`, `useHealth`).
- `components/{chat,layout,feedback,ui}/` — presentational components.
- `lib/motion.ts` — shared framer-motion variants.
- `types.ts` — API types mirroring backend responses.

**Rule:** Every component must be reachable from `App.tsx`. Delete orphans (a component
imported by nothing is dead code — the audit found `Button`, `Badge`, `Skeleton`,
`CitationCard` orphaned).

### `knowledge/` — data (see §6). No code.

---

## 3. Import rules

**Layering (top may import lower; never the reverse):**
```
routers  ->  services  ->  common  ->  (stdlib / third-party)
crawler modules       ->  common  ->  (stdlib / third-party)
```

**Correct**
```python
from app.services.retrieval import search_chunks
from app.services.answer_format import format_chunks_as_answer
from common.html_markdown import table_to_markdown      # shared, one copy
from common.http import USER_AGENT, is_cloudflare_block
```

**Incorrect**
```python
from app.routers.ask import format_chunks_as_answer     # logic lives in services/
from app.services.web_search import _table_to_markdown   # duplicate of common/
import sys; sys.path.insert(0, CRAWLER_DIR)              # crawler is a package now
```

**Circular / latent-cycle policy:** No hard cycles. If a "utility" needs a heavier
service (e.g. rerank optionally calling the LLM), keep that import **lazy** (inside the
function) and document why — it signals the utility is doing more than a utility should.

---

## 4. Adding new features

**New service:** create `backend/app/services/<name>.py` (or a folder if > ~300 LoC),
import only `services`/`common`, expose a clear public function, add a test in
`backend/tests/unit/`.

**New endpoint:** add a route in `routers/`, delegate all logic to a service, add an
integration test in `backend/tests/integration/`.

**New shared helper:** add to the right `common/` module; never copy it into two packages.

**New crawler step:** add a module under `crawler/`, wire it into `ingest.py`, and add a
test under `crawler/tests/`.

**New UI component:** add under `components/`, import it from a parent, reuse `lib/motion.ts`
and `types.ts`.

---

## 5. Naming & style

- Files/modules/functions: `snake_case` (Python), `camelCase`/`PascalCase` (TS components).
- Classes/React components/pydantic models: `PascalCase`.
- Imports grouped: stdlib → third-party → local; explicit (`from x import y`, never `*`).
- Keep modules focused; split at ~400 LoC.
- No comments that narrate the code; comment only non-obvious intent/constraints.

---

## 6. Knowledge data lineage (not duplicates)

The `knowledge/` CSVs are a **pipeline**, each a real input to the next stage:

```
source_registry_seed.csv        (33 curated rows, SRC-001..033; hand-approved)
        │
        ├── build_sitemap_expanded.py     -> sitemap_expanded.csv
        ├── enumerate_catalog_programs.py -> catalog_programs.csv (+ appends to sitemap)
        └── discover_pdfs.py              -> discovered_pdfs.csv
                          │
                          merge_registries.py
                          │
                          ▼
                 source_registry_merged.csv   (production registry; PM-gated rows)
                          │
                          ▼
                 backfill_chromadb.py  -> ChromaDB collection "askmcneese_sources"
```

- The **backend** keyword-matches against `source_registry_seed.csv` for live routing.
- The **crawler** ingests approved rows from `source_registry_merged.csv`.
- Do not delete any of these CSVs; they are regenerable inputs, not stale copies.

---

## 7. Testing strategy

```
backend/tests/
├── unit/          # pure logic: intent, persona, rerank, query_expansion, chunker
├── integration/   # retrieval + ask pipeline (may need ChromaDB)
└── eval/          # run_eval.py + golden_questions.json (fact-recall gate)
crawler/tests/     # ingest/pdf smoke tests (moved out of the source dir)
```

- Unit tests import the module under test directly; no network, no API key.
- `run_eval.py --mode context` needs network but not the LLM key — good for CI gating.
- `--mode answer` needs `ANTHROPIC_API_KEY` — run locally / nightly, not on every PR.

CI (`.github/workflows/ci.yml`) should, over time, add: `ruff` lint, backend import check
(exists), frontend build (exists), and `run_eval.py --mode context` as a soft gate.
