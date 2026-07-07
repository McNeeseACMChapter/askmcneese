# AskMcNeese Data Layer Expansion Proposal

**Status:** Analysis + proposal only (no registry merge, no PDF ingest implementation, no cron)  
**Date:** 2026-07-05  
**Goal:** Expand from 33 hub URLs / 12 Chroma chunks → ~180 registry entries with leaf/detail coverage + PDF ingestion path + refresh design

---

## Executive Summary

| Metric | Current | Target (this sprint) |
|---|---:|---:|
| Registry entries | 33 | ~180 (33 retained + ~147 net-new leaf/detail) |
| ChromaDB chunks | 12 (2 URLs) | ~800–1,200 (estimate) |
| Catalog program pages indexed | 0 | ~80–120 `preview_program.php` URLs |
| PDF sources | 0 | ~15–30 (policy/forms/disclosures) |
| Automated refresh | None | Designed (manual trigger first, cron Phase 2) |

**Deliverable from Task 1:** [`knowledge/sitemap_expanded.csv`](../../knowledge/sitemap_expanded.csv) — **200 rows** (160 high / 40 medium priority), generated from live sitemaps + catalog browse.

**Critical finding:** `catalog.mcneese.edu/sitemap.xml` **does not exist** (404). Catalog URLs must come from a **dedicated catalog inventory crawl**, not the main WordPress sitemap. Initial catalog BFS from root yielded only **24 catalog URLs** and **1** `preview_program.php` page — insufficient for degree-requirement QA. Follow-up implementation must crawl `content.php?catoid=102&navoid=*` inventory pages to enumerate all `poid` values.

---

## TASK 1 — Scrape Extended Registry from McNeese Sitemaps

### 1.1 Data sources discovered

| Source | URL | Result |
|---|---|---|
| McNeese sitemap index | `https://www.mcneese.edu/sitemap_index.xml` | **200 OK** — WordPress sitemap index |
| Child sitemaps | `post-sitemap1..9.xml`, `page-sitemap1..6.xml` | **2,673 unique page URLs** |
| McNeese robots.txt | `https://www.mcneese.edu/robots.txt` | Points to sitemap index |
| Catalog sitemap | `https://catalog.mcneese.edu/sitemap.xml` | **404 Not Found** |
| Catalog robots.txt | `https://catalog.mcneese.edu/robots.txt` | Exists; no sitemap URL listed |
| Catalog browse | `https://catalog.mcneese.edu/` | **251 KB HTML**; Modern Campus Catalog; current catoid appears to be **102** (2026–2027) |

**PDFs:** **Zero** `.pdf` URLs appear in the WordPress sitemaps. PDFs are linked from policy/disclosure pages and must be discovered via **link extraction** during hub-page crawl (see Task 1.4).

### 1.2 Heuristic categorization rules (implemented in generator)

Generator script: [`crawler/scripts/build_sitemap_expanded.py`](../../crawler/scripts/build_sitemap_expanded.py)

| `category_heuristic` | Detection rule | Default priority |
|---|---|---|
| `pdf` | URL ends in `.pdf` | high |
| `catalog_program` | `preview_program.php?catoid=&poid=` | high |
| `catalog_content` | `content.php?catoid=&navoid=` | high |
| `scholarship_leaf` | `/scholarships/` or `international-scholarships` | high |
| `admissions_leaf` | `/admissions/apply`, `estimated-costs`, `deadlines` | high |
| `financial_aid_leaf` | `/financial-aid/<specific-slug>` | high |
| `policy_leaf` | `/policy/<slug>` | high |
| `department_leaf` | `/college-of-`, `/department-of-`, `/school-of-` | medium |
| `academic_leaf` | `/academics/<college>/<program>` (3+ path segments) | medium |
| `hub_nav` | Exact section roots (`/admissions/`, `/student-central/`, etc.) | medium |
| `leaf_detail` | Path depth ≥ 3, not matched above | high/medium |
| `news_post` | Date-based post URLs (`/YYYY/MM/`) | low (excluded from top-200) |
| `external` | Host not in `{www.mcneese.edu, catalog.mcneese.edu}` | low |

