"""Task 1 - Catalog Inventory Crawl.

Enumerate every Modern Campus catalog *program* page
(``preview_program.php?catoid=102&poid=*``) for McNeese State University.

The catalog root (``catalog.mcneese.edu``) lists programs on an "Inventory of
Degree and Certificate Programs" navigation page, but that page renders its
program links with JavaScript and the ``content.php`` endpoint returns HTTP 202
with an empty body to plain HTTP clients (bot protection). We therefore render
the inventory page(s) with headless Chromium (Playwright) - the same mechanism
``crawler/browser_fetch.py`` already uses for Cloudflare-protected pages.

Outputs
-------
1. ``knowledge/catalog_programs.csv``  (url, title, catoid, poid, discovered_date)
2. Appends the same programs to ``knowledge/sitemap_expanded.csv`` with
   ``category_heuristic=catalog_program`` and ``priority=high``.

Run standalone::

    python askmcneese/crawler/scripts/enumerate_catalog_programs.py
    python askmcneese/crawler/scripts/enumerate_catalog_programs.py --catoid 102 --no-merge
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS = Path(__file__).resolve()
_REPO = _THIS.parents[2]  # .../askmcneese
KNOWLEDGE_DIR = _REPO / "knowledge"
CATALOG_CSV = KNOWLEDGE_DIR / "catalog_programs.csv"
SITEMAP_CSV = KNOWLEDGE_DIR / "sitemap_expanded.csv"

CATALOG_BASE = "https://catalog.mcneese.edu/"
DEFAULT_CATOID = 102  # 2026-2027 catalog

# Navigation pages known to list programs. 8495 = "Inventory of Degree and
# Certificate Programs" (the master list); 8461 = "Programs Listed by College".
INVENTORY_NAVOIDS = [8495, 8461]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Tolerate both raw ``&`` and HTML-entity ``&amp;`` between query params, because
# Playwright's ``page.content()`` re-serializes hrefs with entities.
_PROGRAM_HREF = re.compile(r"preview_program\.php\?catoid=(\d+)&(?:amp;)?poid=(\d+)")


# ---------------------------------------------------------------------------
# A) / B) Discover inventory pages and enumerate poids
# ---------------------------------------------------------------------------
def render_inventory_html(catoid: int, navoids: list[int]) -> str:
    """Render every inventory nav page with Playwright and concatenate the HTML."""
    from playwright.sync_api import sync_playwright

    combined: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            for navoid in navoids:
                url = f"{CATALOG_BASE}content.php?catoid={catoid}&navoid={navoid}"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(4000)  # let program list JS settle
                    html = page.content()
                    n = len(_PROGRAM_HREF.findall(html))
                    print(f"  navoid {navoid}: rendered {len(html):>8} bytes, {n} program links")
                    combined.append(html)
                except Exception as exc:  # noqa: BLE001
                    print(f"  navoid {navoid}: ERROR {exc}", file=sys.stderr)
        finally:
            browser.close()
    return "\n".join(combined)


def extract_programs(html: str, catoid: int) -> dict[str, dict]:
    """Return {poid: {title, catoid, poid, url}} parsed from inventory HTML."""
    soup = BeautifulSoup(html, "html.parser")
    programs: dict[str, dict] = {}
    for a in soup.find_all("a", href=True):
        m = _PROGRAM_HREF.search(a["href"])
        if not m:
            continue
        link_catoid, poid = m.group(1), m.group(2)
        # Keep only the requested catalog year.
        if int(link_catoid) != catoid:
            continue
        title = a.get_text(strip=True)
        # First occurrence with a non-empty title wins; otherwise keep placeholder.
        if poid in programs and programs[poid]["title"]:
            continue
        programs[poid] = {
            "poid": poid,
            "catoid": str(catoid),
            "title": title or f"(untitled poid {poid})",
            "url": f"{CATALOG_BASE}preview_program.php?catoid={catoid}&poid={poid}",
        }
    return programs


# ---------------------------------------------------------------------------
# C) Write catalog_programs.csv
# ---------------------------------------------------------------------------
def write_catalog_csv(programs: dict[str, dict], path: Path) -> None:
    today = _dt.date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(programs.values(), key=lambda r: int(r["poid"]))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "title", "catoid", "poid", "discovered_date"])
        for r in rows:
            w.writerow([r["url"], r["title"], r["catoid"], r["poid"], today])
    print(f"Wrote {len(rows)} programs -> {path}")


# ---------------------------------------------------------------------------
# D) Merge into sitemap_expanded.csv
# ---------------------------------------------------------------------------
SITEMAP_COLUMNS = [
    "url",
    "category_heuristic",
    "is_pdf",
    "domain",
    "extracted_from",
    "priority",
    "proposed_parent_source_id",
]


def merge_into_sitemap(programs: dict[str, dict], path: Path) -> tuple[int, int]:
    """Append catalog programs to sitemap_expanded.csv. Returns (added, skipped)."""
    existing_urls: set[str] = set()
    rows: list[dict] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(row)
                existing_urls.add(row["url"].strip())

    added = skipped = 0
    for prog in sorted(programs.values(), key=lambda r: int(r["poid"])):
        if prog["url"] in existing_urls:
            skipped += 1
            continue
        rows.append(
            {
                "url": prog["url"],
                "category_heuristic": "catalog_program",
                "is_pdf": "false",
                "domain": "catalog.mcneese.edu",
                "extracted_from": "catalog_inventory",
                "priority": "high",
                "proposed_parent_source_id": "SRC-011",
            }
        )
        existing_urls.add(prog["url"])
        added += 1

    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SITEMAP_COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in SITEMAP_COLUMNS})

    print(f"Merged into {path}: +{added} new, {skipped} already present, {len(rows)} total")
    return added, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Enumerate McNeese catalog program pages.")
    ap.add_argument("--catoid", type=int, default=DEFAULT_CATOID)
    ap.add_argument("--navoids", type=int, nargs="*", default=INVENTORY_NAVOIDS)
    ap.add_argument("--no-merge", action="store_true", help="Skip merging into sitemap_expanded.csv")
    args = ap.parse_args(argv)

    print(f"Rendering catalog inventory (catoid={args.catoid}, navoids={args.navoids})...")
    html = render_inventory_html(args.catoid, args.navoids)
    programs = extract_programs(html, args.catoid)
    print(f"Discovered {len(programs)} unique program poids.")

    if not programs:
        print("No programs found - inventory rendering may have failed.", file=sys.stderr)
        return 1

    write_catalog_csv(programs, CATALOG_CSV)

    # Sample output (5 rows)
    print("\nSample programs:")
    for r in sorted(programs.values(), key=lambda r: int(r["poid"]))[:5]:
        print(f"  poid {r['poid']:>6}  {r['title'][:60]:<60}  {r['url']}")

    if not args.no_merge:
        merge_into_sitemap(programs, SITEMAP_CSV)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
