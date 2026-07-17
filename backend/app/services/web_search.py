"""Live web search service for McNeese content.

Searches mcneese.edu in real-time to find relevant pages for any query.
Uses DuckDuckGo search API to find pages, then fetches and extracts content.

For Cloudflare-protected pages, falls back to headless browser fetching.
"""

from __future__ import annotations

import re
import asyncio
import concurrent.futures
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

# Try to import duckduckgo-search library
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Try to import Playwright for browser-based fetching (Cloudflare bypass)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# User agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# McNeese domains we trust
MCNEESE_DOMAINS = [
    "mcneese.edu",
    "www.mcneese.edu",
    "catalog.mcneese.edu",
    "schedule.mcneese.edu",
    "mcneesesports.com",
    "mcneese.presence.io",
]

# Cloudflare markers
CLOUDFLARE_MARKERS = ["Just a moment", "cf-browser-verification", "Checking your browser", "Enable JavaScript"]


def _is_cloudflare_blocked(html: str) -> bool:
    """Check if the HTML is a Cloudflare challenge page."""
    if not html:
        return False
    head = html[:5000].lower()
    return any(marker.lower() in head for marker in CLOUDFLARE_MARKERS)


def _fetch_with_browser(url: str) -> tuple[str, str]:
    """Fetch URL using headless browser (Cloudflare bypass)."""
    if not PLAYWRIGHT_AVAILABLE:
        return "", "Playwright not installed"
    
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for Cloudflare challenge to complete
                page.wait_for_timeout(5000)
                html = page.content()
                return html, ""
            finally:
                browser.close()
    except Exception as e:
        return "", str(e)


# ---------------------------------------------------------------------------
# Structure-preserving extraction helpers.
#
# Tables and lists carry the high-value facts (GPA tiers, dollar amounts, test
# cutoffs, deadlines). Flattening them with get_text() shreds the row/column
# association, which is a primary cause of shallow, hedge-heavy answers. We
# convert tables -> Markdown tables and <ul>/<ol> -> Markdown lists so the
# relationships survive into the LLM context.
# ---------------------------------------------------------------------------

def _cell_text(cell: Tag) -> str:
    text = cell.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip().replace("|", "\\|")


