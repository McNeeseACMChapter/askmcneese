"""Perplexity Sonar agentic browsing (domain-filtered).

Uses sonar-pro with web_search_options for multi-step grounded search.
Evidence is fail-closed to allowlisted McNeese / companion domains.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.rccs.allowlist import is_allowed_url, is_mcneese_or_official_url, normalize_url
from app.services.rccs.evidence import sanitize_evidence_text
from app.services.rccs.models import RetrievedEvidence, RetrievalPlan, utcnow
from app.services.search_providers import perplexity_key, web_browsing_enabled


def agentic_enabled() -> bool:
    return os.getenv("PERPLEXITY_AGENTIC_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def agentic_model() -> str:
    return (os.getenv("PERPLEXITY_AGENTIC_MODEL") or os.getenv("PERPLEXITY_MODEL") or "sonar-pro").strip()


def _default_domains(*, social: bool = False) -> list[str]:
    """Campus + RMP by default. Social hosts only when social=True (never silently)."""
    domains = [
        "mcneese.edu",
        "www.mcneese.edu",
        "catalog.mcneese.edu",
        "schedule.mcneese.edu",
        "mcneesesports.com",
        "mcneese.presence.io",
        "ratemyprofessors.com",
        "www.ratemyprofessors.com",
    ]
    if social:
        domains.extend(
            [
                "linkedin.com",
                "www.linkedin.com",
                "instagram.com",
                "www.instagram.com",
                "facebook.com",
                "www.facebook.com",
                "x.com",
                "twitter.com",
                "www.twitter.com",
                "joinhandshake.com",
                "app.joinhandshake.com",
                "www.joinhandshake.com",
            ]
        )
    return domains


def _title_from_url(url: str) -> str:
    try:
        path = urlparse(url).path.strip("/")
        if path:
            leaf = path.split("/")[-1].replace("-", " ").replace("_", " ")
            if leaf and len(leaf) > 2:
                return leaf.title()
        host = urlparse(url).hostname or "Campus source"
        return host.replace("www.", "")
    except Exception:
        return "Campus source"


async def perplexity_agentic_research(
    query: str,
    *,
    plan: RetrievalPlan | None = None,
    include_domains: list[str] | None = None,
    social: bool = False,
    max_results: int = 6,
    on_activity: Any = None,
) -> list[RetrievedEvidence]:
    """Run Sonar Pro agentic web research; open selected pages; return evidence."""
    if not web_browsing_enabled() or not agentic_enabled():
        return []
    key = perplexity_key()
    if not key or not (query or "").strip():
        return []

    from app.services.rccs.browse_plan import BrowseTarget, wants_open_web

    if plan and plan.browse_domains:
        domains = list(plan.browse_domains)
        social = social or bool(plan.browse_social)
    else:
        domains = include_domains or _default_domains(social=social)

    # Sonar search_domain_filter wants apex-ish hosts
    domain_filter = sorted({d.lower().removeprefix("www.") for d in domains})
    open_web = bool(plan and plan.allow_open_web and wants_open_web(query))

    messages = [
        {
            "role": "system",
            "content": (
                "You research questions for AskMcNeese (McNeese State University). "
                "Prefer official mcneese.edu when the question is campus policy or services. "
                "For student ratings use Rate My Professors only and label as student ratings. "
                + (
                    "When LinkedIn/social is in scope: report only publicly visible facts from the "
                    "matching profile (singular). Prefer one primary profile URL. "
                    "Never invent posts, titles, or engagement metrics. "
                    if social
                    else "Do not use LinkedIn, Instagram, Facebook, X, or Handshake unless the user asked. "
                )
                + (
                    "Open-web mode: find the best public sources for the query and include real URLs. "
                    if open_web
                    else ""
                )
                + "Do not invent emails, titles, ratings, or review counts. "
                "Return concise factual bullets with source URLs when possible."
            ),
        },
        {"role": "user", "content": query.strip()},
    ]

    search_type = (os.getenv("PERPLEXITY_SEARCH_TYPE") or "auto").strip()
    context_size = (os.getenv("PERPLEXITY_SEARCH_CONTEXT_SIZE") or "medium").strip()
    web_opts: dict[str, Any] = {
        "search_context_size": context_size,
    }
    if search_type in {"auto", "pro", "fast"}:
        web_opts["search_type"] = search_type

    payload: dict[str, Any] = {
        "model": agentic_model(),
        "messages": messages,
        "temperature": 0.1,
        "web_search_options": web_opts,
    }
    # Domain-filter when classifier scoped the search; omit for true open-web prompts.
    if not open_web and domain_filter:
        payload["search_domain_filter"] = domain_filter[:20]

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=75.0) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        print(f"Perplexity agentic research failed: {e}")
        return []

    content = ""
    try:
        content = data["choices"][0]["message"]["content"] or ""
    except Exception:
        content = ""

    # Prefer structured search_results (title + url + snippet) when Sonar returns them.
    structured: list[dict[str, str]] = []
    seen: set[str] = set()
    for sr in data.get("search_results") or []:
        if not isinstance(sr, dict):
            continue
        url = (sr.get("url") or "").strip()
        if not url:
            continue
        nu = normalize_url(url) or url
        key_u = nu.rstrip("/").lower()
        if key_u in seen:
            continue
        seen.add(key_u)
        structured.append(
            {
                "url": nu,
                "title": (sr.get("title") or "").strip() or _title_from_url(nu),
                "snippet": (sr.get("snippet") or "").strip(),
            }
        )

    for c in data.get("citations") or []:
        if not isinstance(c, str) or not c.strip():
            continue
        nu = normalize_url(c) or c
        key_u = nu.rstrip("/").lower()
        if key_u in seen:
            continue
        seen.add(key_u)
        structured.append({"url": nu, "title": _title_from_url(nu), "snippet": ""})

    evidence: list[RetrievedEvidence] = []
    for i, item in enumerate(structured[:max_results]):
        url = item["url"]
        official = is_mcneese_or_official_url(url)
        companion_ok = False
        if plan is not None:
            companion_ok = is_allowed_url(url, channel="companion", plan=plan)
        elif not official:
            companion_ok = False

        host = (urlparse(url).netloc or "").lower()
        is_rmp = "ratemyprofessors.com" in host
        is_linkedin = "linkedin.com" in host
        # Open-web SERP hits the classifier authorized — keep so page-open can scrape them.
        open_web_hit = open_web and urlparse(url).scheme in {"http", "https"}

        if not official and not companion_ok and not is_rmp and not (social and is_linkedin) and not open_web_hit:
            continue
        if is_linkedin and not social and not open_web:
            continue

        channel = "official_live" if official else "companion"
        tier = "B" if official else "C"
        trust = "campus_live" if official else "social"
        category = "agentic_web" if official else "social"
        source_id = "PPLX_AGENTIC"
        source_name = "Perplexity Sonar"
        citation_label = "Campus live (Perplexity)"

        if is_rmp:
            trust = "student_rating"
            category = "student_rating"
            source_id = "SRC-C-RMP-001"
            source_name = "Rate My Professors"
            citation_label = "Student ratings (Rate My Professors)"
        elif is_linkedin and (social or open_web):
            trust = "social"
            category = "social"
            source_id = "SRC-C-LINKEDIN-001"
            source_name = "LinkedIn (public profile)"
            citation_label = "Public LinkedIn profile"
        elif open_web_hit and not official and not is_rmp and not is_linkedin:
            trust = "web_live"
            category = "web_live"
            channel = "web_live"
            source_id = "PPLX_WEB"
            source_name = "Web search (Perplexity)"
            citation_label = "Web result (will open page when possible)"

        snippet = item.get("snippet") or ""
        if i == 0 and content and (official or is_rmp or is_linkedin):
            body = (
                f"Perplexity Sonar agentic research ({agentic_model()}):\n"
                f"{(snippet or content)[:2200]}\n"
                "Only use facts supported above. Do not invent details."
            )
        else:
            body = (
                f"Perplexity Sonar result:\n"
                f"{(snippet or content[:500] or item.get('title') or url)[:1200]}\n"
                "Only use facts supported above. Do not invent details."
            )
        evidence.append(
            RetrievedEvidence(
                evidence_id=f"ev-pplx-{i}-{abs(hash(url)) % 10_000_000}",
                title=item["title"][:180],
                url=url,
                text=sanitize_evidence_text(body),
                source_id=source_id,
                source_name=source_name,
                source_tier=tier,
                trust_level=trust,
                category=category,
                retrieval_channel=channel,
                published_at=None,
                fetched_at=utcnow(),
                relevance_score=0.8 if i == 0 else 0.65,
                is_link_only=False,
                metadata={
                    "citation_label": citation_label,
                    "provider": "perplexity_agentic",
                    "model": agentic_model(),
                    "snippet_only": True,
                },
            )
        )

    if not evidence and content:
        evidence.append(
            RetrievedEvidence(
                evidence_id=f"ev-pplx-summary-{abs(hash(content)) % 10_000_000}",
                title="Campus live research summary",
                url=None,
                text=sanitize_evidence_text(
                    "Perplexity Sonar agentic summary (no citation URLs returned).\n"
                    f"{content[:3500]}\n"
                    "Treat as unverified until confirmed on official McNeese pages."
                ),
                source_id="PPLX_AGENTIC",
                source_name="Perplexity Sonar",
                source_tier="C",
                trust_level="unverified",
                category="agentic_web",
                retrieval_channel="official_live",
                published_at=None,
                fetched_at=utcnow(),
                relevance_score=0.4,
                is_link_only=True,
                metadata={
                    "citation_label": "Perplexity research (unverified)",
                    "provider": "perplexity_agentic",
                    "fetch_failed": True,
                },
            )
        )

    # Page-open agent: classifier decided where to go — now open selected pages.
    if plan is not None and plan.allow_open_web and plan.max_pages_to_open > 0:
        from app.services.rccs.page_open_agent import open_and_scrape_urls

        target = BrowseTarget(
            domains=list(plan.browse_domains or domains),
            allow_open_web=True,
            max_pages_to_open=plan.max_pages_to_open or 4,
            social=social,
            reason=plan.reason or "classified browse",
        )
        serp_urls = [s["url"] for s in structured if s.get("url")]
        opened = await open_and_scrape_urls(serp_urls, target, on_activity=on_activity)
        if opened:
            opened_keys = {(normalize_url(e.url) or e.url or "").rstrip("/").lower() for e in opened if e.url}
            # Prefer full-page evidence over snippets for the same URL.
            kept = [
                e
                for e in evidence
                if not e.url
                or (normalize_url(e.url) or e.url).rstrip("/").lower() not in opened_keys
            ]
            evidence = opened + kept

    return evidence
