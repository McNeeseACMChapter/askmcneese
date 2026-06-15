"""Browser fetch for Cloudflare-protected McNeese pages.

www.mcneese.edu sits behind Cloudflare. Plain ``requests`` gets HTTP 403 with a
"Just a moment..." challenge page. Tools like ChatGPT browsing pass this because
they run a real browser engine, not because they have special API access.

This module uses headless Chromium (Playwright) — the same class of fix.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

CLOUDFLARE_MARKERS = ("Just a moment", "cf-browser-verification", "Checking your browser")


def is_cloudflare_block(status: int | None, html: str | None) -> bool:
    """True when the response looks like a Cloudflare bot challenge, not real content."""
    if status == 403:
        return True
    if html:
        head = html[:8000]
        return any(marker in head for marker in CLOUDFLARE_MARKERS)
    return False


def fetch_html_browser(url: str, timeout_ms: int = 60000) -> tuple[int, str]:
    """Load ``url`` in headless Chromium and return (status_code, html)."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # Allow Cloudflare JS challenge to finish if present.
            page.wait_for_timeout(4000)
            html = page.content()
            status = response.status if response else 0
            return status, html
        finally:
            browser.close()
