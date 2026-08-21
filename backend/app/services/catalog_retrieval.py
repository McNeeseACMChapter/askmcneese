"""Safe, named-program retrieval for the public McNeese academic catalog.

The Modern Campus catalog presents a JavaScript challenge to ordinary HTTP
clients. This renderer is activated only for degree-plan questions, navigates a
fixed allowlisted catalog index, chooses a program link found on that page, and
extracts that program's curriculum. User text is never converted into a URL.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urljoin, urlparse

from app.services.rccs.evidence import sanitize_evidence_text
from app.services.rccs.models import RetrievedEvidence, utcnow

CATALOG_ID = os.getenv("MCNEESE_CATALOG_ID", "102").strip() or "102"
CATALOG_YEAR = (
    os.getenv("MCNEESE_CATALOG_YEAR", "2026-2027").strip() or "2026-2027"
)
CATALOG_PROGRAMS_NAV_ID = (
    os.getenv("MCNEESE_CATALOG_PROGRAMS_NAV_ID", "8461").strip() or "8461"
)
CATALOG_ORIGIN = "https://catalog.mcneese.edu"
CATALOG_PROGRAM_INDEX = (
    f"{CATALOG_ORIGIN}/content.php?catoid={CATALOG_ID}&navoid={CATALOG_PROGRAMS_NAV_ID}"
)
_ALLOWED_BROWSER_HOSTS = {
    "catalog.mcneese.edu",
    "www.mcneese.edu",
    "acalog-clients.s3.amazonaws.com",
    "ajax.googleapis.com",
    "cdnjs.cloudflare.com",
    "code.jquery.com",
    "challenges.cloudflare.com",
    "www.google.com",
}
_INDEX_TTL_SECONDS = 30 * 60
_PROGRAM_TTL_SECONDS = 60 * 60
_RENDER_TIMEOUT_SECONDS = 45.0

_index_cache: tuple[float, list[dict[str, str]]] | None = None
_program_cache: dict[str, tuple[float, str, str]] = {}
_catalog_lock = asyncio.Lock()

_STOPWORDS = {
    "all", "are", "complete", "courses", "course", "degree", "finish",
    "full", "graduate", "list", "need", "program", "requirements", "study",
    "the", "to", "what", "whole", "with", "mcneese",
}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 1 and token not in _STOPWORDS
    }


def _program_score(question: str, label: str) -> float:
    q = (question or "").lower()
    normalized_label = re.sub(r"\s+", " ", label.lower()).strip()
    label_name = normalized_label.split(",", 1)[0].strip()
    q_tokens = _tokens(q)
    label_tokens = _tokens(normalized_label)
    overlap = len(q_tokens & label_tokens)
    score = overlap * 5.0
    if label_name and label_name in q:
        score += 12.0
    score += SequenceMatcher(None, " ".join(sorted(q_tokens)), label_name).ratio() * 2.0

    wants_minor = bool(re.search(r"\bminor\b", q))
    wants_graduate = bool(re.search(r"\b(?:master|masters|graduate|m\.?s\.?|m\.?eng\.?)\b", q))
    is_minor = "minor" in normalized_label
    is_graduate = bool(re.search(r"\b(?:ma|ms|meng|mba|med|mfa|dnp|edd|phd)\b", normalized_label))

    if wants_minor:
        score += 10.0 if is_minor else -6.0
    elif is_minor:
        score -= 8.0
    if wants_graduate:
        score += 8.0 if is_graduate else -5.0
    elif is_graduate:
        score -= 6.0

    # When a major exists only as concentration variants, a broad request should
    # resolve to its general concentration. Explicit concentration words still
    # win naturally through token overlap (for example, "cybersecurity").
    if "concentration" in normalized_label and "concentration" not in q:
        qualifier_tokens = label_tokens - _tokens(label_name) - {
            "concentration", "ba", "bs", "ma", "ms"
        }
        if q_tokens & qualifier_tokens:
            score += 4.0
        else:
            score += 4.0 if "general" in normalized_label else -1.0

    if not wants_graduate:
        # A generic request for a complete degree normally means the bachelor's
        # curriculum, not a minor or graduate concentration.
        if re.search(r",\s*(?:ba|bs|bba|bm|bsme|bsche|bsn)\b", normalized_label):
            score += 4.0
    return score


def _select_program(question: str, programs: list[dict[str, str]]) -> dict[str, str] | None:
    ranked = sorted(
        ((_program_score(question, item["label"]), item) for item in programs),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not ranked or ranked[0][0] < 5.0:
        return None
    return ranked[0][1]

def _safe_program_url(href: str) -> str | None:
    url = urljoin(f"{CATALOG_ORIGIN}/", href or "")
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "catalog.mcneese.edu"
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        return None
    if parsed.path != "/preview_program.php":
        return None
    params = parse_qs(parsed.query)
    poid = (params.get("poid") or [""])[0]
    if params.get("catoid") != [CATALOG_ID] or not poid.isdigit():
        return None
    return url


def _is_allowed_browser_host(hostname: str | None) -> bool:
    host = (hostname or "").lower().rstrip(".")
    return host in _ALLOWED_BROWSER_HOSTS or host.endswith(".token.awswaf.com")


def _guard_catalog_request_sync(route) -> None:
    parsed = urlparse(route.request.url)
    if parsed.scheme in {"https", "http"} and _is_allowed_browser_host(parsed.hostname):
        if route.request.resource_type in {"image", "media", "font"}:
            route.abort()
        else:
            route.continue_()
    else:
        route.abort()


def _render_catalog_sync(question: str) -> tuple[str, str, str] | None:
    """Sync Playwright render — safe under uvicorn on Windows (no asyncio subprocess)."""
    global _index_cache
    if os.getenv("WEB_BROWSER_MODE", "off").strip().lower() not in {"always", "fallback"}:
        return None
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    now = time.monotonic()
    cached_programs = (
        _index_cache[1]
        if _index_cache and now - _index_cache[0] < _INDEX_TTL_SECONDS
        else None
    )
    if cached_programs is not None:
        selected = _select_program(question, cached_programs)
        if selected is None:
            return None
        program_url = _safe_program_url(selected["href"])
        cached = _program_cache.get(program_url or "")
        if (
            program_url
            and cached
            and time.monotonic() - cached[0] < _PROGRAM_TTL_SECONDS
        ):
            return selected["label"], program_url, cached[2]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"],
        )
        context = browser.new_context()
        context.route("**/*", _guard_catalog_request_sync)
        page = context.new_page()
        try:
            programs = cached_programs
            if programs is None:
                page.goto(
                    CATALOG_PROGRAM_INDEX,
                    wait_until="domcontentloaded",
                    timeout=20_000,
                )
                page.wait_for_selector(
                    'a[href*="preview_program.php"]', timeout=12_000
                )
                programs = page.locator(
                    'a[href*="preview_program.php"]'
                ).evaluate_all(
                    """els => els.map(a => ({
                        label: (a.textContent || '').replace(/\\s+/g, ' ').trim(),
                        href: a.getAttribute('href') || ''
                    })).filter(x => x.label && x.href)"""
                )
                programs = [
                    {"label": str(item["label"]), "href": str(item["href"])}
                    for item in programs
                    if _safe_program_url(str(item.get("href") or ""))
                ]
                _index_cache = (time.monotonic(), programs)

            selected = _select_program(question, programs)
            if selected is None:
                return None
            program_url = _safe_program_url(selected["href"])
            if not program_url:
                return None

            cached = _program_cache.get(program_url)
            if cached and time.monotonic() - cached[0] < _PROGRAM_TTL_SECONDS:
                return selected["label"], program_url, cached[2]

            page.goto(
                program_url,
                wait_until="domcontentloaded",
                timeout=20_000,
            )
            page.wait_for_selector("#acalog-page-title", timeout=20_000)
            heading = page.locator("#acalog-page-title").inner_text()
            content = page.locator("#acalog-page-title").evaluate(
                """el => {
                    let current = el;
                    for (let i = 0; current && i < 10; i += 1) {
                        const text = (current.innerText || '').trim();
                        if (text.length >= 800 && text.length <= 20000) return text;
                        current = current.parentElement;
                    }
                    return '';
                }"""
            )
            content = sanitize_evidence_text(str(content or ""), 16_000)
            if len(content) < 500:
                return None
            _program_cache[program_url] = (
                time.monotonic(),
                str(heading or selected["label"]),
                content,
            )
            return str(heading or selected["label"]), program_url, content
        finally:
            context.close()
            browser.close()


async def _render_catalog(question: str) -> tuple[str, str, str] | None:
    # Run sync Playwright in a worker thread. Uvicorn's Windows event loop cannot
    # spawn Playwright subprocesses via asyncio.create_subprocess_exec.
    async with _catalog_lock:
        return await asyncio.to_thread(_render_catalog_sync, question)


async def retrieve_catalog_degree_plan(
    question: str,
) -> tuple[list[RetrievedEvidence], str | None]:
    """Return one current-catalog curriculum evidence item for a named program."""
    try:
        rendered = await asyncio.wait_for(
            _render_catalog(question), timeout=_RENDER_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        return [], "catalog_render_timeout"
    except Exception as exc:
        return [], f"catalog_render_failed:{type(exc).__name__}"
    if not rendered:
        return [], "catalog_program_not_found"
    title, url, content = rendered
    evidence = RetrievedEvidence(
        evidence_id=f"ev-catalog-{abs(hash(url)) % 10_000_000}",
        title=f"{title} — {CATALOG_YEAR} Academic Catalog",
        url=url,
        text=(
            f"Official McNeese {CATALOG_YEAR} academic catalog curriculum.\n"
            f"{content}"
        ),
        source_id="SRC-011",
        source_name="McNeese Academic Catalog",
        source_tier="A",
        trust_level="official",
        category="degree_plan",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.98,
        metadata={
            "citation_label": f"Official {CATALOG_YEAR} catalog",
            "catalog_id": CATALOG_ID,
            "browser_rendered": True,
        },
    )
    return [evidence], None