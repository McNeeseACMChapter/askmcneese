"""Live web research service for AskMcNeese.

Discovery is registry-first, then supplemented by configured high-quality search
providers (Perplexity first, Google optional). Candidate pages are still opened
and read directly so search-engine snippets or generated summaries never become
the final evidence by themselves.

Important design rules:
- Trust comes from the central RCCS/source-registry policy, not a hard-coded
  handful of domains in this file.
- Question terms receive generic relevance treatment; there are no special
  boosts for parking, hours, location, permits, or specific audiences.
- This module does not invent persona/intent expansions. It searches the user's
  original question. Clarifying questions belong in the conversation/compiler
  layer, where the system can actually ask the user.
- Pages are read over bounded HTTP by default. Chromium is opt-in because a
  headed browser does not fit Render's 512MB web plan.
"""

from __future__ import annotations

import asyncio
import math
import os
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.services.http_runtime import shared_ssl_context
from app.services.safe_errors import redact_sensitive

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
    "newsparents", "faculty & staff", "communitylibrary",
]
_CONTACT_CARD_RE = re.compile(
    r"\b(?:hours?|monday|tuesday|wednesday|thursday|friday|phone:|"
    r"mailing address|337-\d{3}|@mcneese\.edu|a\.m\.|p\.m\.)\b",
    re.I,
)


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


