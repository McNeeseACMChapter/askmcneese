"""Task 2 - PDF Discovery from Hub Pages.

McNeese links most policy / disclosure / form PDFs from hub pages rather than
listing them in a sitemap. This script:

A) Reads ``knowledge/source_registry_seed.csv`` and selects hub rows whose name /
   category / URL match policy-, form-, disclosure-, financial-aid- or Title IX
   keywords.
B) Renders each hub with headless Chromium (www.mcneese.edu is behind
   Cloudflare) and extracts every ``*.pdf`` link on the mcneese.edu domain.
C) Sends a HEAD (falling back to a ranged GET) to each PDF to confirm it is a
   real, reachable ``application/pdf``.
D) Heuristically categorizes each PDF (policy / form / disclosure / report / other).

Output: ``knowledge/discovered_pdfs.csv``

Run standalone::

    python askmcneese/crawler/scripts/discover_pdfs.py
"""

from __future__ import annotations

import csv
import datetime as _dt
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

_THIS = Path(__file__).resolve()
_REPO = _THIS.parents[2]  # .../askmcneese
sys.path.insert(0, str(_REPO / "crawler"))

from browser_fetch import fetch_html_browser  # noqa: E402

KNOWLEDGE_DIR = _REPO / "knowledge"
SEED_CSV = KNOWLEDGE_DIR / "source_registry_seed.csv"
OUT_CSV = KNOWLEDGE_DIR / "discovered_pdfs.csv"

# Hub selection keywords (matched against Source Name / Information Category / URL).
HUB_KEYWORDS = (
    "policy",
    "policies",
    "form",
    "disclosure",
    "consumer",
    "title ix",
    "titleix",
    "financial aid",
    "financial-aid",
    "registrar",
    "compliance",
)