**Exclusions:** `/wp-json/`, `/feed/`, `/author/`, `/tag/`, `/category/`, Breakdance parts, image uploads, comment reply links.

### 1.3 Output: `sitemap_expanded.csv`

**Path:** `askmcneese/knowledge/sitemap_expanded.csv`

**Columns:**

| Column | Description |
|---|---|
| `url` | Normalized URL (https, lowercase host, trimmed trailing slash on path) |
| `category_heuristic` | Rule-based category (see §1.2) |
| `is_pdf` | `true` / `false` |
| `domain` | Extracted host |
| `extracted_from` | `sitemap_xml` or `catalog_browse` |
| `priority` | `high` / `medium` / `low` |
| `proposed_parent_source_id` | Suggested hub parent from existing seed (e.g. `SRC-006`) |

**Counts (actual run):**

| Metric | Value |
|---|---:|
| Total rows | 200 |
| High priority | 160 |
| Medium priority | 40 |
| Catalog URLs | 24 |
| Scholarship-related URLs | 8 |
| `preview_program.php` URLs | **1** (gap — see §1.5) |
| PDF URLs | **0** in top-200 (not in WordPress sitemap) |
| Overlap with existing seed registry | 7 |
| Net-new URLs vs seed | 193 |

**Sample high-priority rows:**

```csv
url,category_heuristic,is_pdf,domain,extracted_from,priority,proposed_parent_source_id
https://www.mcneese.edu/admissions/apply,admissions_leaf,false,www.mcneese.edu,sitemap_xml,high,SRC-002
https://www.mcneese.edu/scholarships/freshman_academic_scholarships/,scholarship_leaf,false,www.mcneese.edu,sitemap_xml,high,SRC-031
https://catalog.mcneese.edu/preview_program.php?catoid=102&poid=61507,catalog_program,false,catalog.mcneese.edu,catalog_browse,high,SRC-011
https://catalog.mcneese.edu/content.php?catoid=102&navoid=8458,catalog_content,false,catalog.mcneese.edu,catalog_browse,high,SRC-011
```

### 1.4 PDF discovery strategy (not yet in CSV)

WordPress sitemaps do not list PDFs. Proposed Phase 1b add-on:

1. Crawl hub pages: `SRC-020` (policy), `SRC-022` (disclosures), `SRC-015` (registrar forms), `SRC-005` (financial-aid/forms)
2. Extract all `href="*.pdf"` links on mcneese.edu domain
3. Append to `sitemap_expanded.csv` with `category_heuristic=pdf`, `priority=high`
4. Expected yield: **15–30 PDFs** (forms, policy PDFs, consumer disclosure reports)

### 1.5 Catalog gap — must fix before merge

The initial BFS found only **1 program page**. For BS CS and similar queries, implementation sprint must:

1. Fetch catalog home → detect current `catoid` (102 = 2026–2027)
2. Crawl **Inventory of Degree and Certificate Programs** nav page(s)
3. Enumerate all `preview_program.php?catoid=102&poid=*` links
4. Target: **~80–120 program pages** added to expanded registry
5. Optionally crawl **Course Descriptions** `content.php` pages for course-number queries

**Estimated final expanded CSV after catalog pass:** 200 (current) + ~100 program pages + ~20 PDFs ≈ **~320 rows**, then PM trims to ~180 ingest-approved.

---

## TASK 2 — Cross-Reference vs Existing Registry

### 2.1 Overlap analysis

**Existing seed:** `knowledge/source_registry_seed.csv` — 33 rows, all `Allowed for AI Retrieval = Yes`

| Status | Count | Notes |
|---|---:|---|
| URLs in both seed and expanded top-200 | **7** | Includes admissions, catalog root, 3 scholarship pages |
| Net-new in expanded top-200 | **193** | Not in seed today |
| Seed URLs NOT in expanded top-200 | **26** | External domains (athletics, presence.io), hubs intentionally deprioritized in cap |

**Seed URLs missing from expanded (expected — external/hub):**

- `mcneesesports.com`, `mcneese.presence.io`, `schedule.mcneese.edu` → `external`, low priority
- Hubs like `SRC-001` (homepage), `SRC-014` (Student Central root) → medium priority, not in top-200 cap

