"""Page-open agent: after SERP/Sonar returns URLs, open selected pages and scrape text.

Uses existing ``fetch_page_content`` (httpx + optional Playwright). Only opens URLs
that match the classification-driven browse target (or open-web allow policy).
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable
from urllib.parse import urlparse

from app.services.rccs.allowlist import (
    is_mcneese_or_official_url,
    is_safe_public_url_literal,
    normalize_url,
)
from app.services.rccs.browse_plan import BrowseTarget, host_blocked_for_open, url_in_browse_domains
from app.services.rccs.evidence import sanitize_evidence_text
from app.services.rccs.models import RetrievedEvidence, utcnow

OnOpenActivity = Callable[[str, dict[str, Any] | None], Awaitable[None]] | None


def select_urls_to_open(
    urls: list[str],
    target: BrowseTarget,
    *,
    limit: int | None = None,
) -> list[str]:
    """Pick which SERP/Sonar links the agent should open."""
    if not target.allow_open_web or target.max_pages_to_open <= 0:
        return []

    cap = limit if limit is not None else target.max_pages_to_open
    out: list[str] = []
    seen: set[str] = set()

    for raw in urls:
        nu = normalize_url(raw) or (raw or "").strip()
        if not nu or not is_safe_public_url_literal(nu):
            continue
        key = nu.rstrip("/").lower()
        if key in seen:
            continue
        host = (urlparse(nu).netloc or "").lower()
        if host_blocked_for_open(host):
            continue

        # Prefer classified domains; in open-web mode also allow other https hosts
        # that appeared in the SERP (system already decided to search broadly).
        in_scope = url_in_browse_domains(nu, target.domains)
        if not in_scope and not target.allow_open_web:
            continue
        if not in_scope and target.allow_open_web:
            # Open-web: allow non-McNeese SERP hits the classifier routed us toward,
            # but still skip obvious junk hosts.
            if urlparse(nu).scheme not in {"http", "https"}:
                continue

        seen.add(key)
        out.append(nu)
        if len(out) >= cap:
            break
    return out


async def open_and_scrape_urls(
    urls: list[str],
    target: BrowseTarget,
    *,
    on_activity: OnOpenActivity = None,
    question: str | None = None,
    fetch_timeout: float = 2.2,
) -> list[RetrievedEvidence]:
    """Fetch full page content for selected URLs."""
    to_open = select_urls_to_open(urls, target)
    if not to_open:
        return []

    from app.services.web_search import fetch_page_content, select_relevant_page_sections

    evidence: list[RetrievedEvidence] = []

    async def _one(i: int, url: str) -> RetrievedEvidence | None:
        host = (urlparse(url).netloc or "").removeprefix("www.")
        if on_activity:
            await on_activity(
                f"Opening {host} to read the full page…",
                {"url": url, "skill": "page_open", "host": host},
            )
        try:
            page = await fetch_page_content(
                url,
                timeout=fetch_timeout,
                question=question,
            )
        except Exception as e:
            if on_activity:
                await on_activity(
                    f"Could not open {host}",
                    {"url": url, "error": str(e)[:120]},
                )
            return None
        if not getattr(page, "success", False) or not (getattr(page, "content", "") or "").strip():
            if on_activity:
                await on_activity(
                    f"No readable content from {host}",
                    {"url": url},
                )
            return None

        official = is_mcneese_or_official_url(url)
        is_rmp = "ratemyprofessors.com" in host
        is_linkedin = "linkedin.com" in host

        if official:
            tier, trust, channel = "B", "campus_live", "official_live"
            source_id, label = "PAGE_OPEN_OFFICIAL", "Opened campus page"
            category = "official_live"
        elif is_rmp:
            tier, trust, channel = "C", "student_rating", "companion"
            source_id, label = "SRC-C-RMP-001", "Opened Rate My Professors page"
            category = "student_rating"
        elif is_linkedin:
            tier, trust, channel = "C", "social", "companion"
            source_id, label = "SRC-C-LINKEDIN-001", "Opened LinkedIn profile page"
            category = "social"
        else:
            tier, trust, channel = "C", "web_live", "web_live"
            source_id, label = "PAGE_OPEN_WEB", "Opened web page"
            category = "web_live"

        title = (getattr(page, "title", None) or host or "Web page")[:180]
        body = sanitize_evidence_text(
            select_relevant_page_sections(page.content or "", question, limit=4500)
        )
        links = list(getattr(page, "links", None) or [])
        if on_activity:
            await on_activity(
                f"Read content from {host}",
                {"url": url, "title": title, "skill": "page_open"},
            )
        return RetrievedEvidence(
            evidence_id=f"ev-open-{i}-{abs(hash(url)) % 10_000_000}",
            title=title,
            url=url,
            text=body,
            source_id=source_id,
            source_name=title,
            source_tier=tier,
            trust_level=trust,
            category=category,
            retrieval_channel=channel,
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=0.86,
            is_link_only=False,
            metadata={
                "citation_label": label,
                "page_fetched": True,
                "page_read": True,
                "provider": "page_open_agent",
                "retrieval_method": "search_result_page_open",
                "browse_reason": target.reason,
                "last_verified": utcnow().isoformat(),
                "action_links": links,
            },
        )

    results = await asyncio.gather(
        *[_one(i, u) for i, u in enumerate(to_open)],
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, RetrievedEvidence):
            evidence.append(r)
    return evidence
