"""Exact current-catalog lookup for a McNeese course code."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from app.services.catalog_retrieval import CATALOG_ID, CATALOG_ORIGIN, CATALOG_YEAR
from app.services.rccs.evidence import sanitize_evidence_text
from app.services.rccs.models import RetrievedEvidence, utcnow

COURSES_NAV_ID = os.getenv("MCNEESE_CATALOG_COURSES_NAV_ID", "8493").strip() or "8493"
_ALLOWED_HOSTS = {
    "catalog.mcneese.edu", "www.mcneese.edu", "acalog-clients.s3.amazonaws.com",
    "ajax.googleapis.com", "cdnjs.cloudflare.com", "code.jquery.com",
    "challenges.cloudflare.com", "www.google.com",
}
_LOCK = asyncio.Lock()
_CACHE: dict[str, tuple[float, list[RetrievedEvidence]]] = {}


def _course_code(question: str) -> tuple[str, str] | None:
    match = re.search(r"\b([A-Z]{2,5})\s*(\d{3,4}[A-Z]?)\b", question or "", re.I)
    return (match.group(1).upper(), match.group(2).upper()) if match else None


def _safe_course_url(href: str) -> str | None:
    url = urljoin(f"{CATALOG_ORIGIN}/", href or "")
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


@lru_cache(maxsize=1)
def _course_index() -> dict[str, dict[str, str]]:
    path = Path(__file__).resolve().parents[3] / "knowledge" / f"catalog_course_index_{CATALOG_ID}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        courses = payload.get("courses")
        return courses if isinstance(courses, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


async def _guard(route) -> None:
    parsed = urlparse(route.request.url)
    host = (parsed.hostname or "").lower().rstrip(".")
    allowed = host in _ALLOWED_HOSTS or host.endswith(".token.awswaf.com")
    if parsed.scheme not in {"http", "https"} or not allowed:
        await route.abort()
    elif route.request.resource_type in {"image", "media", "font"}:
        await route.abort()
    else:
        await route.continue_()


async def _render(question: str) -> tuple[str, str, str] | None:
    code = _course_code(question)
    if not code:
        return None
    if os.getenv("WEB_BROWSER_MODE", "off").strip().lower() not in {"always", "fallback"}:
        return None
    prefix, number = code
    try:
        from playwright.async_api import async_playwright
    except Exception:
        return None

    index_url = f"{CATALOG_ORIGIN}/content.php?catoid={CATALOG_ID}&navoid={COURSES_NAV_ID}"
    async with _LOCK:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
            context = await browser.new_context()
            await context.route("**/*", _guard)
            page = await context.new_page()
            try:
                record = _course_index().get(f"{prefix} {number}") or {}
                selected_url = _safe_course_url(str(record.get("url") or ""))
                selected_title = str(record.get("title") or "")
                if not selected_url:
                    filter_url = f"{CATALOG_ORIGIN}/content.php?" + urlencode([
                        ("filter[27]", prefix), ("filter[29]", number),
                        ("filter[course_type]", "-1"), ("filter[keyword]", ""),
                        ("filter[32]", "1"), ("filter[cpage]", "1"),
                        ("cur_cat_oid", CATALOG_ID), ("expand", ""),
                        ("navoid", COURSES_NAV_ID), ("search_database", "Filter"),
                    ])
                    try:
                        await page.goto(filter_url, wait_until="domcontentloaded", timeout=20_000)
                    except Exception:
                        await page.goto(index_url, wait_until="domcontentloaded", timeout=20_000)
                        await page.get_by_label("Choose Course Prefix").select_option(prefix)
                        await page.get_by_label("Choose Course Number").fill(number)
                        await page.get_by_role("button", name="Filter", exact=True).click()
                    links = page.locator('a[href*="preview_course_nopop.php"]')
                    await links.first.wait_for(timeout=12_000)
                    for item in await links.all():
                        label = re.sub(r"\s+", " ", (await item.inner_text()).strip())
                        if re.match(rf"^{re.escape(prefix)}\s*{re.escape(number)}\b", label, re.I):
                            selected_url = _safe_course_url(await item.get_attribute("href") or "")
                            selected_title = label
                            break
                if not selected_url:
                    return None

                await page.goto(selected_url, wait_until="domcontentloaded", timeout=20_000)
                heading = page.locator("#course_preview_title")
                await heading.wait_for(timeout=12_000)
                content = await heading.evaluate(
                    r"""el => {
                        let current = el;
                        for (let i = 0; current && i < 9; i += 1) {
                            const text = (current.innerText || '').replace(/\s+/g, ' ').trim();
                            if (text.length >= 120 && text.length <= 8000) return text;
                            current = current.parentElement;
                        }
                        return '';
                    }"""
                )
                content = sanitize_evidence_text(str(content or ""), 7000)
                if f"{prefix} {number}".lower() not in content.lower() or len(content) < 80:
                    return None
                return str(await heading.inner_text() or selected_title).strip(), selected_url, content
            finally:
                await context.close()
                await browser.close()


async def retrieve_catalog_course(question: str) -> tuple[list[RetrievedEvidence], str | None]:
    code = _course_code(question)
    cache_key = " ".join(code) if code else ""
    cached = _CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < 3600:
        return cached[1], None
    try:
        rendered = await asyncio.wait_for(_render(question), timeout=45.0)
    except asyncio.TimeoutError:
        return [], "catalog_course_timeout"
    except Exception as exc:
        return [], f"catalog_course_failed:{type(exc).__name__}"
    if not rendered:
        return [], "catalog_course_not_found"
    title, url, content = rendered
    evidence = [RetrievedEvidence(
        evidence_id=f"ev-course-{abs(hash(url)) % 10_000_000}",
        title=f"{title} - {CATALOG_YEAR} Academic Catalog",
        url=url,
        text=f"Official McNeese {CATALOG_YEAR} course record.\n{content}",
        source_id="SRC-011",
        source_name="McNeese Academic Catalog",
        source_tier="A",
        trust_level="official",
        category="course_catalog",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.99,
        metadata={"citation_label": f"Official {CATALOG_YEAR} catalog", "browser_rendered": True},
    )]
    if cache_key:
        _CACHE[cache_key] = (time.monotonic(), evidence)
    return evidence, None
