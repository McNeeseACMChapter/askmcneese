"""Live web search service for McNeese content.

Searches mcneese.edu in real-time to find relevant pages for any query.
Uses DuckDuckGo search API to find pages, then fetches and extracts content.

"""

from __future__ import annotations

import os
import re
import asyncio
import concurrent.futures
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

from app.services.safe_errors import redact_sensitive

# Try to import duckduckgo-search library
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

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
    "mcneesecowboystore.com",
    "mcneesereslife.com",
    "mcneese.presence.io",
]

# Cloudflare challenge pages — not ordinary <noscript> "enable JavaScript" copy.
CLOUDFLARE_MARKERS = [
    "just a moment",
    "cf-browser-verification",
    "checking your browser",
    "cf-challenge",
    "cf-turnstile",
    "attention required! | cloudflare",
]


def _is_cloudflare_blocked(html: str) -> bool:
    """Check if the HTML is a Cloudflare challenge page."""
    if not html:
        return False
    head = html[:5000].lower()
    return any(marker in head for marker in CLOUDFLARE_MARKERS)


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
    "headings color", "brand hover color", "site main background",
    "headings font size", "text font sizes", "section spacing",
    "tokenwp", "tokenwp-button",
]
_THEME_SHELL_SELECTORS = (
    "script",
    "style",
    "svg",
    "iframe",
    "#headspin-tokenWP",
    ".tokenWP-modal",
    "[id^='tokenwp']",
    "[id*='tokenWP']",
    "[class*='tokenwp']",
    "[class*='tokenWP']",
)
_NAV_FRAGMENTS = [
    "newsparents", "faculty & staff", "communitylibrary", "1-800-622-3352",
]


def _is_garbage(text_lower: str) -> bool:
    return any(g in text_lower for g in _GARBAGE_PATTERNS)


def _looks_like_theme_shell(tag: Tag | None) -> bool:
    """Breakdance/Headspin puts a fake <main id='tokenwp-main'> ahead of the page."""
    if tag is None:
        return True
    ident = f"{tag.get('id') or ''} {' '.join(tag.get('class') or [])}".lower()
    if "tokenwp" in ident:
        return True
    text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
    if len(text) < 80:
        return True
    low = text.lower()
    if _is_garbage(low):
        return True
    token_hits = sum(
        1
        for marker in (
            "headings color",
            "brand hover",
            "global colors",
            "font size",
            "border radius",
            "section spacing",
            "site main background",
        )
        if marker in low
    )
    return token_hits >= 2 and len(text) < 2000


def _strip_non_content(soup: BeautifulSoup) -> None:
    for selector in _THEME_SHELL_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()
    for tag in soup(["header", "nav", "footer"]):
        tag.decompose()


def _content_root(soup: BeautifulSoup) -> Tag | None:
    for candidate in (
        soup.find("main"),
        soup.find("article"),
        soup.find(attrs={"role": "main"}),
    ):
        if candidate and not _looks_like_theme_shell(candidate):
            return candidate
    return soup.find("body")


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


_SECTION_STOP = {
    "about", "from", "have", "mcneese", "please", "that", "this", "university",
    "what", "when", "where", "which", "with", "your", "page", "official",
}
_GENERIC_QUERY_TOKENS = {
    "apply", "application", "applications", "doing", "exact", "find", "get",
    "getting", "give", "help", "make", "need", "needed", "needs", "process",
    "show", "step", "steps", "student", "students", "tell", "want",
}
_AUDIENCE_TOKENS = {
    "dual", "freshman", "freshmen", "graduate", "international", "online",
    "returning", "transfer", "visiting",
}
_ACTION_LINKS_APPENDIX = re.compile(
    r"(?:\n|^)Relevant official action links found on this page:.*\Z",
    re.IGNORECASE | re.DOTALL,
)


def _question_for_sections(question: str | None) -> str:
    text = (question or "").strip()
    if not text:
        return ""
    try:
        from app.services.campus_intelligence.route_validator import correct_campus_spelling

        text, _ = correct_campus_spelling(text)
    except Exception:
        pass
    return text


