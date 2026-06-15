# Data Schema Draft — AskMcNeese (PM-04)

**Sprint 1 draft.** Field names and purpose for the three core data models. This is the
contract the Backend developer codes against — **review field names with Backend before
freezing** (per PM-04 acceptance criteria).

There are three stores, each with a different job:

| Model | Where it lives | Job |
|-------|----------------|-----|
| `source_registry` | structured file (CSV now → SQLite later) | The approved list of what we may crawl |
| `chunks` | **ChromaDB** (vector store) | The searchable knowledge the assistant answers from |
| `query_logs` | append-only file (JSONL → SQLite later) | A record of what was asked and what was retrieved |

---

## 1. `source_registry`

The human-curated, PM-approved list of sources. The crawler reads this and **refuses any URL
not listed or not allowed for AI retrieval**. Currently seeded at
`knowledge/source_registry_seed.csv`.

| Field | Type | Purpose |
|-------|------|---------|
| `source_id` | string (PK) | Stable ID, e.g. `SRC-011`; also prefixes chunk IDs |
| `title` | string | Human name of the source (e.g. "Academic Catalog") |
| `url` | string | The approved URL |
| `category` | string | Information category (admissions, financial aid, catalog, …) |
| `trust_tier` | enum (`High`/`Medium`/`Low`) | How authoritative the source is; used to rank retrieval |
| `department_owner` | string | Who owns the page (for freshness/conflict follow-up) |
| `approval_status` | enum (`Approved`/`Pending`/`Needs_review`) | **Only `Approved` may be crawled in production** |
| `allowed_for_ai` | bool-ish (`Yes`/`Yes, with limits`/`No`) | Content team's permission flag |
| `crawl_scope` | string | What may be fetched (page only, page + children, …) |
| `content_sensitivity` | enum (`Low`/`Medium`/`High`) | Extra care for Title IX, emergency, compliance pages |
| `last_checked_date` | date | When the source was last verified (freshness) |
| `notes` | string | Caveats, redirects, special handling |

**Primary key:** `source_id`. **Relationships:** one source → many `chunks` (via `source_url`/`source_id`).

---

## 2. `chunks`  (the retrieval core)

Each crawled page is cleaned and split into ~300-token chunks. Every chunk is stored in
ChromaDB with its embedding **and** the metadata needed to cite and freshness-check it.
This is exactly what `crawler/chunker.py` already produces.

| Field | Type | Purpose |
|-------|------|---------|
| `chunk_id` | string (PK) | e.g. `SRC-011-0003` — unique, source-prefixed |
| `chunk_index` | int | Order of the chunk within its page |
| `text` | string | The chunk content (what the assistant reads) |
| `embedding` | vector(float[]) | Semantic vector — **managed by ChromaDB**, not stored by hand |
| `source_url` | string (FK) | Links back to `source_registry.url` for citations |
| `title` | string | Source title (denormalized for fast display) |
| `category` | string | Denormalized from the registry, for filtering |
| `trust_tier` | string | Denormalized, for ranking results |
| `last_checked_date` | date | Denormalized, for staleness checks |

**Storage note:** in ChromaDB, `text` is the document, `embedding` is auto-generated, and the
rest live in the chunk's `metadata`. **Primary key:** `chunk_id`.

---

## 3. `query_logs`

An append-only record of usage, so we can later measure quality, find gaps in the registry,
and debug bad answers. **No personal data in Sprint 1** (no names, no auth).

| Field | Type | Purpose |
|-------|------|---------|
| `query_id` | string (PK) | Unique ID per question |
| `timestamp` | datetime (UTC) | When it was asked |
| `question_text` | string | The raw question |
| `retrieved_chunk_ids` | string[] | Which chunks were pulled (FK → `chunks.chunk_id`) |
| `top_source_urls` | string[] | The sources behind the answer |
| `num_results` | int | How many chunks were retrieved |
| `latency_ms` | int | Retrieval time (basic performance signal) |

> Fields like `answer_text` and user `feedback` are deferred — they belong to the
> answer-generation week, which is **out of Sprint 1 scope**.

---

## Relationships (at a glance)

```
source_registry (1) ───< chunks (many)        via source_id / source_url
chunks (many) ───< query_logs.retrieved_chunk_ids   via chunk_id
```

## Sprint 1 storage decisions

- **`chunks` → ChromaDB** (local, on disk). Already working in `crawler/`.
- **`source_registry` → CSV now** (`knowledge/source_registry_seed.csv`), promote to SQLite if it grows.
- **`query_logs` → JSONL** to start (one JSON object per line); promote to SQLite later.
- No heavyweight relational DB in Week 1. No ORM lock-in.

*Status: draft for Backend review (PM-04). Confirm field names with Backend before freezing.*
