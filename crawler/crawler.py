"""BE-01 — Crawler v0.

Fetch one approved McNeese public URL. Rejects any URL that is not present in
the source registry or not marked allowed for AI retrieval. Saves raw HTML to a
local, gitignored folder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import requests

from source_registry import Source, find_source

RAW_DIR = Path(__file__).resolve().parent / "raw"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20


@dataclass
class FetchResult:
    url: str
    ok: bool
    status: int | None = None
    html: str | None = None
    source: Source | None = None
    error: str | None = None
    raw_path: str | None = None
    meta: dict = field(default_factory=dict)


def _slugify(url: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in url).strip("_")[:120]


def fetch_url(url: str, allow_pending: bool = True) -> FetchResult:
    """Fetch a single approved URL.

    ``allow_pending`` lets the Week 1 proof run on sources whose Approval Status
    is still "Pending" (the PM sign-off gate). Set it to False to require a
    formally PM-approved source.
    """
    source = find_source(url)
    if source is None:
        return FetchResult(url=url, ok=False, error="URL not in source registry — rejected.")
    if not source.crawl_allowed:
        return FetchResult(url=url, ok=False, source=source,
                           error="Source not allowed for AI retrieval — rejected.")
    if not source.pm_approved and not allow_pending:
        return FetchResult(url=url, ok=False, source=source,
                           error="Source approval status is not 'Approved' — rejected.")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return FetchResult(url=url, ok=False, source=source, error=f"Request failed: {exc}")

    if resp.status_code != 200:
        return FetchResult(url=url, ok=False, status=resp.status_code, source=source,
                           error=f"Non-200 response: {resp.status_code}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"{_slugify(url)}.html"
    raw_path.write_text(resp.text, encoding="utf-8")

    return FetchResult(
        url=url,
        ok=True,
        status=resp.status_code,
        html=resp.text,
        source=source,
        raw_path=str(raw_path),
        meta={
            "source_id": source.source_id,
            "title": source.title,
            "category": source.category,
            "trust_tier": source.trust_tier,
            "last_checked_date": source.last_checked_date,
        },
    )


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.mcneese.edu/"
    result = fetch_url(target)
    if result.ok:
        print(f"OK {result.status}  {result.url}")
        print(f"Saved raw HTML -> {result.raw_path} ({len(result.html or '')} chars)")
    else:
        print(f"REJECTED/FAILED  {result.url}\n  {result.error}")