def _section_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(token) > 2 and token not in _SECTION_STOP
    }


def select_relevant_page_sections(
    content: str,
    question: str | None,
    *,
    limit: int = 4500,
) -> str:
    """Keep heading-sized blocks that overlap the question, not just the page head."""
    text = (content or "").strip()
    if not text:
        return text
    appendix = ""
    match = _ACTION_LINKS_APPENDIX.search(text)
    if match:
        appendix = match.group(0).strip()
        text = text[: match.start()].strip()
    if not text:
        return appendix[:limit] if appendix else ""
    if question:
        selected = _select_question_blocks(text, question, limit=limit)
        if not (selected or "").strip():
            selected = text[:limit]
    elif len(text) <= limit:
        selected = text
    else:
        selected = text[:limit]
    if appendix:
        remaining = limit - len(selected) if len(text) > limit else max(0, 16000 - len(selected))
        if remaining > 80:
            glue = "\n\n" if selected else ""
            selected = selected + glue + appendix[: max(0, remaining - len(glue))]
    return selected


def _select_question_blocks(text: str, question: str | None, *, limit: int) -> str:
    query = _section_tokens(_question_for_sections(question))
    if not query:
        return text[:limit]
    discriminators = query - _GENERIC_QUERY_TOKENS
    audience = query & _AUDIENCE_TOKENS
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    expanded: list[str] = []
    for block in blocks:
        if len(block) > 800 and (block.count("\n") > 8 or block.count("|") >= 3):
            expanded.extend(row.strip() for row in block.split("\n") if row.strip())
        else:
            expanded.append(block)
    blocks = expanded
    if not blocks:
        return text[:limit]
    block_tokens = [_section_tokens(block) for block in blocks]
    token_df: dict[str, int] = {}
    for tokens in block_tokens:
        for token in tokens:
            token_df[token] = token_df.get(token, 0) + 1
    scored: list[tuple[int, int, str]] = []
    for index, block in enumerate(blocks):
        overlap = query & block_tokens[index]
        exclusive = {token for token in overlap if token_df.get(token, 0) == 1}
        focused = overlap & discriminators
        audience_hit = overlap & audience
        score = len(overlap) + len(exclusive) * 6 + len(focused) * 10 + len(audience_hit) * 12
        first_tokens = _section_tokens(block.split("\n", 1)[0])
        if audience_hit & first_tokens:
            score += 10
        elif focused & first_tokens:
            score += 8
        elif query & first_tokens:
            score += 2
        asked = _question_for_sections(question).lower()
        if re.search(r"\bhours?\b", asked) and re.search(r"\bhours?\b", block, re.I):
            score += 12
        if re.search(r"\b(?:start|begin|first day)\b", asked) and re.search(
            r"\b(?:classes?\s+begin|instruction\s+begins?|semester\s+starts?|first\s+day)\b",
            block,
            re.I,
        ):
            score += 16
        if re.search(r"\b(?:location|located|where)\b", asked) and re.search(
            r"\b(?:located|location|address|library|building)\b",
            block,
            re.I,
        ):
            score += 10
        if re.search(r"\bpermit\b", asked) and re.search(r"\bpermit\b", block, re.I):
            score += 14
        if re.search(
            r"\b(?:step|deadline|hours?|apply|requirement|contact|fee|location|"
            r"process|transcript|admission|register|withdraw)\b",
            block,
            re.I,
        ):
            score += 1
        scored.append((score, index, block))
    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    if ranked[0][0] <= 0:
        return text[:limit]
    best_score = ranked[0][0]
    min_keep = max(2, best_score // 3)
    if audience:
        allowed = {
            index
            for index, tokens in enumerate(block_tokens)
            if tokens & audience
        }
        if allowed:
            expanded = set(allowed)
            for index in allowed:
                if index + 1 < len(blocks):
                    expanded.add(index + 1)
            ranked = [item for item in ranked if item[1] in expanded] or ranked
    score_by_index = {index: score for score, index, _ in scored}
    fitting = [
        (score, index, block)
        for score, index, block in ranked
        if score >= min_keep and len(block) <= limit
    ]
    keep: set[int] = set()
    used = 0
    for score, index, block in (fitting or ranked[:1]):
        extra = len(block) + (2 if keep else 0)
        if keep and used + extra > limit:
            continue
        if not keep and extra > limit:
            keep.add(index)
            break
        keep.add(index)
        used += extra
        neighbor = index + 1
        if (
            neighbor < len(blocks)
            and neighbor not in keep
            and score_by_index.get(neighbor, 0) > 0
        ):
            nxt = blocks[neighbor]
            extra_n = len(nxt) + 2
            if used + extra_n <= limit:
                keep.add(neighbor)
                used += extra_n
        if used >= limit:
            break
    selected_idxs = sorted(keep)
    while selected_idxs:
        joined = "\n\n".join(blocks[index] for index in selected_idxs)
        if len(joined) <= limit:
            return joined
        if len(selected_idxs) == 1:
            return joined[:limit]
        weakest = min(selected_idxs, key=lambda index: (score_by_index[index], -index))
        selected_idxs.remove(weakest)
    return text[:limit]


def _extract_page_action_links(
    root: Tag,
    url: str,
    question: str | None = None,
    *,
    limit: int = 30,
) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen_links: set[str] = set()
    link_cues = re.compile(
        r"(?:form|appeal|application|request|login|handshake|self-service|portal|"
        r"submit|report|complaint|download|apply|admission|requirement|deadline|"
        r"hours|contact|steps?|process|rate|housing|dining|scholarship|transcript|"
        r"calendar|withdraw|register|\.pdf(?:$|\?)|\.docx?(?:$|\?)|\.xlsx?(?:$|\?))",
        re.IGNORECASE,
    )
    query = _section_tokens(_question_for_sections(question))
    q = (question or "").lower()
    if re.search(r"\b(?:where|location|located|address|directions?)\b", q):
        query.update({"contact", "location", "directions", "visit"})
    if re.search(r"\b(?:contact|phone|telephone|email|hours?|open|close[sd]?|closing)\b", q):
        query.update({"contact", "hours", "location"})
    discriminators = query - _GENERIC_QUERY_TOKENS
    ranked: list[tuple[int, int, dict[str, str]]] = []
    for index, anchor in enumerate(root.find_all("a", href=True)):
        label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True)).strip()
        href = urljoin(url, str(anchor.get("href") or "").strip())
        if not href.startswith(("http://", "https://")):
            continue
        blob = f"{label} {href}"
        if not link_cues.search(blob):
            continue
        key = href.rstrip("/").lower()
        if key in seen_links:
            continue
        seen_links.add(key)
        tokens = _section_tokens(blob)
        score = len(query & tokens) + 4 * len(discriminators & tokens)
        ranked.append((score, index, {"label": label or "Official action link", "url": href}))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    for _, _, item in ranked[:limit]:
        links.append(item)
    return links


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
    links: list[dict[str, str]] = field(default_factory=list)


