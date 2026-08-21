"""Task 3 - Merge Extended Registry.

Combine every discovered source into one production-ready registry:

  * ``source_registry_seed.csv``   - 33 curated rows (SRC-001..033), kept as-is.
  * ``sitemap_expanded.csv``       - sitemap + catalog program URLs.
  * ``catalog_programs.csv``       - catalog program pages (subset of the above).
  * ``discovered_pdfs.csv``        - validated PDF URLs.

Output: ``knowledge/source_registry_merged.csv`` with the extended schema from
proposal section 3.1. New rows get IDs from SRC-034 upward, grouped by category
so related leaves are contiguous. New rows are marked ``PM_Review_Status =
Pending_Review``; ``Allowed for AI Retrieval`` is left blank (a PM gate).

Idempotent: re-running regenerates the same file from the source CSVs.

Run standalone::

    python askmcneese/crawler/scripts/merge_registries.py
"""

from __future__ import annotations

import csv
import datetime as _dt
from pathlib import Path
from urllib.parse import urlparse, urlunparse

_THIS = Path(__file__).resolve()
_REPO = _THIS.parents[2]  # .../askmcneese
KNOWLEDGE = _REPO / "knowledge"

SEED_CSV = KNOWLEDGE / "source_registry_seed.csv"
SITEMAP_CSV = KNOWLEDGE / "sitemap_expanded.csv"
CATALOG_CSV = KNOWLEDGE / "catalog_programs.csv"
PDF_CSV = KNOWLEDGE / "discovered_pdfs.csv"
OUT_CSV = KNOWLEDGE / "source_registry_merged.csv"

OUT_COLUMNS = [
    "source_id",
    "source_name",
    "url",
    "domain",
    "content_type",        # html | pdf | dynamic_catalog
    "category",
    "parent_source_id",
    "is_leaf",             # true | false
    "catalog_year",
    "priority_for_ingest", # high | medium | low
    "PM_Review_Status",    # Approved | Pending | Pending_Review
    "Allowed_for_AI_Retrieval",
    "last_ingested_timestamp",
    "content_hash",
    "discovered_from",
    "notes",
]

# Order in which category groups receive new SRC-### ids (keeps related leaves
# contiguous). Anything not listed sorts last, alphabetically.
CATEGORY_ORDER = [
    "scholarship_leaf",
    "admissions_leaf",
    "financial_aid_leaf",
    "academic_leaf",
    "catalog_program",
    "catalog_content",
    "policy",
    "pdf_policy",
    "pdf_form",
    "pdf_disclosure",
    "pdf_report",
    "pdf_other",
    "hub_nav",
]


# ---------------------------------------------------------------------------
# URL normalization / dedup
# ---------------------------------------------------------------------------
def normalize_url(url: str) -> str:
    """Canonical key for dedup. Preserves query (poid) for catalog pages."""
    url = (url or "").strip()
    if not url:
        return ""
    p = urlparse(url)
    scheme = "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/") or "/"
    # Keep query only when it carries identity (catalog poid/catoid/navoid).
    query = p.query if ("poid=" in p.query or "navoid=" in p.query) else ""
    return urlunparse((scheme, netloc, path, "", query, ""))


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def content_type_for(url: str, is_pdf: bool) -> str:
    if is_pdf or url.lower().split("?")[0].endswith(".pdf"):
        return "pdf"
    if "catalog.mcneese.edu" in url and "preview_program.php" in url:
        return "dynamic_catalog"
    return "html"


def catalog_year_for(url: str) -> str:
    # catoid=102 == 2026-2027 catalog.
    if "catalog.mcneese.edu" in url and "catoid=102" in url:
        return "2026-2027"
    return ""


def is_leaf_for(category: str, content_type: str) -> str:
    if content_type in ("pdf", "dynamic_catalog"):
        return "true"
    if category.endswith("_leaf") or category == "catalog_program":
        return "true"
    if any(k in category for k in ("hub", "nav", "content", "root", "index")):
        return "false"
    return "true"


def priority_for(category: str, existing: str, is_leaf: str) -> str:
    if existing in ("high", "medium", "low"):
        return existing
    return "high" if is_leaf == "true" else "medium"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_seed() -> tuple[list[dict], set[str], int]:
    """Return (seed_rows_in_out_schema, seen_norm_urls, max_seed_num)."""
    rows: list[dict] = []
    seen: set[str] = set()
    max_num = 0
    if not SEED_CSV.exists():
        return rows, seen, max_num
    with SEED_CSV.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            sid = (r.get("Source ID") or "").strip()
            url = (r.get("Source URL") or "").strip()
            if sid.startswith("SRC-"):
                try:
                    max_num = max(max_num, int(sid.split("-")[1]))
                except ValueError:
                    pass
            norm = normalize_url(url)
            if norm:
                seen.add(norm)
            ct = content_type_for(url, is_pdf=False)
            rows.append({
                "source_id": sid,
                "source_name": (r.get("Source Name") or "").strip(),
                "url": url,
                "domain": domain_of(url),
                "content_type": ct,
                "category": (r.get("Information Category") or "").strip(),
                "parent_source_id": "",
                "is_leaf": "false",  # seed entries are mostly section hubs
                "catalog_year": catalog_year_for(url),
                "priority_for_ingest": "high",
                "PM_Review_Status": (r.get("Approval Status") or "").strip(),
                "Allowed_for_AI_Retrieval": (r.get("Allowed for AI Retrieval") or "").strip(),
                "last_ingested_timestamp": "",
                "content_hash": "",
                "discovered_from": "seed",
                "notes": (r.get("Notes / Issues") or "").strip(),
            })
    return rows, seen, max_num