### 2.2 Parent-child relationships (proposed)

New column `proposed_parent_source_id` maps leaf → nearest existing hub:

| Parent ID | Hub name | Example children discovered |
|---|---|---|
| SRC-002 | Admissions | `/admissions/apply`, `/admissions/estimated-costs` |
| SRC-005 | Financial Aid | `/financial-aid/fafsa-resources`, `/financial-aid/forms` |
| SRC-006 | Scholarships | `/financial-aid/graduate_scholarships`, engineering endowed lists |
| SRC-031 | Freshman Scholarships | `/scholarships/freshman_academic_scholarships/` (seed) + `/financial-aid/freshman_academic_scholarships` (mirror) |
| SRC-032 | Continuing Scholarships | mirror paths under `/financial-aid/` and `/scholarships/` |
| SRC-033 | International Scholarships | `/student-central/international-scholarships/` + `/financial-aid/international-scholarships` |
| SRC-011 | Academic Catalog | all `catalog.mcneese.edu/content.php` and `preview_program.php` |
| SRC-007 | Undergraduate Programs | college-specific program marketing pages |
| SRC-020 | University Policies | `/policy/<slug>` leaf pages |

**Duplicate content warning:** McNeese mirrors scholarship content under both `/scholarships/` and `/financial-aid/` paths. Registry merge should **pick one canonical URL per topic** and mark the other as `alias_of_source_id` (future column) to avoid double-ingesting identical tables.

### 2.3 Special handling flags

| Type | Count in expanded | Handling |
|---|---:|---|
| HTML leaf pages | 200 | Standard `ingest_page()` |
| PDF | 0 (pending link crawl) | `ingest_pdf()` (Task 4) |
| External domains | 0 in top-200 | Keep in seed for routing; do not ingest into Chroma |
| Dynamic catalog | 24 | HTML fetch works; treat as `content_type=dynamic_catalog` |
| `schedule.mcneese.edu` | In seed only | Do not ingest (dynamic JS class search) |

---

## TASK 3 — Proposed Extended Registry Structure

**Do not modify `source_registry_seed.csv` yet.** Merge happens in implementation sprint after PM review.

### 3.1 Merged CSV schema

**File (proposed):** `knowledge/source_registry_extended.csv`

**Retain all 19 existing columns** from seed, plus:

| New column | Type | Description |
|---|---|---|
| `parent_source_id` | string | Hub source ID (e.g. `SRC-006`). Empty for top-level hubs. |
| `is_leaf` | boolean | `true` if detail/deep page; `false` if hub/index |
| `content_type` | enum | `page`, `pdf`, `dynamic_catalog`, `external` |
| `catalog_year` | string | e.g. `2026-2027` when `catoid=102`; empty otherwise |
| `catalog_catoid` | int | Modern Campus catalog ID (102 for current) |
| `priority_for_ingest` | enum | `high`, `medium`, `low` — controls ingest batch order |
| `last_ingested_timestamp` | ISO-8601 UTC | Empty until first ingest; updated by ingest job |
| `content_hash` | string | SHA-256 of cleaned text; skip re-embed if unchanged |
| `alias_of_source_id` | string | If duplicate mirror URL, point to canonical source |
| `sitemap_category` | string | From `sitemap_expanded.csv` heuristic |

### 3.2 Sample merged rows (illustrative)

```csv
Source ID,Source Name,Source URL,...,parent_source_id,is_leaf,content_type,catalog_year,priority_for_ingest,last_ingested_timestamp
SRC-001,McNeese Main Website Root,https://www.mcneese.edu/,..., ,false,page,,low,
SRC-006,Scholarships Hub,https://www.mcneese.edu/student-central/scholarships/,..., ,false,page,,medium,
SRC-031,Freshman Academic Scholarships,https://www.mcneese.edu/scholarships/freshman_academic_scholarships/,...,SRC-006,true,page,,high,
SRC-034,Financial Aid Mirror - Freshman Scholarships,https://www.mcneese.edu/financial-aid/freshman_academic_scholarships,...,SRC-031,true,page,,low,SRC-031
SRC-101,Catalog - BS Computer Science,https://catalog.mcneese.edu/preview_program.php?catoid=102&poid=XXXXX,...,SRC-011,true,dynamic_catalog,2026-2027,high,
SRC-201,Policy PDF - Academic Standing,https://www.mcneese.edu/media/.../academic-standing.pdf,...,SRC-020,true,pdf,,high,
```