def is_mcneese_url(url: str) -> bool:
    """Check if URL is from an official McNeese / campus-live domain.

    Delegates to RCCS allowlist when available (adds SSRF/private-IP rejection)
    while preserving historical MCNEESE_DOMAINS behavior as fallback.
    """
    try:
        from app.services.rccs.allowlist import is_mcneese_or_official_url

        return is_mcneese_or_official_url(url)
    except Exception:
        # Authorization helpers failing must close the route, never widen it.
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


_MAX_PAGE_BYTES = max(64 * 1024, int(os.getenv("WEB_MAX_PAGE_BYTES", str(2 * 1024 * 1024))))
_MAX_REDIRECTS = 3
_ALLOWED_PAGE_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
_DEFAULT_FETCH_TIMEOUT = max(1.0, float(os.getenv("WEB_FETCH_TIMEOUT_SECONDS", "4.0")))


async def _fetch_http_html(url: str, timeout: float | None = None) -> tuple[str, str, str]:
    """Fetch bounded public HTML while validating DNS and every redirect hop."""
    from app.services.rccs.allowlist import validate_outbound_url

    current = await validate_outbound_url(url)
    request_timeout = timeout if timeout is not None else _DEFAULT_FETCH_TIMEOUT
    async with httpx.AsyncClient(
        timeout=request_timeout,
        follow_redirects=False,
        verify=shared_ssl_context(),
    ) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            current = await validate_outbound_url(current)
            async with client.stream("GET", current, headers=HEADERS) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        return current, "", "Redirect missing Location header"
                    current = urljoin(current, location)
                    continue
                if response.status_code != 200:
                    return current, "", f"HTTP {response.status_code}"
                content_type = response.headers.get("content-type", "").lower()
                if content_type and not any(
                    allowed in content_type for allowed in _ALLOWED_PAGE_TYPES
                ):
                    return current, "", "Unsupported page content type"
                payload = bytearray()
                async for chunk in response.aiter_bytes():
                    payload.extend(chunk)
                    if len(payload) > _MAX_PAGE_BYTES:
                        return current, "", "Page exceeded safe size limit"
                encoding = response.encoding or "utf-8"
                return current, bytes(payload).decode(encoding, errors="replace"), ""
        return current, "", "Too many redirects"