def _table_to_markdown(table: Tag) -> str:
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False) or tr.find_all(["th", "td"])
        values = [_cell_text(c) for c in cells]
        if any(v for v in values):
            rows.append(values)
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    if width < 2:
        return "\n".join(f"- {r[0]}" for r in rows if r and r[0].strip())
    norm = [r + [""] * (width - len(r)) for r in rows]
    header = norm[0]
    if not any(h.strip() for h in header):
        header = [f"Column {i + 1}" for i in range(width)]
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join(["---"] * width) + " |"]
    for row in norm[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _list_to_markdown(list_tag: Tag) -> str:
    ordered = list_tag.name == "ol"
    lines: list[str] = []
    idx = 1
    for li in list_tag.find_all("li", recursive=False):
        parts = []
        for child in li.children:
            if isinstance(child, Tag) and child.name in ("ul", "ol"):
                continue
            text = child.get_text(" ", strip=True) if isinstance(child, Tag) else str(child).strip()
            if text:
                parts.append(text)
        item = re.sub(r"\s+", " ", " ".join(parts)).strip()
        if item:
            lines.append(f"{idx}. {item}" if ordered else f"- {item}")
            idx += 1
        for nested in li.find_all(["ul", "ol"], recursive=False):
            for sub in _list_to_markdown(nested).splitlines():
                lines.append("  " + sub)
    return "\n".join(lines)


# Garbage patterns to skip (McNeese design tokens and navigation).
_GARBAGE_PATTERNS = [
    "font size", "heading size", "text size",
    "border radius", "spacing", "global colors",
    "section constrained", "section horizontal",
    "skip to content", "cookie policy", "privacy policy",
    "just a moment", "enable javascript", "please wait",
    "captcha", "verify you are human", "search for:",
]
_NAV_FRAGMENTS = [
    "newsparents", "faculty & staff", "communitylibrary", "1-800-622-3352",
]


def _is_garbage(text_lower: str) -> bool:
    return any(g in text_lower for g in _GARBAGE_PATTERNS)


def _is_nav_noise(text: str) -> bool:
    low = text.lower()
    if any(f in low for f in _NAV_FRAGMENTS):
        return True
    # Long runs of concatenated words with no spaces = squished nav menu.
    # Exempt emails/URLs — a valid address like "internationaloffice@mcneese.edu"
    # is a single long token and must NOT be treated as squished nav.
    real_words = [w for w in text.split() if "@" not in w and "://" not in w and "." not in w]
    longest_run = max((len(w) for w in real_words), default=0)
    return longest_run > 28


def _extract_structured_content(body: Tag) -> str:
    """Walk the body in document order, emitting Markdown for tables/lists and
    clean text for prose, while filtering McNeese nav/design-token noise.

    Tables and lists are emitted whole (never squished); their descendants are
    skipped so nothing is double-counted.
    """
    parts: list[str] = []

    for elem in body.find_all(
        ["table", "ul", "ol", "p", "h1", "h2", "h3", "h4", "section", "div"]
    ):
        # Everything inside a table/list is emitted by its container.
        if elem.find_parent(["table", "ul", "ol"]):
            continue

        name = elem.name

        if name == "table":
            block = _table_to_markdown(elem)
            if block and not _is_garbage(block.lower()):
                parts.append(block)
            continue

        if name in ("ul", "ol"):
            block = _list_to_markdown(elem)
            if not block:
                continue
            low = block.lower()
            if _is_garbage(low) or _is_nav_noise(block):
                continue
            if len(block) < 8:
                continue
            parts.append(block)
            continue

        # Prose: only emit leaf-ish sections/divs so we don't re-emit text that
        # is already captured by inner <p>/<h*> tags.
        if name in ("section", "div") and elem.find(
            ["p", "table", "ul", "ol", "h1", "h2", "h3", "h4", "section", "div"]
        ):
            continue

        text = re.sub(r"\s+", " ", elem.get_text(" ", strip=True)).strip()
        if not text or len(text) < 25:
            continue
        low = text.lower()
        if _is_garbage(low) or _is_nav_noise(text):
            continue
        if text.count("|") > 3:  # pipe-heavy prose = nav bar
            continue
        parts.append(text)

    # Deduplicate (nesting produces repeats); key on the first 100 chars.
    seen: set[str] = set()
    unique: list[str] = []
    for part in parts:
        key = part[:100]
        if key not in seen:
            seen.add(key)
            unique.append(part)
    return "\n\n".join(unique)


@dataclass
class SearchResult:
    """A single search result."""
    url: str
    title: str
    snippet: str
    domain: str


@dataclass
class FetchedPage:
    """Content fetched from a URL."""
    url: str
    title: str
    content: str
    success: bool
    error: Optional[str] = None


def is_mcneese_url(url: str) -> bool:
    """Check if URL is from an official McNeese / campus-live domain.

    Delegates to RCCS allowlist when available (adds SSRF/private-IP rejection)
    while preserving historical MCNEESE_DOMAINS behavior as fallback.
    """
    try:
        from app.services.rccs.allowlist import is_mcneese_or_official_url

        return is_mcneese_or_official_url(url)
    except Exception:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(d in domain for d in MCNEESE_DOMAINS)
        except Exception:
            return False


def _ddgs_search_sync(query: str, max_results: int) -> list[dict]:
    """Run DuckDuckGo search synchronously (for thread pool)."""
    if not DDGS_AVAILABLE:
        return []
    
    try:
        # Don't use site: operator - it doesn't work with DDGS
        # Instead, include "mcneese" in query and filter results later
        search_query = f"mcneese {query}"
        
        with DDGS() as ddgs:
            results = list(ddgs.text(
                search_query,
                max_results=max_results * 2,  # Get more results to filter
                region="us-en"
            ))
            return results
    except Exception as e:
        print(f"DDGS search error: {e}")
        return []


async def search_duckduckgo(query: str, max_results: int = 8) -> list[SearchResult]:
    """
    Search DuckDuckGo for McNeese-related pages using the API library.
    """
    if not DDGS_AVAILABLE:
        print("duckduckgo-search library not available")
        return []
    
    # Run sync DDGS in thread pool
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        raw_results = await loop.run_in_executor(
            pool, _ddgs_search_sync, query, max_results + 3
        )
    
    results: list[SearchResult] = []
    for r in raw_results:
        url = r.get("href", "")
        if is_mcneese_url(url):
            parsed = urlparse(url)
            results.append(SearchResult(
                url=url,
                title=r.get("title", ""),
                snippet=r.get("body", ""),
                domain=parsed.netloc,
            ))
        if len(results) >= max_results:
            break
    
    return results


async def fetch_page_content(url: str) -> FetchedPage:
    """
    Fetch and extract main content from a URL.
    Uses headless browser as fallback for Cloudflare-protected pages.
    """
    html = ""
    
    try:
        # Try regular HTTP first
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)
            
            if response.status_code != 200:
                return FetchedPage(
                    url=url,
                    title="",
                    content="",
                    success=False,
                    error=f"HTTP {response.status_code}"
                )
            
            html = response.text
        
        # Check if Cloudflare blocked us
        if _is_cloudflare_blocked(html):
            if PLAYWRIGHT_AVAILABLE:
                # Try browser-based fetch in thread pool
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    browser_html, error = await loop.run_in_executor(
                        pool, _fetch_with_browser, url
                    )
                    if browser_html and not _is_cloudflare_blocked(browser_html):
                        html = browser_html
                    elif error:
                        return FetchedPage(
                            url=url,
                            title="",
                            content="",
                            success=False,
                            error=f"Cloudflare block, browser fetch failed: {error}"
                        )
            else:
                return FetchedPage(
                    url=url,
                    title="",
                    content="",
                    success=False,
                    error="Page blocked by Cloudflare (install playwright for bypass)"
                )
        
        # Parse the HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # Get title
        title = ""
        title_elem = soup.find("title")
        if title_elem:
            title = title_elem.get_text(strip=True)
            # Clean up common suffixes
            title = re.sub(r"\s*\|\s*McNeese.*$", "", title)
            title = re.sub(r"\s*-\s*McNeese.*$", "", title)
        
        # Remove script, style, and other non-content elements
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()
        
        # McNeese-specific: their <main> contains CSS token config, NOT content.
        # The actual content is in section.bde-section-* elements in body, so we
        # use body directly and let the structure-aware extractor filter garbage
        # while preserving tables and lists as Markdown.
        body = soup.find("body")
        if not body:
            return FetchedPage(
                url=url,
                title=title,
                content="",
                success=False,
                error="No body found"
            )

        content = _extract_structured_content(body)
        
        if len(content) < 50:
            return FetchedPage(
                url=url,
                title=title,
                content="",
                success=False,
                error="No meaningful content extracted"
            )
        
        # Truncate if too long
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        return FetchedPage(
            url=url,
            title=title,
            content=content,
            success=True
        )
        
    except Exception as e:
        return FetchedPage(
            url=url,
            title="",
            content="",
            success=False,
            error=str(e)
        )