# Always-crawl hubs from the task brief (in case seed rows are absent/renamed).
FALLBACK_HUBS = [
    ("SRC-020", "https://www.mcneese.edu/policy/"),
    ("SRC-015", "https://www.mcneese.edu/registrar/"),
    ("SRC-005", "https://www.mcneese.edu/financial-aid/"),
    ("SRC-022", "https://www.mcneese.edu/ire/consumer-disclosures/"),
    ("SRC-023", "https://www.mcneese.edu/titleix/data/"),
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

MCNEESE_DOMAINS = ("mcneese.edu",)


# ---------------------------------------------------------------------------
# A) Load hub URLs from the seed registry
# ---------------------------------------------------------------------------
def load_hub_urls() -> list[tuple[str, str]]:
    """Return [(source_id, url)] of hubs likely to contain PDF links."""
    hubs: dict[str, str] = {}
    if SEED_CSV.exists():
        # utf-8-sig strips a possible BOM so the "Source ID" header key matches.
        with SEED_CSV.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                sid = (row.get("Source ID") or "").strip()
                url = (row.get("Source URL") or "").strip()
                name = (row.get("Source Name") or "").lower()
                cat = (row.get("Information Category") or "").lower()
                haystack = f"{name} {cat} {url.lower()}"
                if url and any(k in haystack for k in HUB_KEYWORDS):
                    hubs[url] = sid
    # Merge in fallbacks (do not overwrite a seed-derived source id).
    for sid, url in FALLBACK_HUBS:
        hubs.setdefault(url, sid)
    return [(sid, url) for url, sid in hubs.items()]


# ---------------------------------------------------------------------------
# B) Crawl hubs, extract PDF links
# ---------------------------------------------------------------------------
def _is_mcneese(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in MCNEESE_DOMAINS)


def extract_pdf_links(base_url: str, html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    pdfs: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.lower().startswith(("mailto:", "javascript:", "tel:")):
            continue
        absolute = urljoin(base_url, href)
        # Drop fragments/queries for the extension test, but keep full URL.
        path = urlparse(absolute).path.lower()
        if path.endswith(".pdf") and _is_mcneese(absolute):
            pdfs.add(absolute.split("#")[0])
    return pdfs


def crawl_hub(source_id: str, url: str) -> set[str]:
    print(f"  crawling {source_id} {url}")
    try:
        status, html = fetch_html_browser(url)
    except Exception as exc:  # noqa: BLE001
        print(f"    render ERROR: {exc}", file=sys.stderr)
        return set()
    if not html:
        print("    empty HTML")
        return set()
    pdfs = extract_pdf_links(url, html)
    print(f"    status {status}, {len(pdfs)} pdf link(s)")
    return pdfs


# ---------------------------------------------------------------------------
# C) Validate PDFs
# ---------------------------------------------------------------------------
def validate_pdf(client: httpx.Client, url: str) -> tuple[str, str]:
    """Return (status, content_type). status in {ok, not_pdf, http_<code>, error}."""
    try:
        r = client.head(url, follow_redirects=True, timeout=25)
        if r.status_code == 405 or (r.status_code >= 400):
            # Some servers reject HEAD; try a tiny ranged GET.
            r = client.get(url, follow_redirects=True, timeout=25,
                           headers={"Range": "bytes=0-1024"})
        ctype = r.headers.get("content-type", "").lower()
        if r.status_code in (200, 206):
            if "pdf" in ctype or url.lower().endswith(".pdf"):
                return "ok", ctype or "application/pdf"
            return "not_pdf", ctype
        return f"http_{r.status_code}", ctype
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:60]


# ---------------------------------------------------------------------------
# D) Categorize
# ---------------------------------------------------------------------------
def categorize_pdf(url: str) -> str:
    u = url.lower()
    if any(k in u for k in ("form", "application", "request", "petition")):
        return "form"
    if any(k in u for k in ("policy", "policies", "procedure", "handbook", "code")):
        return "policy"
    if any(k in u for k in ("disclosure", "consumer", "clery", "annual-security", "asr")):
        return "disclosure"
    if any(k in u for k in ("report", "data", "factbook", "statistic")):
        return "report"
    return "other"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
OUT_COLUMNS = ["pdf_url", "category", "source_id_hub", "hub_url",
               "validation_status", "content_type", "discovered_date"]


def main() -> int:
    hubs = load_hub_urls()
    print(f"Selected {len(hubs)} hub URL(s) to crawl:")
    for sid, url in hubs:
        print(f"  {sid}: {url}")

    # Map pdf_url -> (hub_source_id, hub_url)
    found: dict[str, tuple[str, str]] = {}
    print("\nCrawling hubs...")
    for sid, url in hubs:
        for pdf in crawl_hub(sid, url):
            found.setdefault(pdf, (sid, url))

    print(f"\nTotal unique PDF links discovered: {len(found)}")
    if not found:
        print("No PDFs found.", file=sys.stderr)
        # still write empty file with header for downstream idempotency
        _write([], OUT_CSV)
        return 0

    print("\nValidating PDFs (HEAD / ranged GET)...")
    today = _dt.date.today().isoformat()
    rows: list[dict] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        for pdf, (sid, hub) in sorted(found.items()):
            status, ctype = validate_pdf(client, pdf)
            rows.append({
                "pdf_url": pdf,
                "category": categorize_pdf(pdf),
                "source_id_hub": sid,
                "hub_url": hub,
                "validation_status": status,
                "content_type": ctype,
                "discovered_date": today,
            })
            print(f"  [{status:>9}] {categorize_pdf(pdf):<10} {pdf}")

    _write(rows, OUT_CSV)

    # Summary counts
    by_cat: dict[str, int] = {}
    ok = 0
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
        if r["validation_status"] == "ok":
            ok += 1
    print(f"\nWrote {len(rows)} rows -> {OUT_CSV}")
    print(f"Validated OK: {ok}/{len(rows)}")
    print("By category:", ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    return 0


def _write(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    raise SystemExit(main())
