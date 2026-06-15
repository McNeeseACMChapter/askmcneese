# Crawler — AskMcNeese retrieval pipeline (Sprint 1)

Sprint 1 backend deliverable: a **crawler → clean → chunk → local ChromaDB ingest**
proof on **approved** public McNeese pages. No LLM, no private data, no full-site crawl.

## Pipeline (tickets BE-01 → BE-05)

| File | Ticket | Job |
|------|--------|-----|
| `source_registry.py` | — | Load approved sources from `knowledge/source_registry_seed.csv`; reject anything not allowed for AI retrieval |
| `crawler.py` | BE-01 | `fetch_url()` — fetch one approved URL, save raw HTML to `crawler/raw/` (gitignored) |
| `clean_text.py` | BE-02 | `clean_html()` — strip nav/scripts/styles, keep headings, normalize whitespace |
| `chunker.py` | BE-03 | `chunk_text()` — ~300-token chunks, 50-token overlap, full metadata |
| `ingest.py` | BE-04/05 | `ingest_page()` — fetch+clean+chunk+insert into local ChromaDB; writes samples |

## Setup

```bash
cd crawler
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the proof

```bash
# Ingest the first allowed source and write samples to docs/samples/
python ingest.py

# Ingest a specific approved URL
python ingest.py --url https://www.mcneese.edu/

# Ingest the first 3 allowed sources
python ingest.py --all --limit 3
```

Expected output (example):

```
INGESTED  https://www.mcneese.edu/
  chunks=12  collection=askmcneese_sources  stored_total=12
```

## What gets produced

- `crawler/raw/*.html` — raw HTML (gitignored)
- `crawler/chroma_db/` — local ChromaDB store (gitignored)
- `docs/samples/clean_text_sample.md` — readable clean-text sample (committed)
- `docs/samples/chunks_sample.json` — first 3 chunks with metadata (committed)

## Chunk metadata

Every chunk carries: `chunk_id`, `chunk_index`, `source_url`, `title`, `category`,
`trust_tier`, `last_checked_date` — enough for future citations and freshness checks.

## Rules enforced

- Only URLs present in the source registry **and** marked *Allowed for AI Retrieval = Yes* are fetched.
- Sources whose **Approval Status is still "Pending"** can be crawled for the Week 1 proof
  (`allow_pending=True`), but must be **PM-approved** before production use. Set
  `allow_pending=False` in `crawler.fetch_url` to enforce strict approval.
- **`www.mcneese.edu` 403:** see `docs/crawler_403_strategy.md`. Use subdomain sources
  (e.g. `catalog.mcneese.edu`) until resolved.

## Notes

- Tokenizer uses `tiktoken` when installed; otherwise falls back to a whitespace tokenizer.
- ChromaDB uses its default local embedding model (downloaded once on first run).