### 3.3 Merge procedure (implementation sprint)

1. Load seed CSV → assign existing 33 IDs unchanged
2. Assign new IDs `SRC-034` through `SRC-214` (~180 new)
3. Join `sitemap_expanded.csv` net-new URLs
4. Run catalog inventory pass → append program rows
5. Run PDF link extraction → append PDF rows
6. PM review: approve/deny each row (`Approval Status`, `Allowed for AI Retrieval`)
7. Dedupe mirrors via `alias_of_source_id`

**Estimated final row count:** 33 seed + ~147 net-new HTML leaves + ~80 catalog programs (after dedupe with content pages: ~180–220 total)

---

## TASK 4 — PDF Ingestion Skeleton

### 4.1 Current ingest pipeline (reference)

```
ingest.py: ingest_page(url)
  → crawler.fetch_url(url)     # registry gate; HTML only today
  → clean_html(html)
  → chunk_text(text)
  → chromadb.upsert()
```

**Gap:** `fetch_url()` rejects unknown URLs and only handles HTML. PDF URLs are not in registry and have no parser.

### 4.2 Proposed module: `crawler/ingest_pdf.py` (skeleton only)

```python
"""PDF ingestion for AskMcNeese crawler pipeline (SKELETON — not implemented)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Proposed dependencies (add to crawler/requirements.txt when implementing):
#   pymupdf>=1.24.0        # text + layout extraction (fitz)
#   pdfplumber>=0.11.0     # table extraction fallback
# OR: unstructured[pdf]    # heavier but unified

from chunker import chunk_text  # reuse structure-aware chunker


@dataclass
class PdfPage:
    page_num: int
    text: str
    tables_markdown: list[str]


@dataclass
class PdfIngestResult:
    url: str
    ok: bool
    pages: list[PdfPage]
    error: str | None = None


def download_pdf(url: str, dest_dir: Path) -> Path:
    """Download PDF to gitignored crawler/raw/pdf/ ; return local path."""
    raise NotImplementedError


def extract_pdf_pages(pdf_path: Path) -> list[PdfPage]:
    """Extract text per page; convert detected tables to Markdown."""
    # Pseudocode:
    # for page in pymupdf.open(pdf_path):
    #     text = page.get_text("text")
    #     tables = pdfplumber.open(pdf_path).pages[i].extract_tables()
    #     tables_md = [_table_to_markdown(t) for t in tables]
    raise NotImplementedError


def pdf_pages_to_chunks(
    pages: list[PdfPage],
    *,
    source_url: str,
    title: str,
    category: str,
    trust_tier: str,
    last_checked_date: str,
    source_id: str,
) -> list:
    """Build chunks: one chunk per table (atomic), prose chunked at 300 tokens."""
    chunks = []
    for pg in pages:
        body = pg.text
        if pg.tables_markdown:
            body += "\n\n" + "\n\n".join(pg.tables_markdown)
        chunks.extend(
            chunk_text(
                body,
                source_url=source_url,
                title=f"{title} (p.{pg.page_num})",
                category=category,
                trust_tier=trust_tier,
                last_checked_date=last_checked_date,
                source_id=f"{source_id}-p{pg.page_num:03d}",
            )
        )
    return chunks


def ingest_pdf(url: str, source_meta: dict) -> dict:
    """Full PDF ingest: download → extract → chunk → return chunk dicts for upsert."""
    # 1. download_pdf
    # 2. extract_pdf_pages
    # 3. pdf_pages_to_chunks
    # 4. return {"ok": True, "chunks": [...], "pages": len(pages)}
    raise NotImplementedError
```

### 4.3 ChromaDB metadata for PDF chunks

Extend upsert metadata (both HTML and PDF):