async def search_and_fetch(query: str, max_pages: int = 5) -> list[FetchedPage]:
    """
    Find relevant McNeese pages and fetch their content.

    Retrieval strategy (reliable-first):
    1. Route the query to approved pages in the curated source registry
       (fast, reliable, always available).
    2. Supplement with live DuckDuckGo search for broader coverage
       (best-effort; may be rate-limited).
    3. Fetch all candidate URLs in parallel and return pages with real content.
    """
    from app.services.source_registry import match_sources
    from app.services.query_expansion import expand_query
    from app.services.rerank import rerank_texts

    urls_to_fetch: list[str] = []
    seen_urls: set[str] = set()

    def _add_url(u: str) -> None:
        # Normalize trailing slash for dedup
        key = u.rstrip("/").lower()
        if key not in seen_urls:
            seen_urls.add(key)
            urls_to_fetch.append(u)

    # Step 1: Expand the query so persona-specific pages (new freshman vs.
    # continuing vs. graduate/international) all get routed, then map each
    # sub-query to approved registry sources.
    subqueries = expand_query(query) or [query]
    for sq in subqueries:
        for src in match_sources(sq, max_sources=3):
            _add_url(src.url)

    # Step 2: Live search supplement (best-effort)
    try:
        search_results = await search_duckduckgo(query, max_results=max_pages)
        for r in search_results:
            _add_url(r.url)
    except Exception as e:
        print(f"Web search supplement failed: {e}")

    if not urls_to_fetch:
        return []

    # Step 3: Fetch candidate pages in parallel. Pull a wider net than
    # max_pages so reranking has real choices to make.
    candidates = urls_to_fetch[: max_pages + 4]
    tasks = [fetch_page_content(url) for url in candidates]
    fetched_pages = await asyncio.gather(*tasks)

    # Keep only successful fetches with real content
    successful_pages = [p for p in fetched_pages if p.success and p.content]
    if not successful_pages:
        return []

    # Step 4: Rerank fetched pages against the ORIGINAL question and keep the
    # most relevant, instead of trusting registry/DDG ordering.
    ranked = rerank_texts(
        query,
        [f"{p.title}\n{p.content}" for p in successful_pages],
    )
    ordered = [successful_pages[idx] for idx, _ in ranked]
    return ordered[:max_pages]


def pages_to_context(pages: list[FetchedPage]) -> tuple[str, list[dict]]:
    """
    Convert fetched pages to context string and source list.
    
    Returns:
        (context_string, sources_list)
    """
    if not pages:
        return "", []
    
    context_parts = []
    sources = []
    
    for i, page in enumerate(pages, 1):
        context_parts.append(f"[Source {i}: {page.title}]\nURL: {page.url}\n{page.content}")
        sources.append({
            "id": f"src-{i}",
            "title": page.title or f"McNeese Page {i}",
            "url": page.url,
            "snippet": page.content[:200] + "..." if len(page.content) > 200 else page.content,
        })
    
    context = "\n\n---\n\n".join(context_parts)
    return context, sources