def load_sitemap() -> list[dict]:
    out: list[dict] = []
    if not SITEMAP_CSV.exists():
        return out
    with SITEMAP_CSV.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            url = (r.get("url") or "").strip()
            if not url:
                continue
            out.append({
                "url": url,
                "category": (r.get("category_heuristic") or "").strip(),
                "is_pdf": (r.get("is_pdf") or "").strip().lower() == "true",
                "priority": (r.get("priority") or "").strip().lower(),
                "parent": (r.get("proposed_parent_source_id") or "").strip(),
                "title": "",
                "discovered_from": (r.get("extracted_from") or "sitemap").strip(),
            })
    return out


def load_catalog_titles() -> dict[str, str]:
    """Map normalized catalog URL -> program title (for nicer source_name)."""
    titles: dict[str, str] = {}
    if not CATALOG_CSV.exists():
        return titles
    with CATALOG_CSV.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            titles[normalize_url(r.get("url", ""))] = (r.get("title") or "").strip()
    return titles


def load_pdfs() -> list[dict]:
    out: list[dict] = []
    if not PDF_CSV.exists():
        return out
    with PDF_CSV.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if (r.get("validation_status") or "").strip() != "ok":
                continue  # skip 404/403/not_pdf
            url = (r.get("pdf_url") or "").strip()
            if not url:
                continue
            out.append({
                "url": url,
                "category": f"pdf_{(r.get('category') or 'other').strip()}",
                "is_pdf": True,
                "priority": "medium",
                "parent": (r.get("source_id_hub") or "").strip(),
                "title": Path(urlparse(url).path).stem.replace("-", " ").replace("_", " ")[:80],
                "discovered_from": "pdf_hub_crawl",
            })
    return out


# ---------------------------------------------------------------------------
# Main merge
# ---------------------------------------------------------------------------
def main() -> int:
    seed_rows, seen, max_num = load_seed()
    catalog_titles = load_catalog_titles()

    candidates = load_sitemap() + load_pdfs()

    # Dedup across candidate sources, and against seed.
    new_by_norm: dict[str, dict] = {}
    dedup_report: list[tuple[str, str]] = []  # (dropped_url, kept_reason)

    def canonical_rank(cand: dict) -> int:
        # Lower = more canonical. Prefer leaf detail / pdf over hub/nav mirrors.
        cat = cand["category"]
        if cand["is_pdf"]:
            return 1
        if cat == "catalog_program" or cat.endswith("_leaf"):
            return 0
        if any(k in cat for k in ("hub", "nav", "content")):
            return 3
        return 2

    for cand in candidates:
        norm = normalize_url(cand["url"])
        if not norm:
            continue
        if norm in seen:
            dedup_report.append((cand["url"], "mirror of existing seed source"))
            continue
        if norm in new_by_norm:
            keep = new_by_norm[norm]
            if canonical_rank(cand) < canonical_rank(keep):
                dedup_report.append((keep["url"], f"replaced by more-canonical {cand['url']}"))
                new_by_norm[norm] = cand
            else:
                dedup_report.append((cand["url"], f"duplicate of {keep['url']}"))
            continue
        new_by_norm[norm] = cand

    # Order new rows by category group, then URL, and assign SRC ids.
    def cat_key(cand: dict) -> tuple[int, str]:
        cat = cand["category"]
        idx = CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else len(CATEGORY_ORDER)
        return (idx, cand["url"])

    ordered = sorted(new_by_norm.values(), key=cat_key)

    today = _dt.date.today().isoformat()
    new_rows: list[dict] = []
    num = max_num
    for cand in ordered:
        num += 1
        url = cand["url"]
        ct = content_type_for(url, cand["is_pdf"])
        leaf = is_leaf_for(cand["category"], ct)
        norm = normalize_url(url)
        name = catalog_titles.get(norm) or cand["title"] or url.rsplit("/", 1)[-1] or url
        new_rows.append({
            "source_id": f"SRC-{num:03d}",
            "source_name": name,
            "url": url,
            "domain": domain_of(url),
            "content_type": ct,
            "category": cand["category"],
            "parent_source_id": cand["parent"],
            "is_leaf": leaf,
            "catalog_year": catalog_year_for(url),
            "priority_for_ingest": priority_for(cand["category"], cand["priority"], leaf),
            "PM_Review_Status": "Pending_Review",
            "Allowed_for_AI_Retrieval": "",  # PM gate - intentionally blank
            "last_ingested_timestamp": "",
            "content_hash": "",
            "discovered_from": cand["discovered_from"],
            "notes": "",
        })

    all_rows = seed_rows + new_rows
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    # ---- Summary ----
    print(f"Wrote {len(all_rows)} rows -> {OUT_CSV}")
    print(f"  seed rows (unchanged): {len(seed_rows)}  (SRC-001..SRC-{max_num:03d})")
    print(f"  new rows: {len(new_rows)}  (SRC-{max_num + 1:03d}..SRC-{num:03d})")

    def tally(rows, key):
        d: dict[str, int] = {}
        for r in rows:
            d[r[key]] = d.get(r[key], 0) + 1
        return dict(sorted(d.items(), key=lambda kv: -kv[1]))

    print("\nNew rows by content_type:", tally(new_rows, "content_type"))
    print("New rows by priority_for_ingest:", tally(new_rows, "priority_for_ingest"))
    print("New rows by category:")
    for k, v in tally(new_rows, "category").items():
        print(f"  {k:<20} {v}")

    print(f"\nDedup report: {len(dedup_report)} mirror(s)/duplicate(s) dropped")
    for dropped, reason in dedup_report[:15]:
        print(f"  DROP {dropped}\n       -> {reason}")
    if len(dedup_report) > 15:
        print(f"  ... and {len(dedup_report) - 15} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
