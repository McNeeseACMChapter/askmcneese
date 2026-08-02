"""Build a compact code-to-record index from the public current McNeese catalog."""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

CATALOG_ID = os.getenv("MCNEESE_CATALOG_ID", "102").strip() or "102"
COURSES_NAV_ID = os.getenv("MCNEESE_CATALOG_COURSES_NAV_ID", "8493").strip() or "8493"
ORIGIN = "https://catalog.mcneese.edu"
OUTPUT = Path(__file__).resolve().parents[2] / "knowledge" / f"catalog_course_index_{CATALOG_ID}.json"
ALLOWED_HOSTS = {
    "catalog.mcneese.edu", "www.mcneese.edu", "acalog-clients.s3.amazonaws.com",
    "ajax.googleapis.com", "cdnjs.cloudflare.com", "code.jquery.com",
    "challenges.cloudflare.com", "www.google.com",
}


def _page_url(page_number: int) -> str:
    if page_number == 1:
        return f"{ORIGIN}/content.php?catoid={CATALOG_ID}&navoid={COURSES_NAV_ID}"
    return (
        f"{ORIGIN}/content.php?catoid={CATALOG_ID}&catoid={CATALOG_ID}"
        f"&navoid={COURSES_NAV_ID}&filter%5Bitem_type%5D=3"
        f"&filter%5Bonly_active%5D=1&filter%5B3%5D=1"
        f"&filter%5Bcpage%5D={page_number}#acalog_template_course_filter"
    )


def _valid_course_url(href: str) -> str | None:
    url = urljoin(f"{ORIGIN}/", href or "")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if (
        parsed.scheme == "https"
        and parsed.hostname == "catalog.mcneese.edu"
        and parsed.path == "/preview_course_nopop.php"
        and params.get("catoid") == [CATALOG_ID]
        and (params.get("coid") or [""])[0].isdigit()
    ):
        return url
    return None


async def _guard(route) -> None:
    parsed = urlparse(route.request.url)
    host = (parsed.hostname or "").lower().rstrip(".")
    allowed = host in ALLOWED_HOSTS or host.endswith(".token.awswaf.com")
    if parsed.scheme not in {"http", "https"} or not allowed:
        await route.abort()
    elif route.request.resource_type in {"image", "media", "font"}:
        await route.abort()
    else:
        await route.continue_()


async def build_index() -> dict[str, dict[str, str]]:
    from playwright.async_api import async_playwright

    entries: dict[str, dict[str, str]] = {}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = await browser.new_context()
        await context.route("**/*", _guard)
        page = await context.new_page()
        try:
            page_number = 1
            max_page = 1
            while page_number <= max_page and page_number <= 100:
                await page.goto(_page_url(page_number), wait_until="domcontentloaded", timeout=25_000)
                course_links = page.locator('a[href*="preview_course_nopop.php"]')
                await course_links.first.wait_for(timeout=15_000)
                links = await course_links.evaluate_all(
                    r"""els => els.map(a => ({
                        label: (a.textContent || '').replace(/\s+/g, ' ').trim(),
                        href: a.getAttribute('href') || ''
                    })).filter(x => x.label && x.href)"""
                )
                for item in links:
                    match = re.match(r"^([A-Z]{2,5})\s+(\d{3,4}[A-Z]?)\s*-\s*(.+)$", str(item["label"]), re.I)
                    url = _valid_course_url(str(item["href"]))
                    if not match or not url:
                        continue
                    code = f"{match.group(1).upper()} {match.group(2).upper()}"
                    entries[code] = {"title": str(item["label"]), "url": url}

                paging_hrefs = await page.locator('a[href*="filter%5Bcpage%5D="]').evaluate_all(
                    "els => els.map(a => a.getAttribute('href') || '')"
                )
                for href in paging_hrefs:
                    found = re.search(r"filter%5Bcpage%5D=(\d+)", str(href), re.I)
                    if found:
                        max_page = max(max_page, int(found.group(1)))
                page_number += 1
        finally:
            await context.close()
            await browser.close()
    return dict(sorted(entries.items()))


async def main() -> None:
    entries = await build_index()
    payload = {"catalog_id": CATALOG_ID, "course_count": len(entries), "courses": entries}
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} courses to {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
