"""Task 6 - Backfill ChromaDB from the merged registry.

Reads ``knowledge/source_registry_merged.csv``, selects sources by batch, fetches
each (one shared headless Chromium handles both Cloudflare on www.mcneese.edu and
the JS-rendered catalog), cleans + chunks (structure-aware) or runs the PDF
pipeline, and upserts into the same ChromaDB collection the backend reads.

Batches
-------
* ``batch1`` - scholarship / admissions / financial-aid leaf HTML pages.
* ``batch2`` - catalog program pages (dynamic_catalog).
* ``pdf``    - validated PDFs.
* ``all``    - everything selected across the above.

Resumability
------------
Each successfully ingested row gets ``last_ingested_timestamp`` written back to
the merged CSV. Re-running skips rows that already have a timestamp unless
``--force`` is given. Progress is logged to ``crawler/logs/``.

Usage::

    python askmcneese/crawler/scripts/backfill_chromadb.py --batch batch1
    python askmcneese/crawler/scripts/backfill_chromadb.py --batch batch2 --limit 30
    python askmcneese/crawler/scripts/backfill_chromadb.py --batch all --include-pending
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import sys
import time
from pathlib import Path

_THIS = Path(__file__).resolve()
_REPO = _THIS.parents[2]           # .../askmcneese
_CRAWLER = _REPO / "crawler"
sys.path.insert(0, str(_CRAWLER))

import httpx  # noqa: E402

from clean_text import clean_html  # noqa: E402
from chunker import chunk_text  # noqa: E402
from browser_fetch import is_cloudflare_block  # noqa: E402
from ingest import CHROMA_DIR, COLLECTION  # noqa: E402
from ingest_pdf import ingest_pdf  # noqa: E402

MERGED_CSV = _REPO / "knowledge" / "source_registry_merged.csv"
LOG_DIR = _CRAWLER / "logs"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

BATCH1_CATEGORIES = {"scholarship_leaf", "financial_aid_leaf", "admissions_leaf"}
BATCH1_URL_HINTS = ("scholarship", "financial-aid", "admissions", "international")


# ---------------------------------------------------------------------------
# Registry IO
# ---------------------------------------------------------------------------
def load_rows() -> list[dict]:
    with MERGED_CSV.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def save_rows(rows: list[dict], fieldnames: list[str]) -> None:
    with MERGED_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def select(rows: list[dict], batch: str, include_pending: bool) -> list[dict]:
    def approved(r: dict) -> bool:
        status = (r.get("PM_Review_Status") or "").strip().lower()
        allowed = (r.get("Allowed_for_AI_Retrieval") or "").strip().lower()
        if status == "approved" or allowed.startswith("yes"):
            return True
        return include_pending  # pre-approve high-priority pending rows for MVP

    picked: list[dict] = []
    for r in rows:
        ct = (r.get("content_type") or "").strip()
        cat = (r.get("category") or "").strip()
        url = (r.get("url") or "").strip().lower()
        if not approved(r):
            continue
        is_b1 = cat in BATCH1_CATEGORIES or (
            ct == "html" and any(h in url for h in BATCH1_URL_HINTS)
        )
        is_b2 = ct == "dynamic_catalog"
        is_pdf = ct == "pdf"
        if batch == "batch1" and is_b1:
            picked.append(r)
        elif batch == "batch2" and is_b2:
            picked.append(r)
        elif batch == "pdf" and is_pdf:
            picked.append(r)
        elif batch == "all" and (is_b1 or is_b2 or is_pdf):
            picked.append(r)
    # High priority first, then stable by source_id.
    prio = {"high": 0, "medium": 1, "low": 2}
    picked.sort(key=lambda r: (prio.get((r.get("priority_for_ingest") or "").strip(), 9),
                               r.get("source_id", "")))
    return picked


# ---------------------------------------------------------------------------
# Fetching (single shared browser)
# ---------------------------------------------------------------------------
class Fetcher:
    def __init__(self) -> None:
        self._pw = None
        self._browser = None
        self._page = None
        self._http = httpx.Client(headers={"User-Agent": USER_AGENT},
                                  follow_redirects=True, timeout=25)

    def _ensure_browser(self):
        if self._page is None:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self._page = self._browser.new_page(user_agent=USER_AGENT)
        return self._page

    def fetch_html(self, url: str, force_browser: bool = False) -> tuple[int, str]:
        if not force_browser:
            try:
                r = self._http.get(url)
                if r.status_code == 200 and r.text and not is_cloudflare_block(r.status_code, r.text):
                    return r.status_code, r.text
            except Exception:  # noqa: BLE001 - fall through to browser
                pass
        page = self._ensure_browser()
        resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)
        return (resp.status if resp else 0), page.content()

    def close(self) -> None:
        try:
            self._http.close()
        except Exception:  # noqa: BLE001
            pass
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()


# ---------------------------------------------------------------------------
# Ingest a single HTML/catalog row
# ---------------------------------------------------------------------------
def ingest_html_row(row: dict, fetcher: Fetcher, collection) -> dict:
    url = row["url"]
    ct = (row.get("content_type") or "").strip()
    force_browser = ct == "dynamic_catalog" or "catalog.mcneese.edu" in url
    status, html = fetcher.fetch_html(url, force_browser=force_browser)
    if status != 200 or not html:
        return {"ok": False, "error": f"fetch status {status}"}
    text = clean_html(html)
    if not text or len(text.strip()) < 50:
        return {"ok": False, "error": "empty after clean"}
    chunks = chunk_text(
        text,
        source_url=url,
        title=row.get("source_name", ""),
        category=row.get("category", ""),
        trust_tier="",
        last_checked_date="",
        source_id=row.get("source_id", "SRC"),
    )
    if not chunks:
        return {"ok": False, "error": "no chunks"}
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{
            "source_url": c.source_url,
            "source_id": row.get("source_id", ""),
            "title": c.title,
            "category": c.category,
            "trust_tier": c.trust_tier,
            "last_checked_date": c.last_checked_date,
            "chunk_index": c.chunk_index,
            "chunk_type": c.chunk_type,
            "content_type": ct or "html",
        } for c in chunks],
    )
    return {"ok": True, "chunks": len(chunks)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill ChromaDB from the merged registry.")
    ap.add_argument("--batch", choices=["batch1", "batch2", "pdf", "all"], default="batch1")
    ap.add_argument("--limit", type=int, default=0, help="Max sources this run (0 = no limit)")
    ap.add_argument("--include-pending", action="store_true",
                    help="Also ingest high-priority Pending_Review rows (MVP pre-approval)")
    ap.add_argument("--force", action="store_true", help="Re-ingest even if already timestamped")
    args = ap.parse_args()

    import chromadb
    collection = chromadb.PersistentClient(path=str(CHROMA_DIR)).get_or_create_collection(COLLECTION)

    rows = load_rows()
    fieldnames = list(rows[0].keys()) if rows else []
    targets = select(rows, args.batch, args.include_pending)
    if not args.force:
        targets = [r for r in targets if not (r.get("last_ingested_timestamp") or "").strip()]
    if args.limit:
        targets = targets[:args.limit]

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"backfill_{args.batch}_{_dt.datetime.now():%Y%m%d_%H%M%S}.log"
    log = log_path.open("w", encoding="utf-8")

    def emit(msg: str) -> None:
        print(msg)
        log.write(msg + "\n")
        log.flush()

    emit(f"Backfill batch={args.batch} targets={len(targets)} "
         f"start_count={collection.count()} include_pending={args.include_pending}")

    fetcher = Fetcher()
    ok = fail = total_chunks = 0
    try:
        for i, row in enumerate(targets, 1):
            sid = row.get("source_id", "?")
            url = row["url"]
            ct = (row.get("content_type") or "").strip()
            t0 = time.perf_counter()
            try:
                if ct == "pdf":
                    res = ingest_pdf(url, meta={
                        "source_id": sid,
                        "title": row.get("source_name", ""),
                        "category": row.get("category", ""),
                    }, collection=collection)
                else:
                    res = ingest_html_row(row, fetcher, collection)
            except Exception as exc:  # noqa: BLE001
                res = {"ok": False, "error": f"exception: {exc}"}
            dt = (time.perf_counter() - t0) * 1000

            if res.get("ok"):
                ok += 1
                total_chunks += res.get("chunks", 0)
                row["last_ingested_timestamp"] = _dt.datetime.now().isoformat(timespec="seconds")
                emit(f"[{i}/{len(targets)}] OK   {sid} {res.get('chunks')} chunks "
                     f"({dt:.0f}ms) {url}")
            else:
                fail += 1
                emit(f"[{i}/{len(targets)}] FAIL {sid} {res.get('error')} ({dt:.0f}ms) {url}")

            # Persist registry timestamps periodically so a crash is resumable.
            if i % 5 == 0:
                save_rows(rows, fieldnames)
    finally:
        fetcher.close()
        save_rows(rows, fieldnames)
        emit(f"\nDONE batch={args.batch} ok={ok} fail={fail} chunks_added={total_chunks} "
             f"end_count={collection.count()}")
        emit(f"Log: {log_path}")
        log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
