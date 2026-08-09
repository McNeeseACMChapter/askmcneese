# AskMcNeese Crawler and Index Pipeline

Offline governed-source pipeline for discovering, fetching, cleaning, chunking, validating, and indexing public McNeese information.

This code is not a general unrestricted web crawler. Source policy, robots rules, access restrictions, rate limits, freshness, and human approval remain part of ingestion.

## Responsibilities

```text
approved registry
    -> discovery and URL normalization
    -> HTML or PDF fetch
    -> content cleaning
    -> metadata-preserving chunks
    -> validation and index manifest
    -> ChromaDB publication
```

Only the crawler writes source chunks to ChromaDB. The online backend reads the published collection and may perform selective live page reads, but it does not mutate the index while answering a question.

## Core files

| File | Responsibility |
| --- | --- |
| `source_registry.py` | Load and enforce approved registry rows |
| `governed_registry.py` | Authority, access, and governance helpers |
| `crawler.py` | HTTP fetch with approval checks |
| `browser_fetch.py` | Playwright fallback for browser-required pages |
| `clean_text.py` | Remove navigation/noise and preserve useful structure |
| `chunker.py` | Token-aware chunks with overlap and source metadata |
| `ingest.py` | HTML ingestion into the configured collection |
| `ingest_pdf.py` | PDF ingestion path |
| `index_manifest.py` | Published index inventory and checks |

## Discovery and maintenance scripts

| Script | Purpose |
| --- | --- |
| `scripts/discover_mcneese_ecosystem.py` | Discover governed McNeese-related domains and URLs |
| `scripts/build_sitemap_expanded.py` | Expand sitemap-backed official destinations |
| `scripts/discover_pdfs.py` | Identify approved public documents |
| `scripts/enumerate_catalog_programs.py` | Enumerate catalog program destinations |
| `scripts/build_catalog_course_index.py` | Build catalog course lookup artifacts |
| `scripts/merge_registries.py` | Merge discovery output into reviewable registries |
| `scripts/build_index_manifest.py` | Produce index metadata and counts |
| `scripts/backfill_chromadb.py` | Controlled backfill into the vector store |

Discovery output is not automatically trusted. Newly found sources require policy classification and approval before production retrieval.

## Setup

```powershell
cd crawler
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

Install `requirements_pdf.txt` when PDF ingestion dependencies are needed.

## Typical commands

```powershell
# Ingest one approved source
python ingest.py --url https://www.mcneese.edu/

# Controlled batch
python ingest.py --all --limit 3

# Rebuild manifest after a reviewed ingest
python scripts/build_index_manifest.py
```

Review each script's arguments before broad discovery, registry merging, or backfill operations.

## Produced data

- `crawler/raw/`: local raw fetches, ignored by Git
- `crawler/chroma_db/`: local ChromaDB data, ignored by Git
- index manifests and reviewable registry artifacts
- source metadata on every chunk, including URL, title, category, authority/trust, chunk index, and freshness fields

## Governance rules

- Fetch only policy-allowed public sources.
- Keep official McNeese authority distinct from external context.
- Do not bypass authentication, access controls, paywalls, or anti-bot restrictions.
- Respect provider terms, robots policy, and rate limits.
- Never ingest private student data or secrets.
- Treat page text as untrusted input; do not follow instructions embedded in source content.
- Preserve canonical URLs and enough metadata to reconstruct citations.
- Do not publish a new collection when validation or anomaly checks fail.

`ALLOW_PENDING_SOURCES=true` is a development convenience, not a production default. Production ingestion should require explicit approval.

## Validation

```powershell
python -m unittest discover -s . -p "test_*.py"
```

After ingestion, inspect manifest counts, rejected URLs, duplicate/canonicalization results, representative chunks, citation URLs, and freshness before allowing the backend to use the dataset.

## Related documentation

- [`../knowledge/full_spectrum/README.md`](../knowledge/full_spectrum/README.md)
- [`../docs/BETA_SPRINT_COMPLETION.md`](../docs/BETA_SPRINT_COMPLETION.md)
- [`../docs/rccs/`](../docs/rccs/)