def _visible_text(elem: Tag) -> str:
    """Keep line breaks from <br> so hours/address cards stay parseable."""
    parts: list[str] = []
    for child in elem.descendants:
        if isinstance(child, Tag):
            if child.name == "br":
                parts.append("\n")
            continue
        text = str(child)
        if text.strip():
            parts.append(text)
        elif "\n" in text:
            parts.append("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in "".join(parts).splitlines()]
    return "\n".join(line for line in lines if line)


def _harvest_contact_cards(soup: BeautifulSoup) -> list[str]:
    """Keep hours/phone/address widgets even when they live in the page chrome."""
    cards: list[str] = []
    seen: set[str] = set()
    for node in soup.select(".bde-icon-list__text, .bde-rich-text, p, li"):
        text = _visible_text(node)
        if not text or len(text) < 12 or len(text) > 900:
            continue
        if not _CONTACT_CARD_RE.search(text):
            continue
        if _is_garbage(text.lower()):
            continue
        key = re.sub(r"\s+", " ", text).lower()[:160]
        if key in seen:
            continue
        seen.add(key)
        cards.append(text)
        if len(cards) >= 8:
            break
    return cards


def _is_nav_noise(text: str) -> bool:
    # Campus contact cards include the university 800-number. That is not nav.
    if _CONTACT_CARD_RE.search(text or ""):
        return False
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

        text = _visible_text(elem)
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
_ACTION_LINKS_APPENDIX = re.compile(
    r"(?:\n|^)Relevant official action links found on this page:.*\Z",
    re.IGNORECASE | re.DOTALL,
)


def _question_for_sections(question: str | None) -> str:
    """Normalize spelling only; do not infer or expand user intent here."""
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


def _generic_overlap_score(
    query_tokens: set[str],
    block_tokens: set[str],
    token_df: dict[str, int],
    total_blocks: int,
) -> float:
    """Score lexical overlap without topic-specific or audience-specific bonuses.

    Every query term follows the same formula. Terms that occur in fewer page
    blocks naturally carry more information (IDF-like weighting), but no word
    such as "permit", "hours", "location", or "international" is privileged by
    a hand-written rule.
    """
    overlap = query_tokens & block_tokens
    if not overlap:
        return 0.0
    return sum(
        1.0 + math.log((total_blocks + 1) / (token_df.get(token, 0) + 1))
        for token in overlap
    )


def select_relevant_page_sections(
    content: str,
    question: str | None,
    *,
    limit: int = 4500,
) -> str:
    """Keep page blocks relevant to the literal user question."""
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

    total_blocks = len(blocks)
    scored: list[tuple[float, int, str]] = []
    for index, block in enumerate(blocks):
        score = _generic_overlap_score(query, block_tokens[index], token_df, total_blocks)

        # A heading match is useful structurally, but the same multiplier applies
        # to every term. No subject receives special treatment.
        first_tokens = _section_tokens(block.split("\n", 1)[0])
        heading_score = _generic_overlap_score(query, first_tokens, token_df, total_blocks)
        score += 0.5 * heading_score
        scored.append((score, index, block))

    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    if not ranked or ranked[0][0] <= 0:
        return text[:limit]

    best_score = ranked[0][0]
    min_keep = best_score * 0.35
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

        # Preserve one adjacent block when it overlaps the question, or when the
        # kept block is a heading and the next block is its body. That is a
        # layout rule, not a topic-specific boost.
        heading_like = "\n" not in block and len(block) <= 160
        neighbor = index + 1
        if (
            neighbor < len(blocks)
            and neighbor not in keep
            and (score_by_index.get(neighbor, 0) > 0 or heading_like)
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
    """Find potentially useful action/document links with generic relevance.

    The cue list determines whether a link looks actionable; relevance ranking is
    based only on literal query overlap. There are no special query rewrites for
    location, hours, parking, permits, applications, or any other topic.
    """
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
    ranked: list[tuple[float, int, dict[str, str]]] = []

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
        overlap = query & tokens
        # Equal lexical treatment: each overlapping query token contributes 1.
        # A tiny baseline keeps clearly actionable links available even when the
        # user's wording differs from the link label.
        score = float(len(overlap)) + 0.01
        ranked.append((score, index, {"label": label or "Official action link", "url": href}))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    for _, _, item in ranked[:limit]:
        links.append(item)
    return links


@dataclass
class SearchResult:
    """A search-provider result that still must pass project trust policy."""

    url: str
    title: str
    snippet: str
    domain: str
    provider: str = ""


@dataclass
class FetchedPage:
    """Content fetched from a trusted URL."""

    url: str
    title: str
    content: str
    success: bool
    error: Optional[str] = None
    links: list[dict[str, str]] = field(default_factory=list)
    fetch_method: str = ""


def is_mcneese_url(url: str) -> bool:
    """Compatibility name: ask the central policy whether a URL is trusted.

    There is intentionally no local eight-domain list anymore. Official and
    companion coverage belongs in the RCCS/source-registry policy so adding a
    new approved campus or companion source does not require editing this file.
    """
    try:
        from app.services.rccs.allowlist import is_mcneese_or_official_url

        return bool(is_mcneese_or_official_url(url))
    except Exception:
        # A broken trust policy must fail closed; web search must never widen
        # itself to arbitrary public URLs merely because the allowlist failed.
        return False


def _provider_query(query: str) -> str:
    """Add university context without changing the user's intent."""
    cleaned = re.sub(r"\s+", " ", (query or "").strip())
    if "mcneese" in cleaned.lower():
        return cleaned
    return f"McNeese State University {cleaned}".strip()


async def search_perplexity(query: str, max_results: int = 8) -> list[SearchResult]:
    """Use Perplexity Search API for ranked live-web discovery.

    This function uses Perplexity for discovery only. AskMcNeese still opens the
    returned original pages and extracts evidence itself; an LLM-generated
    Perplexity summary is not treated as source evidence.
    """
    api_key = (os.getenv("PERPLEXITY_API_KEY") or "").strip()
    if not api_key:
        return []

    payload = {
        "query": _provider_query(query),
        "max_results": max(1, min(max_results * 2, 20)),
        "max_tokens_per_page": max(256, int(os.getenv("PERPLEXITY_MAX_TOKENS_PER_PAGE", "1024"))),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        async with httpx.AsyncClient(
            timeout=max(2.0, float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "8.0"))),
            verify=shared_ssl_context(),
        ) as client:
            response = await client.post(
                "https://api.perplexity.ai/search",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        print(f"Perplexity search failed: {redact_sensitive(exc)}")
        return []

    results: list[SearchResult] = []
    for item in data.get("results", []) or []:
        url = str(item.get("url") or "").strip()
        if not url or not is_mcneese_url(url):
            continue
        results.append(
            SearchResult(
                url=url,
                title=str(item.get("title") or "").strip(),
                snippet=str(item.get("snippet") or "").strip(),
                domain=urlparse(url).netloc,
                provider="perplexity",
            )
        )
        if len(results) >= max_results:
            break
    return results


async def search_google(query: str, max_results: int = 8) -> list[SearchResult]:
    """Use Google Programmable Search when an existing CSE is configured.

    GOOGLE_SEARCH_API_KEY (or GOOGLE_API_KEY) and GOOGLE_SEARCH_CX (or
    GOOGLE_CSE_ID) are required. Google has announced migration/deprecation
    constraints for this API, so it is intentionally optional rather than the
    only discovery path.
    """
    api_key = (os.getenv("GOOGLE_SEARCH_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    cx = (os.getenv("GOOGLE_SEARCH_CX") or os.getenv("GOOGLE_CSE_ID") or "").strip()
    if not api_key or not cx:
        return []

    params = {
        "key": api_key,
        "cx": cx,
        "q": _provider_query(query),
        "num": max(1, min(max_results * 2, 10)),
        "safe": "active",
        "gl": "us",
    }
    try:
        async with httpx.AsyncClient(
            timeout=max(2.0, float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "8.0"))),
            verify=shared_ssl_context(),
        ) as client:
            response = await client.get(
                "https://customsearch.googleapis.com/customsearch/v1",
                params=params,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        print(f"Google search failed: {redact_sensitive(exc)}")
        return []

    results: list[SearchResult] = []
    for item in data.get("items", []) or []:
        url = str(item.get("link") or "").strip()
        if not url or not is_mcneese_url(url):
            continue
        results.append(
            SearchResult(
                url=url,
                title=str(item.get("title") or "").strip(),
                snippet=str(item.get("snippet") or "").strip(),
                domain=urlparse(url).netloc,
                provider="google",
            )
        )
        if len(results) >= max_results:
            break
    return results


_SEARCH_PROVIDERS = {
    "perplexity": search_perplexity,
    "google": search_google,
}


async def search_live_web(query: str, max_results: int = 8) -> list[SearchResult]:
    """Merge configured live-search providers without guessing user intent."""
    requested = [
        p.strip().lower()
        for p in os.getenv("WEB_SEARCH_PROVIDER_ORDER", "perplexity,google").split(",")
        if p.strip()
    ]
    providers = [p for p in requested if p in _SEARCH_PROVIDERS]
    if not providers:
        return []

    # Run configured providers concurrently. Provider order only breaks ties when
    # both discover the same general material; final page ranking is still done
    # against the original user question after the pages are actually read.
    calls = [_SEARCH_PROVIDERS[name](query, max_results=max_results) for name in providers]
    batches = await asyncio.gather(*calls, return_exceptions=True)

    merged: list[SearchResult] = []
    seen: set[str] = set()
    for provider, batch in zip(providers, batches):
        if isinstance(batch, Exception):
            print(f"{provider} search failed: {redact_sensitive(batch)}")
            continue
        for item in batch:
            key = item.url.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= max_results:
                return merged
    return merged


_MAX_PAGE_BYTES = max(64 * 1024, int(os.getenv("WEB_MAX_PAGE_BYTES", str(2 * 1024 * 1024))))
_MAX_REDIRECTS = 3
_ALLOWED_PAGE_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
_DEFAULT_FETCH_TIMEOUT = max(1.0, float(os.getenv("WEB_FETCH_TIMEOUT_SECONDS", "4.0")))
_BROWSER_MODE = os.getenv("WEB_BROWSER_MODE", "off").strip().lower()
_DEFAULT_BROWSER_TIMEOUT = max(2.0, float(os.getenv("WEB_BROWSER_TIMEOUT_SECONDS", "15.0")))
_BROWSER_SETTLE_MS = max(0, int(os.getenv("WEB_BROWSER_SETTLE_MS", "1200")))
_CLOUDFLARE_WAIT_MS = max(0, int(os.getenv("WEB_CLOUDFLARE_WAIT_MS", "5000")))


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



async def _fetch_browser_html(url: str, timeout: float | None = None) -> tuple[str, str, str]:
    """Render a trusted public page in Chromium and return the final HTML.

    Browser requests are guarded with the same public-URL validator used by the
    HTTP path. The main navigation must also remain inside the project's trusted
    source policy after redirects.
    """
    from app.services.rccs.allowlist import validate_outbound_url

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return url, "", "Playwright is not installed"

    try:
        current = await validate_outbound_url(url)
    except Exception as exc:
        return url, "", f"Unsafe browser URL: {redact_sensitive(exc)}"

    request_timeout = timeout if timeout is not None else _DEFAULT_BROWSER_TIMEOUT
    browser = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                locale="en-US",
                java_script_enabled=True,
                ignore_https_errors=False,
            )
            page = await context.new_page()

            async def guard_request(route, request) -> None:
                request_url = request.url
                parsed = urlparse(request_url)
                if parsed.scheme in {"data", "blob", "about"}:
                    await route.continue_()
                    return
                if parsed.scheme not in {"http", "https"}:
                    await route.abort()
                    return
                try:
                    # Validate every network request. This keeps browser rendering
                    # from becoming an SSRF escape hatch through page subresources.
                    await validate_outbound_url(request_url)
                except Exception:
                    await route.abort()
                    return
                await route.continue_()

            await page.route("**/*", guard_request)
            await page.goto(
                current,
                wait_until="domcontentloaded",
                timeout=int(request_timeout * 1000),
            )
            if _BROWSER_SETTLE_MS:
                await page.wait_for_timeout(_BROWSER_SETTLE_MS)

            final_url = page.url
            try:
                final_url = await validate_outbound_url(final_url)
            except Exception as exc:
                return current, "", f"Unsafe browser redirect: {redact_sensitive(exc)}"
            if not is_mcneese_url(final_url):
                return final_url, "", "Browser redirected outside trusted source policy"

            html = await page.content()
            if _is_cloudflare_blocked(html) and _CLOUDFLARE_WAIT_MS:
                # Give legitimate browser verification a short chance to resolve.
                # We do not bypass CAPTCHAs or defeat access controls.
                await page.wait_for_timeout(_CLOUDFLARE_WAIT_MS)
                html = await page.content()

            if _is_cloudflare_blocked(html):
                return final_url, "", "Browser verification challenge did not resolve"
            return final_url, html, ""
    except Exception as exc:
        return current, "", f"Browser fetch failed: {redact_sensitive(exc)}"
    finally:
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass


async def _parse_html_result(
    url: str,
    html: str,
    question: str | None,
    *,
    fetch_method: str,
) -> FetchedPage:
    parsed = await asyncio.to_thread(_parse_fetched_html, url, html, question)
    parsed.fetch_method = fetch_method
    return parsed

def _parse_fetched_html(url: str, html: str, question: str | None = None) -> FetchedPage:
    """Parse fetched HTML without blocking the asyncio event loop."""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    title_elem = soup.find("title")
    if title_elem:
        title = title_elem.get_text(strip=True)
        title = re.sub(r"\s*\|\s*McNeese.*$", "", title)
        title = re.sub(r"\s*-\s*McNeese.*$", "", title)

    # Capture query-relevant action links before removing navigation. Department sites
    # may place useful local links only in their side menu.
    shell_links = _extract_page_action_links(soup, url, question, limit=40)
    contact_cards = _harvest_contact_cards(soup)
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
    if len(content) < 50 and not contact_cards:
        return FetchedPage(
            url=url,
            title=title,
            content="",
            success=False,
            error="No meaningful content extracted",
        )
    content = select_relevant_page_sections(content, question, limit=16000)
    if contact_cards:
        extra = "\n\n".join(contact_cards)
        if extra not in (content or ""):
            content = extra + ("\n\n" + content if content else "")
    if not (content or "").strip():
        return FetchedPage(
            url=url,
            title=title,
            content="",
            success=False,
            error="No meaningful content extracted",
        )
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
    """Open and extract a trusted page. HTTP is the default on small hosts.

    WEB_BROWSER_MODE controls behavior:
      - off       (default): bounded HTTP only. Safe for Render's 512MB plan.
      - fallback: use bounded HTTP first, then Chromium if the page needs it.
      - always:   render every candidate in Chromium first; HTTP is a fallback.

    Even in browser mode, URL trust/SSRF validation remains mandatory.
    """
    mode = _BROWSER_MODE if _BROWSER_MODE in {"always", "fallback", "off"} else "off"
    errors: list[str] = []

    async def browser_attempt() -> FetchedPage | None:
        final_url, html, error = await _fetch_browser_html(url, timeout=timeout)
        if error:
            errors.append(error)
            return None
        result = await _parse_html_result(
            final_url,
            html,
            question,
            fetch_method="browser",
        )
        if result.success and result.content:
            return result
        errors.append(result.error or "Browser rendered page but extraction was empty")
        return None

    async def http_attempt() -> FetchedPage | None:
        final_url, html, error = await _fetch_http_html(url, timeout=timeout)
        if error:
            errors.append(error)
            return None
        if _is_cloudflare_blocked(html):
            errors.append("HTTP response requires browser verification")
            return None
        result = await _parse_html_result(
            final_url,
            html,
            question,
            fetch_method="http",
        )
        if result.success and result.content:
            return result
        errors.append(result.error or "HTTP page extraction was empty")
        return None

    try:
        if mode == "always":
            result = await browser_attempt()
            if result is not None:
                return result
            result = await http_attempt()
            if result is not None:
                return result
        elif mode == "fallback":
            result = await http_attempt()
            if result is not None:
                return result
            result = await browser_attempt()
            if result is not None:
                return result
        else:
            result = await http_attempt()
            if result is not None:
                return result
    except Exception as exc:
        errors.append(str(redact_sensitive(exc)))

    return FetchedPage(
        url=url,
        title="",
        content="",
        success=False,
        error="; ".join(dict.fromkeys(error for error in errors if error)) or "Unable to read page",
        fetch_method="failed",
    )


async def search_and_fetch(query: str, max_pages: int = 5) -> list[FetchedPage]:
    """Find trusted candidate pages, read them, then rerank real page content.

    Retrieval strategy:
    1. Match the ORIGINAL user question against the approved source registry.
       No persona expansion or inferred audience is introduced here.
    2. Supplement with configured live search providers (Perplexity first,
       Google optional by default).
    3. Open candidate pages. Browser rendering is opt-in via WEB_BROWSER_MODE.
    4. Rerank the content actually read from those pages against the ORIGINAL
       user question.

    Clarifying questions are intentionally not invented in this module. If the
    question is ambiguous, the future conversation/compiler layer should ask the
    user before this retrieval function is called with a guessed intent.
    """
    from app.services.source_registry import match_sources
    from app.services.rerank import rerank_texts

    query = re.sub(r"\s+", " ", (query or "").strip())
    if not query:
        return []

    urls_to_fetch: list[str] = []
    seen_urls: set[str] = set()

    def _add_url(candidate: str) -> None:
        candidate = (candidate or "").strip()
        if not candidate or not is_mcneese_url(candidate):
            return
        key = candidate.rstrip("/").lower()
        if key not in seen_urls:
            seen_urls.add(key)
            urls_to_fetch.append(candidate)

    # Step 1: literal registry match only. Use a wider candidate set instead of
    # inventing persona-specific subqueries.
    try:
        for src in match_sources(query, max_sources=max(6, max_pages + 3)):
            _add_url(src.url)
    except Exception as exc:
        print(f"Registry source matching failed: {redact_sensitive(exc)}")

    # Step 2: high-quality live discovery. Results still must pass central trust
    # policy before they can become candidate URLs.
    try:
        live_results = await search_live_web(query, max_results=max(max_pages + 4, 8))
        for result in live_results:
            _add_url(result.url)
    except Exception as exc:
        print(f"Live web search supplement failed: {redact_sensitive(exc)}")

    if not urls_to_fetch:
        return []

    # Step 3: pull a wider candidate set so browser/page-level reranking has real
    # choices. Fetch concurrently; each page individually enforces URL safety.
    candidates = urls_to_fetch[: max_pages + 8]
    fetched_pages = await asyncio.gather(
        *(fetch_page_content(candidate, question=query) for candidate in candidates),
        return_exceptions=True,
    )

    successful_pages: list[FetchedPage] = []
    for page in fetched_pages:
        if isinstance(page, Exception):
            print(f"Candidate page read failed: {redact_sensitive(page)}")
            continue
        if page.success and page.content:
            successful_pages.append(page)
    if not successful_pages:
        return []

    # Step 4: provider order is not final authority. Rank what the pages actually
    # said against exactly what the user asked.
    ranked = rerank_texts(
        query,
        [f"{page.title}\n{page.content}" for page in successful_pages],
    )
    ordered = [successful_pages[index] for index, _ in ranked]
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