def _parse_fetched_html(url: str, html: str, question: str | None = None) -> FetchedPage:
    """Parse fetched HTML without blocking the asyncio event loop."""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    title_elem = soup.find("title")
    if title_elem:
        title = title_elem.get_text(strip=True)
        title = re.sub(r"\s*\|\s*McNeese.*$", "", title)
        title = re.sub(r"\s*-\s*McNeese.*$", "", title)

    # Capture intent-matched links before removing navigation. Department sites
    # commonly place "Contact Us" and "Hours" only in their local side menu.
    shell_links = _extract_page_action_links(soup, url, question, limit=40)
    _strip_non_content(soup)
    body = _content_root(soup)
    if not body:
        return FetchedPage(url=url, title=title, content="", success=False, error="No body found")

    body_links = _extract_page_action_links(body, url, question)
    links = []
    seen_link_urls: set[str] = set()
    for item in [*body_links, *shell_links]:
        key = str(item.get("url") or "").rstrip("/").lower()
        if not key or key in seen_link_urls:
            continue
        seen_link_urls.add(key)
        links.append(item)
        if len(links) >= 30:
            break
    content = _extract_structured_content(body)
    if len(content) < 50:
        return FetchedPage(
            url=url,
            title=title,
            content="",
            success=False,
            error="No meaningful content extracted",
        )
    content = select_relevant_page_sections(content, question, limit=16000)
    if links:
        action_lines = ["Relevant official action links found on this page:"]
        action_lines.extend(f"- {item['label']}: {item['url']}" for item in links)
        content = f"{content}\n\n" + "\n".join(action_lines)

    return FetchedPage(url=url, title=title, content=content, success=True, links=links)


async def fetch_page_content(
    url: str,
    *,
    timeout: float | None = None,
    question: str | None = None,
) -> FetchedPage:
    """
    Fetch and extract main content from a URL.
    Enforces public-address, redirect, content-type, and response-size limits.
    """
    html = ""
    
    try:
        final_url, html, fetch_error = await _fetch_http_html(url, timeout=timeout)
        if fetch_error:
            return FetchedPage(
                url=final_url or url,
                title="",
                content="",
                success=False,
                error=fetch_error,
            )
        url = final_url

        # Browser automation is intentionally not used here. It follows subresource
        # and navigation requests outside the DNS/redirect guard and adds seconds of
        # latency. Snippet/registry evidence remains available when a page is blocked.
        if _is_cloudflare_blocked(html):
            return FetchedPage(
                url=url,
                title="",
                content="",
                success=False,
                error="Page requires browser verification",
            )
        
        # BeautifulSoup parsing is CPU-bound and can take seconds for large or
        # malformed pages. Keep it off the event loop so turn deadlines remain
        # enforceable while page reads run concurrently.
        return await asyncio.to_thread(_parse_fetched_html, url, html, question)
        
    except Exception as e:
        return FetchedPage(
            url=url,
            title="",
            content="",
            success=False,
            error=redact_sensitive(e)
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
from app.services.http_runtime import shared_ssl_context