```python
{
    "source_url": url,
    "title": title,
    "category": category,
    "trust_tier": trust_tier,
    "last_checked_date": last_checked_date,
    "chunk_index": i,
    "chunk_type": "table" | "prose" | "list",
    # PDF-specific:
    "content_type": "pdf",
    "page_num": 3,
    "is_table": True,          # when chunk originated from table extraction
    "source_id": "SRC-201",
}
```

### 4.4 Wiring into `ingest.py` (proposed)

```python
def ingest_source(source: Source, write_samples: bool = False) -> dict:
    """Route to HTML or PDF ingest based on content_type / URL."""
    content_type = getattr(source, "content_type", None) or _infer_content_type(source.url)

    if content_type == "pdf" or source.url.lower().endswith(".pdf"):
        from ingest_pdf import ingest_pdf
        result = ingest_pdf(source.url, source_meta=_source_to_meta(source))
        chunks = result["chunks"]
    else:
        fetched = fetch_url(source.url)
        ...
        chunks = chunk_text(clean_html(fetched.html), ...)

    collection.upsert(ids=..., documents=..., metadatas=...)
    _update_last_ingested(source.source_id)
    return {"ok": True, "chunks": len(chunks)}
```

### 4.5 Registry gate changes required

Today `crawler.fetch_url()` **rejects any URL not in registry**. Implementation must:

1. Add PDF URLs to extended registry with `content_type=pdf`
2. Relax `fetch_url` or add `fetch_pdf_url` that skips HTML/Cloudflare logic
3. Optionally allow `ingest_pdf` to bypass raw HTML save path

---

## TASK 5 — Refresh / Re-Ingest Strategy (Design Only)

### 5.1 Current state

- Ingest is **manual CLI**: `python ingest.py --url URL` or `--all --limit N`
- Default `--all` uses `crawl_allowed_sources()[:limit]` — ingests **first N** registry rows only
- No `last_ingested_timestamp` column exists
- ChromaDB has **12 chunks from 2 URLs** — stale partial snapshot
- Live API path (`use_web_search=True`) bypasses ChromaDB entirely

### 5.2 Proposed CSV fields for freshness

| Field | Purpose |
|---|---|
| `last_ingested_timestamp` | When this source was last successfully chunked into ChromaDB |
| `content_hash` | SHA-256 of normalized clean text; skip embed if unchanged |
| `last_checked_date` | PM manual review date (existing) |
| `Update Frequency` | PM intent (existing) — maps to schedule tier |

### 5.3 Ingest schedule tiers

| Tier | `priority_for_ingest` / source type | Re-ingest interval | Examples |
|---|---|---:|---|
| Tier A | high + leaf + scholarships/admissions/deadlines | **90 days** | Scholarship tables, apply pages, estimated costs |
| Tier B | high + catalog program pages | **180 days** | `preview_program.php` (annual catalog cycle) |
| Tier C | medium hubs | **90 days** | `/admissions/`, `/financial-aid/` roots |
| Tier D | PDF policy/forms | **365 days** | Policy PDFs, disclosure reports |
| Tier E | low / external | **On demand** | Athletics, Presence.io — route only, no embed |

### 5.4 Re-ingest job design

**Script (proposed):** `crawler/refresh.py`

```python
# Pseudocode — NOT implemented
def sources_due_for_refresh(now) -> list[Source]:
    for source in load_registry():
        tier = schedule_tier(source)
        last = parse_ts(source.last_ingested_timestamp)
        if last is None or (now - last) > tier.interval:
            yield source

def refresh_due_sources(dry_run=False):
    for source in sources_due_for_refresh(utcnow()):
        result = ingest_source(source)
        if result["ok"]:
            update_registry_field(source.source_id,
                last_ingested_timestamp=utcnow(),
                content_hash=result["hash"])
```

**CLI:**

```bash
python refresh.py --dry-run          # list due sources
python refresh.py --tier high        # refresh all high-priority due
python refresh.py --source SRC-031   # force single source
python refresh.py --full             # initial backfill (implementation sprint)
```

### 5.5 Cron / scheduler options (pick one in implementation)

**Option A — OS cron (simplest for dev/staging):**

