"""Live, term-aware retrieval for McNeese academic calendar questions."""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.academic_calendar import (
    academic_schedule_url_candidates,
    is_academic_schedule_candidate,
    resolve_academic_term,
)
from app.services.activity_events import RETRIEVAL_SOURCE_FOUND, RETRIEVAL_STARTED
from app.services.rccs import config as cfg
from app.services.rccs.evidence import from_fetched_page
from app.services.rccs.models import RetrievedEvidence, RetrievalPlan


async def retrieve_academic_calendar(
    question: str,
    plan: RetrievalPlan,
    limit: int,
    *,
    on_activity=None,
    audit: dict[str, Any] | None = None,
) -> tuple[list[RetrievedEvidence], str | None]:
    """Read the exact term page first; search only if configured routes fail."""
    from app.services.rccs.hybrid import _emit_activity
    from app.services.search_providers import (
        preferred_provider,
        provider_status,
        search_web,
        web_browsing_enabled,
    )
    from app.services.web_search import fetch_page_content

    trace = audit if audit is not None else {}
    trace.setdefault("provider_search_executed", False)
    trace.setdefault("provider_queries", [])
    trace.setdefault("providers_requested", [])
    trace.setdefault("providers_returned", [])
    trace.setdefault("page_fetch_attempted", [])
    trace.setdefault("page_fetch_succeeded", [])
    trace.setdefault("page_fetch_failed", [])

    reference = resolve_academic_term(question)
    candidates = academic_schedule_url_candidates(question)
    trace["resolved_term"] = reference.label if reference else None
    trace["term_year_inferred"] = bool(reference and not reference.explicit_year)
    trace["routing_candidates"] = list(candidates)

    async def _fetch_candidates(urls: list[str], method: str) -> list[RetrievedEvidence]:
        bounded = list(dict.fromkeys(urls))[: max(1, min(limit, 4))]
        if not bounded:
            return []
        trace["page_fetch_attempted"].extend(
            url for url in bounded if url not in trace["page_fetch_attempted"]
        )
        label = reference.label if reference else "the requested term"
        await _emit_activity(
            on_activity,
            RETRIEVAL_STARTED,
            {
                "operation": "page_fetch",
                "retrieval_method": method,
                "urls": bounded,
                "resolved_term": trace.get("resolved_term"),
            },
            message=f"Opening the official {label} academic schedule",
        )

        async def _one(url: str):
            try:
                return await asyncio.wait_for(
                    fetch_page_content(url),
                    timeout=min(5.5, cfg.fetch_timeout_seconds()),
                )
            except Exception:
                return None

        pages = await asyncio.gather(*[_one(url) for url in bounded])
        evidence: list[RetrievedEvidence] = []
        for index, (requested_url, page) in enumerate(zip(bounded, pages)):
            if not getattr(page, "success", False):
                if requested_url not in trace["page_fetch_failed"]:
                    trace["page_fetch_failed"].append(requested_url)
                continue
            page_url = getattr(page, "url", "") or requested_url
            if not is_academic_schedule_candidate(
                page_url,
                question,
                title=getattr(page, "title", "") or "",
            ):
                if page_url not in trace["page_fetch_failed"]:
                    trace["page_fetch_failed"].append(page_url)
                continue
            item = from_fetched_page(page, index, tier="A")
            item.category = "academic_calendar"
            item.metadata.update(
                {
                    "page_fetched": True,
                    "retrieval_method": method,
                    "resolved_term": trace.get("resolved_term"),
                    "term_year_inferred": trace.get("term_year_inferred"),
                    "citation_label": "Official McNeese academic schedule",
                }
            )
            trace["page_fetch_succeeded"].append(page_url)
            evidence.append(item)

        if evidence:
            await _emit_activity(
                on_activity,
                RETRIEVAL_SOURCE_FOUND,
                {
                    "operation": "page_fetch",
                    "sources_found": len(evidence),
                    "urls": [item.url for item in evidence],
                    "resolved_term": trace.get("resolved_term"),
                },
                message=f"Read the official {label} schedule",
            )
        return evidence

    direct = await _fetch_candidates(candidates, "canonical_term_page")
    if direct:
        return direct[:limit], None

    if not web_browsing_enabled():
        return [], "academic_schedule_page_unavailable"

    label = reference.label if reference else question
    search_query = f"McNeese {label} Registrar academic schedule classes begin"
    if "final" in (question or "").lower():
        search_query = f"McNeese {label} final exam schedule Registrar"
    status = provider_status()
    preferred = preferred_provider()
    if preferred == "auto":
        preferred = next(
            (
                name
                for name, key in (
                    ("tavily", "tavily_configured"),
                    ("serper", "serper_configured"),
                    ("perplexity", "perplexity_configured"),
                )
                if status.get(key)
            ),
            "ddg",
        )
    providers = list(dict.fromkeys([preferred, "serper", "tavily", "ddg"]))
    trace["provider_search_executed"] = True
    trace["provider_queries"].append(search_query)
    trace["providers_requested"].extend(
        provider for provider in providers if provider not in trace["providers_requested"]
    )
    await _emit_activity(
        on_activity,
        RETRIEVAL_STARTED,
        {
            "operation": "provider_search",
            "query": search_query,
            "providers": providers,
            "domains": ["mcneese.edu"],
        },
        message=f"Searching McNeese for the official {label} schedule",
    )
    try:
        hits = await asyncio.wait_for(
            search_web(
                search_query,
                max_results=min(limit, 5),
                include_domains=["mcneese.edu", "www.mcneese.edu"],
                providers=providers,
            ),
            timeout=min(6.0, cfg.fetch_timeout_seconds()),
        )
    except Exception:
        hits = []
    for hit in hits:
        if hit.provider not in trace["providers_returned"]:
            trace["providers_returned"].append(hit.provider)
    discovered = [
        hit.url
        for hit in hits
        if hit.url
        and is_academic_schedule_candidate(hit.url, question, title=hit.title or "")
    ]
    opened = await _fetch_candidates(discovered, "provider_discovery_page_fetch")
    return (opened[:limit], None) if opened else ([], "academic_schedule_not_verified")