```cron
# /etc/cron.d/askmcneese-ingest
# Weekly: check for due sources, ingest max 20 per run
0 3 * * 0 deploy-user cd /app/askmcneese/crawler && .venv/bin/python refresh.py --max 20 >> logs/refresh.log 2>&1
```

**Option B — APScheduler inside FastAPI (not recommended for heavy ingest):**

- Ingest holds GIL/CPU during embed; can starve `/ask` latency
- Better: separate worker process

**Option C — GitHub Actions scheduled workflow (good for MVP):**

```yaml
# .github/workflows/ingest-refresh.yml
on:
  schedule: [{ cron: '0 8 * * 1' }]  # Mondays 08:00 UTC
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - run: python crawler/refresh.py --max 30
```

**Recommendation:** Option C for MVP (no server cron access needed); migrate to Option A in production.

### 5.6 Full backfill plan (one-time, implementation sprint)

Ordered ingest batches:

| Batch | Sources | Est. chunks |
|---|---|---:|
| 1 — Scholarships + admissions leaves | ~25 | ~120 |
| 2 — Catalog `preview_program.php` (all poids) | ~80–120 | ~400–600 |
| 3 — Financial aid + registrar leaves | ~40 | ~150 |
| 4 — Policy pages + PDFs | ~30 | ~80 |
| 5 — Medium hubs | ~15 | ~60 |
| **Total** | **~180–230** | **~800–1,200** |

After backfill: switch default API path to `use_web_search=False` for deterministic eval, OR hybrid (KB primary + web supplement).

---

## Implementation Sprint Plan (One Sprint)

| Day | Task | Output |
|---|---|---|
| 1 | Catalog inventory crawl; expand CSV to ~120 program URLs | Updated `sitemap_expanded.csv` |
| 1 | PDF link extraction from policy/disclosure hubs | +15–30 PDF rows |
| 2 | PM review; merge into `source_registry_extended.csv` | ~180 approved rows |
| 2 | Implement `ingest_pdf.py` (minimal: pymupdf text + pdfplumber tables) | PDF chunks in Chroma |
| 3 | Wire `ingest_source()` router; relax registry gate for extended IDs | Unified ingest |
| 3 | Full backfill batch 1–2 (scholarships + catalog) | ~500+ chunks |
| 4 | Full backfill batch 3–4; add `last_ingested_timestamp` updates | ~800+ chunks |
| 4 | Implement `refresh.py` (dry-run + tier filter) | Manual refresh works |
| 5 | Re-run eval harness (`run_eval.py`); tune routing to KB mode | 100% fact recall on golden Qs |
| 5 | Document cron (GitHub Action workflow stub) | Refresh design complete |

---

## Risks and Open Questions

1. **Catalog enumeration:** Must confirm `catoid=102` is 2026–2027 and scrape all `poid` values — initial pass found only 1 program page.
2. **Duplicate scholarship mirrors:** `/scholarships/` vs `/financial-aid/` — need canonical URL policy before ingest doubles table content.
3. **Cloudflare on bulk ingest:** Rate-limit ingest; reuse Playwright fallback from `browser_fetch.py`.
4. **PM approval gate:** Extended registry should not auto-set `Approval Status=Approved` — keep `Pending` until Content/PM sign-off.
5. **Chroma embedding consistency:** Re-ingest should use same default embedding model; document model name in collection metadata.
6. **No PostgreSQL:** If PM expects Postgres, that is a separate infrastructure task — this proposal stays CSV-based unless directed otherwise.

---

## Files Produced by This Analysis

| File | Purpose |
|---|---|
| [`knowledge/sitemap_expanded.csv`](../../knowledge/sitemap_expanded.csv) | 200 URL rows — Task 1 output |
| [`docs/knowledge/registry_expansion_proposal.md`](registry_expansion_proposal.md) | This document |
| [`crawler/scripts/build_sitemap_expanded.py`](../../crawler/scripts/build_sitemap_expanded.py) | Regenerator script for Task 1 CSV |

**Not modified (per instructions):** `source_registry_seed.csv`, `ingest.py`, ChromaDB contents.
