"""Hybrid retrieval orchestration for RCCS.

Selective channels: KB, official live (search+fetch), companions, and agentic
Sonar + page-open scrape for classifier-selected URLs.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

from app.services.activity_events import (
    QUERY_CLASSIFIED,
    QUERY_REWRITTEN,
    RETRIEVAL_SOURCE_FOUND,
    RETRIEVAL_STARTED,
    skill_result_message,
    skill_start_message,
    source_preview_from_citations,
)
from app.services.domain_registry import domains_for_question, trust_tier_for_url
from app.services.rccs import config as cfg
from app.services.rccs.adapters import retrieve_from_companion
from app.services.rccs.allowlist import is_allowed_url, normalize_url
from app.services.rccs.classify import (
    INTENT_ACADEMIC_PROGRAMS,
    INTENT_DEGREE_PLAN,
    INTENT_COURSE_CATALOG,
    INTENT_FACULTY_IDENTITY,
    INTENT_POLICY_PROCEDURE,
    INTENT_FORM_LOOKUP,
    INTENT_CAREER_SERVICES,
    INTENT_GENERAL,
    classify_retrieval,
    extract_entities,
    with_user_web_preference,
)
from app.services.rccs.companion_registry import get_companion, match_companions
from app.services.rccs.evidence import (
    dedupe_evidence,
    from_fetched_page,
    has_sufficient_evidence,
    from_kb_chunk,
    looks_like_job_vacancy,
    rank_and_cap,
    sanitize_evidence_text,
)
from app.services.campus_intelligence.full_spectrum import (
    evidence_category_for_shape,
    requires_live_discovery,
)
from app.services.rccs.models import (
    DetectedEntity,
    HybridRetrievalResult,
    RetrievedEvidence,
    RetrievalPlan,
    utcnow,
)
from app.services.rccs.plan import build_retrieval_plan

    # Keep local to avoid circular import with orchestrator.skills â†’ hybrid.
OnActivity = Callable[..., Awaitable[None] | None]


async def _emit_activity(
    on_activity: OnActivity | None,
    event: str,
    metadata: dict[str, Any] | None = None,
    message: str | None = None,
) -> None:
    if on_activity is None:
        return
    try:
        result = on_activity(event, metadata, message)
    except TypeError:
        result = on_activity(event, metadata)
    if asyncio.iscoroutine(result):
        await result


def _preview_from_evidence(items: list[RetrievedEvidence], *, limit: int = 3) -> str | None:
    return source_preview_from_citations(
        [{"title": e.title, "url": e.url} for e in items if e.title],
        limit=limit,
    )


def _attach_governed_provenance(items: list[RetrievedEvidence]) -> None:
    """Bridge every runtime result back to the governed source/group registry."""
    from app.services.campus_intelligence.registry import source_groups_for

    exact_sources: dict[str, Any] = {}
    try:
        from app.services.source_registry import load_registry

        exact_sources = {src.url.rstrip("/").lower(): src for src in load_registry()}
    except Exception:
        exact_sources = {}
    verified_at = utcnow().isoformat()
    for item in items:
        key = (item.url or "").rstrip("/").lower()
        matched = exact_sources.get(key)
        if matched and item.source_id in {"KB", "OFFICIAL_LIVE", "WEB_SEARCH"}:
            item.source_id = matched.source_id
        groups = item.metadata.get("source_groups") or []
        if isinstance(groups, str):
            groups = [groups]
        if not groups:
            groups = source_groups_for(source_id=item.source_id, url=item.url or "")
        item.metadata["source_groups"] = list(dict.fromkeys(groups))
        if item.retrieval_channel in {"official_live", "agentic", "web_live", "companion"}:
            item.metadata.setdefault("last_verified", verified_at)
            item.metadata.setdefault(
                "content_type",
                "pdf" if (item.url or "").lower().split("?", 1)[0].endswith(".pdf") else "html",
            )

_CHANNEL_SKILL = {
    "structured_specialist": "registry_specialist",
    "kb": "kb_retrieve",
    "official_live": "official_web",
    "companion": "companion",
    "agentic": "agentic_web",
}


async def _retrieve_structured_specialist(
    question: str,
    plan: RetrievalPlan,
) -> tuple[list[RetrievedEvidence], str | None]:
    try:
        from app.services.campus_intelligence.compiler import compile_campus_query
        from app.services.campus_intelligence.specialists import retrieve_registry_records

        campus_query = compile_campus_query(question)
        records = await asyncio.to_thread(
            retrieve_registry_records,
            question,
            campus_query,
            limit=min(5, cfg.max_official_results()),
        )
        return records, None
    except Exception as exc:
        return [], str(exc)

async def _retrieve_kb(question: str, limit: int) -> tuple[list[RetrievedEvidence], str | None]:
    try:
        from app.services.retrieval import search_chunks

        chunks = await asyncio.to_thread(search_chunks, question, limit)
        return [from_kb_chunk(c, i) for i, c in enumerate(chunks)], None
    except Exception as e:
        return [], str(e)


async def _retrieve_official(
    question: str,
    plan: RetrievalPlan,
    limit: int,
) -> tuple[list[RetrievedEvidence], str | None]:
    try:
        priority_evidence: list[RetrievedEvidence] = []
        if plan.primary_intent == INTENT_COURSE_CATALOG:
            from app.services.course_retrieval import retrieve_catalog_course

            course_evidence, _course_error = await retrieve_catalog_course(question)
            if course_evidence:
                return course_evidence[:limit], None

        if plan.primary_intent == INTENT_FACULTY_IDENTITY:
            from app.services.people_retrieval import retrieve_person_directory

            person = next((e for e in extract_entities(question) if e.entity_type == "faculty_or_staff"), None)
            if person:
                directory_item = await retrieve_person_directory(person.normalized_name)
                if directory_item:
                    priority_evidence.append(directory_item)

        if plan.primary_intent == INTENT_DEGREE_PLAN:
            from app.services.catalog_retrieval import retrieve_catalog_degree_plan

            catalog_evidence, _catalog_error = await retrieve_catalog_degree_plan(question)
            if catalog_evidence:
                return catalog_evidence[:limit], None

        if plan.primary_intent == INTENT_ACADEMIC_PROGRAMS:
            from app.services.program_inventory import (
                is_program_inventory_question,
                retrieve_undergraduate_program_inventory,
            )

            if is_program_inventory_question(question):
                inventory_evidence, _inventory_error = await retrieve_undergraduate_program_inventory(
                    question
                )
                if inventory_evidence:
                    return inventory_evidence[:limit], None

        from app.services.search_providers import (
            preferred_provider,
            provider_status,
            search_web,
            web_browsing_enabled,
        )
        from app.services.source_registry import match_sources
        from app.services.web_search import fetch_page_content

        urls: list[str] = []
        canonical_urls: list[str] = []
        has_query_specific_page = False
        snippet_evidence: list[RetrievedEvidence] = []
        seen: set[str] = set()

        def _add(u: str) -> None:
            nu = normalize_url(u) or u
            key = nu.rstrip("/").lower()
            if key in seen:
                return
            if not is_allowed_url(nu, channel="official_live"):
                return
            seen.add(key)
            urls.append(nu)

        # Resolve planned official source IDs â†’ seed URLs from the whole registry.
        if plan.official_source_ids:
            try:
                from app.services.source_registry import (
                    academic_schedule_page_candidates,
                    get_source,
                    match_child_urls,
                )

                direct_pages = academic_schedule_page_candidates(question)
                for page_url in direct_pages:
                    _add(page_url)
                has_query_specific_page = bool(direct_pages)

                for sid in plan.official_source_ids:
                    hub = get_source(sid)
                    if hub:
                        _add(hub.url)
                        if sid.startswith("CAP-"):
                            canonical = normalize_url(hub.url) or hub.url
                            if canonical not in canonical_urls:
                                canonical_urls.append(canonical)
                # Expand matched hubs into best-fitting child pages from the registry.
                for child in match_child_urls(
                    question,
                    list(plan.official_source_ids),
                    max_urls=4,
                ):
                    _add(child)
            except Exception as e:
                print(f"Official source id resolve failed: {e}")

        for sq in plan.search_queries[:4] or [question]:
            for src in match_sources(sq, max_sources=3):
                _add(src.url)

        # Search when direct pages are scarce, freshness matters, or the intent
        # routes to an affiliated domain that none of the direct URLs cover.
        routed_domains = domains_for_question(question)
        routed_affiliates = [
            d for d in routed_domains
            if d not in {"mcneese.edu", "catalog.mcneese.edu", "schedule.mcneese.edu"}
        ]
        direct_hosts = {(urlparse(u).hostname or "").lower() for u in urls}
        missing_routed_affiliate = any(
            not any(host == d or host.endswith("." + d) for host in direct_hosts)
            for d in routed_affiliates
        )
        coverage_critical = plan.primary_intent in {
            INTENT_POLICY_PROCEDURE, INTENT_FORM_LOOKUP, INTENT_CAREER_SERVICES,
            INTENT_COURSE_CATALOG, INTENT_FACULTY_IDENTITY, INTENT_GENERAL,
        }
        has_canonical_seed = any(sid.startswith("CAP-") for sid in plan.official_source_ids)
        needs_provider_search = (
            not urls
            or plan.primary_intent == INTENT_FACULTY_IDENTITY
            or (missing_routed_affiliate and not has_canonical_seed)
        )

        # Paid web search APIs (Tavily/Serper/Perplexity) â€” governed domains.
        if web_browsing_enabled() and needs_provider_search:
            try:
                mcneese_domains = domains_for_question(question)
                # Prefer browse_domains from the registry-driven plan.
                if plan.browse_domains:
                    merged: list[str] = []
                    seen_d: set[str] = set()
                    for d in mcneese_domains + list(plan.browse_domains):
                        key = d.lower().removeprefix("www.")
                        if key in seen_d:
                            continue
                        seen_d.add(key)
                        merged.append(d)
                    mcneese_domains = merged

                # One search query only â€” avoid cascading provider timeouts.
                sq = question if coverage_critical else (plan.search_queries[:1] or [question])[0]
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
                hits = await asyncio.wait_for(
                    search_web(
                        sq if "mcneese" in sq.lower() else f"McNeese {sq}",
                        max_results=min(limit, 4),
                        include_domains=mcneese_domains,
                        # Preferred first, but never a single point of failure:
                        # a quota-exhausted provider must not zero the search.
                        providers=list(dict.fromkeys([preferred, "serper", "tavily", "ddg"])),
                    ),
                    timeout=min(6.0, cfg.fetch_timeout_seconds()),
                )
                for hi, hit in enumerate(hits):
                    if hit.url:
                        _add(hit.url)
                    if hit.snippet and hit.url and is_allowed_url(hit.url, channel="official_live"):
                        snippet_evidence.append(
                            RetrievedEvidence(
                                evidence_id=f"ev-web-{hi}-{abs(hash(hit.url)) % 10_000_000}",
                                title=hit.title or "McNeese web result",
                                url=hit.url,
                                text=sanitize_evidence_text(
                                    f"Live web search ({hit.provider}):\n{hit.snippet}"
                                ),
                                source_id="WEB_SEARCH",
                                source_name=hit.title or "Web search",
                                source_tier=trust_tier_for_url(hit.url),
                                trust_level="campus_live",
                                category="official_live",
                                retrieval_channel="official_live",
                                published_at=None,
                                fetched_at=utcnow(),
                                relevance_score=0.72,
                                metadata={
                                    "citation_label": f"Live web ({hit.provider})",
                                    "provider": hit.provider,
                                    "source_groups": list(plan.source_group_ids),
                                },
                            )
                        )
                    elif (
                        hit.snippet
                        and hit.url
                        and plan.primary_intent == INTENT_FACULTY_IDENTITY
                        and not priority_evidence
                    ):
                        public_host = (urlparse(hit.url).hostname or "").lower().removeprefix("www.")
                        if public_host in {"linkedin.com", "github.com", "instagram.com", "facebook.com"}:
                            snippet_evidence.append(
                                RetrievedEvidence(
                                    evidence_id=f"ev-public-person-{hi}-{abs(hash(hit.url)) % 10_000_000}",
                                    title=hit.title or "Public profile result",
                                    url=hit.url,
                                    text=sanitize_evidence_text(
                                        f"Public web result - not an official McNeese record.\n{hit.snippet}"
                                    ),
                                    source_id="PUBLIC_PERSON_SEARCH",
                                    source_name=hit.title or "Public profile result",
                                    source_tier="C",
                                    trust_level="third_party_context",
                                    category="public_person_profile",
                                    retrieval_channel="companion",
                                    published_at=None,
                                    fetched_at=utcnow(),
                                    relevance_score=0.68,
                                    metadata={
                                        "citation_label": f"Public profile ({hit.provider})",
                                        "provider": hit.provider,
                                    },
                                )
                            )
            except Exception as e:
                print(f"Official provider search failed: {e}")

        if not urls and not snippet_evidence:
            return priority_evidence[:limit], (None if priority_evidence else "no_official_urls")

        evidence: list[RetrievedEvidence] = list(priority_evidence) + list(snippet_evidence)
        if urls:
            async def _fetch_one(url: str):
                try:
                    return await asyncio.wait_for(
                        fetch_page_content(url),
                        timeout=min(5.5, cfg.fetch_timeout_seconds()),
                    )
                except Exception:
                    return None

            # Live-discovery domains (jobs, events, housing, athletics, etc.)
            # prefer precise destination URLs over a generic governed hub page.
            fetch_urls = urls if _compiled_live_discovery(plan) else (canonical_urls or urls)
            tasks = [_fetch_one(u) for u in fetch_urls[: min(limit, 3)]]
            pages = await asyncio.gather(*tasks)
            for i, page in enumerate(pages):
                if isinstance(page, Exception) or not getattr(page, "success", False):
                    continue
                if not is_allowed_url(page.url, channel="official_live"):
                    continue
                fetched = from_fetched_page(page, i, tier=trust_tier_for_url(page.url))
                fetched.metadata["source_groups"] = list(plan.source_group_ids)
                evidence.append(fetched)
        return evidence[:limit], None
    except Exception as e:
        return [], str(e)


def _compiled_live_discovery(plan: RetrievalPlan) -> bool:
    cq = plan.compiled_query or {}
    if cq.get("requires_live_discovery"):
        return True
    return requires_live_discovery(
        domain=str(cq.get("domain") or ""),
        freshness=str(cq.get("freshness") or plan.freshness or ""),
        freshness_class=str(cq.get("freshness_class") or "") or None,
        answer_shape=str(cq.get("answer_shape") or ""),
    )


def _evidence_has_job_vacancy(items: list[RetrievedEvidence]) -> bool:
    return any(
        looks_like_job_vacancy(title=item.title, text=item.text, url=item.url or "")
        for item in items
    )


def _planned_search_phrases(question: str, plan: RetrievalPlan) -> list[tuple[str, list[str] | None, str]]:
    """Return (query, include_domains, source_mode) tuples for live discovery."""
    cq = plan.compiled_query or {}
    planned = list(cq.get("planned_queries") or [])
    preferred = [str(d).strip().lower() for d in (cq.get("preferred_domains") or []) if str(d).strip()]
    phrases: list[tuple[str, list[str] | None, str]] = []
    for row in planned:
        query = str(row.get("query") or "").strip()
        if not query:
            continue
        domains = [
            str(d).strip().lower()
            for d in (row.get("preferred_domains") or preferred)
            if str(d).strip()
        ]
        mode = str(row.get("source_mode") or "official_first").strip()
        phrases.append((query, domains, mode))
    if phrases:
        return phrases[:4]
    if str(cq.get("domain") or "") == "employment":
        return [
            (
                'site:mcneese.edu/hr/employment ("Latest Opportunities" OR student OR faculty OR classified)',
                ["mcneese.edu", "www.mcneese.edu"],
                "official_first",
            ),
            (
                "McNeese State University jobs openings Lake Charles student worker Sodexo",
                None,
                "external_discovery",
            ),
            (
                "McNeese jobs Indeed OR BeBee OR ZipRecruiter Lake Charles",
                None,
                "external_discovery",
            ),
        ]
    official_domains = preferred or ["mcneese.edu", "www.mcneese.edu"]
    return [
        (f"site:mcneese.edu {question}", official_domains, "official_first"),
        (question, preferred or None, "official_first"),
    ]


async def _retrieve_agentic(
    question: str,
    plan: RetrievalPlan,
    *,
    use_web_search: bool = False,
    on_activity=None,
) -> tuple[list[RetrievedEvidence], str | None]:
    """Agentic research plus a bounded provider fallback for live campus facts."""
    if not use_web_search or not plan.use_official_live:
        return [], None
    try:
        from app.services.perplexity_agentic import agentic_enabled, perplexity_agentic_research

        compiled = plan.compiled_query or {}
        compiled_domain = str(compiled.get("domain") or "")
        live_discovery = _compiled_live_discovery(plan)
        items: list[RetrievedEvidence] = []
        # Provider cascade is faster for volatile listing-style facts. Skip the
        # broad agentic pass first when the compiled query requires live discovery.
        if agentic_enabled() and not live_discovery:
            social = bool(plan.browse_social) or (
                "social" in (plan.companion_categories or [])
            )

            async def _act(message: str, meta: dict | None = None) -> None:
                await _emit_activity(
                    on_activity,
                    RETRIEVAL_SOURCE_FOUND,
                    meta,
                    message=message,
                )

            items = await perplexity_agentic_research(
                question,
                plan=plan,
                social=social,
                max_results=cfg.max_official_results(),
                on_activity=_act if on_activity else None,
            )

        if items or not live_discovery:
            return items, None

        from app.services.rccs.allowlist import is_safe_public_url_literal
        from app.services.search_providers import preferred_provider, search_web

        _pref = preferred_provider()
        provider_order = list(
            dict.fromkeys(
                ([_pref] if _pref in {"tavily", "serper", "serpapi", "perplexity", "ddg"} else [])
                + ["tavily", "serper", "serpapi", "ddg"]
            )
        )
        phrases = _planned_search_phrases(question, plan)
        search_tasks = []
        for query, domains, mode in phrases:
            include = domains
            if mode == "official_first" and not include:
                include = ["mcneese.edu", "www.mcneese.edu"]
            if mode == "external_discovery":
                include = domains
            search_tasks.append(
                search_web(
                    query,
                    max_results=min(cfg.max_official_results(), 6),
                    include_domains=include,
                    providers=provider_order,
                )
            )
        hit_groups = await asyncio.gather(*search_tasks) if search_tasks else []
        hits = []
        seen_hit_urls: set[str] = set()
        answer_shape = str(compiled.get("answer_shape") or "")
        default_category = evidence_category_for_shape(answer_shape) if answer_shape else (
            "job_listing" if compiled_domain == "employment" else "live_discovery"
        )

        def _hit_rank(hit) -> tuple[int, int, int, int]:
            url = (hit.url or "").lower()
            title = (hit.title or "").lower()
            snippet = (hit.snippet or "").lower()
            vacancy = looks_like_job_vacancy(title=title, text=snippet, url=url)
            official = "mcneese.edu" in url or "mcneesereslife.com" in url
            direct = any(
                marker in url
                for marker in ("viewjob", "/job/", "/jobs/", "/events/", "/calendar", "/housing", "/dining", "/athletics")
            )
            topical = any(
                token in f"{title} {snippet}"
                for token in (
                    str(compiled.get("seed_entity") or "").lower(),
                    str(compiled.get("category") or "").lower(),
                    "student worker",
                    "sodexo",
                    "hiring",
                )
                if token
            )
            # For employment, concrete vacancies outrank random official pages.
            if compiled_domain == "employment":
                return (0 if vacancy else 1, 0 if direct else 1, 0 if topical else 1, 0 if official else 1)
            return (0 if official else 1, 0 if direct else 1, 0 if topical else 1, 0 if vacancy else 1)

        for group in hit_groups:
            for hit in sorted(group or [], key=_hit_rank):
                key = (normalize_url(hit.url) or hit.url or "").rstrip("/").lower()
                if not key or key in seen_hit_urls:
                    continue
                # Drop obvious off-topic employment noise before page-open budget.
                if compiled_domain == "employment" and not looks_like_job_vacancy(
                    title=hit.title or "",
                    text=hit.snippet or "",
                    url=hit.url or "",
                ):
                    title_snip = f"{hit.title or ''} {hit.snippet or ''}".lower()
                    if any(
                        bad in title_snip
                        for bad in ("performing arts", "study abroad", "music major", "libguides")
                    ):
                        continue
                seen_hit_urls.add(key)
                hits.append(hit)
        now = utcnow()
        fallback_items: list[RetrievedEvidence] = []
        category_label = str(compiled.get("category") or compiled_domain or "campus")
        for i, hit in enumerate(hits):
            if not hit.url or not is_safe_public_url_literal(hit.url):
                continue
            if not (hit.snippet or "").strip():
                continue
            vacancy = looks_like_job_vacancy(
                title=hit.title or "",
                text=hit.snippet or "",
                url=hit.url or "",
            )
            item_category = (
                "job_listing"
                if compiled_domain == "employment" and vacancy
                else ("employment_portal" if compiled_domain == "employment" else default_category)
            )
            third_party = "mcneese.edu" not in (hit.url or "").lower() and "mcneesereslife.com" not in (
                hit.url or ""
            ).lower()
            note = (
                "Treat non-McNeese URLs as third-party discovery and tell the user to verify the information is still current."
                if third_party
                else "Official or affiliated McNeese-related result; still verify volatile fields before acting."
            )
            fallback_items.append(
                RetrievedEvidence(
                    evidence_id=f"ev-live-search-{i}-{abs(hash(hit.url)) % 10_000_000}",
                    title=hit.title or f"Current {category_label} search result",
                    url=hit.url,
                    text=sanitize_evidence_text(
                        f"Current web result retrieved for {category_label}.\n"
                        f"Provider: {hit.provider}\n{hit.snippet}\n{note}"
                    ),
                    source_id="FULL_SPECTRUM_LIVE_WEB",
                    source_name=hit.title or "Public live search",
                    source_tier="A" if ("mcneese.edu" in (hit.url or "").lower() or "mcneesereslife.com" in (hit.url or "").lower()) else "C",
                    trust_level="web_live" if (third_party or vacancy) else (
                        "official" if ("mcneese.edu" in (hit.url or "").lower() or "mcneesereslife.com" in (hit.url or "").lower()) else "web_live"
                    ),
                    category=item_category,
                    retrieval_channel="web_live",
                    published_at=None,
                    fetched_at=now,
                    relevance_score=(0.97 if vacancy else (0.9 if _hit_rank(hit)[0] == 0 else 0.8)),
                    metadata={
                        "citation_label": f"Current result ({hit.provider})",
                        "provider": hit.provider,
                        "last_verified": now.isoformat(),
                        "source_groups": list(plan.source_group_ids),
                        "category_id": compiled.get("category_id"),
                        "answer_schema": compiled.get("answer_schema"),
                        "snippet_only": True,
                        "vacancy": vacancy,
                    },
                )
            )

        # Commander step: planned/search URLs are destinations to READ, not cite-only.
        # Snippets discover pages; page-open extracts the answer fields.
        # Prefer opening vacancy URLs first for employment questions.
        open_hits = [hit.url for hit in hits if hit.url]
        if compiled_domain == "employment":
            open_hits = sorted(
                open_hits,
                key=lambda url: (
                    0
                    if looks_like_job_vacancy(
                        title=next((h.title or "" for h in hits if h.url == url), ""),
                        text=next((h.snippet or "" for h in hits if h.url == url), ""),
                        url=url,
                    )
                    else 1
                ),
            )
        page_evidence = await _open_live_destination_pages(
            question,
            plan,
            hits=open_hits,
            on_activity=on_activity,
            evidence_category=default_category,
        )
        if page_evidence:
            for item in page_evidence:
                vacancy = looks_like_job_vacancy(
                    title=item.title,
                    text=item.text,
                    url=item.url or "",
                )
                if compiled_domain == "employment":
                    item.category = "job_listing" if vacancy else "employment_portal"
                    item.metadata["vacancy"] = vacancy
            # Prefer full-page reads over bare snippets for the same URL.
            page_keys = {
                (normalize_url(item.url) or item.url or "").rstrip("/").lower()
                for item in page_evidence
                if item.url
            }
            kept_snippets = [
                item
                for item in fallback_items
                if (normalize_url(item.url) or item.url or "").rstrip("/").lower() not in page_keys
            ]
            merged = [*page_evidence, *kept_snippets]
            return merged[: max(cfg.max_official_results(), 6)], None

        return fallback_items[: cfg.max_official_results()], None
    except Exception as e:
        return [], str(e)


_URL_PRIORITY_STOPWORDS = {
    "about", "after", "again", "also", "another", "apply", "before", "being",
    "campus", "could", "does", "each", "find", "from", "have", "help", "into",
    "know", "mcneese", "much", "need", "next", "official", "over", "page",
    "please", "request", "should", "some", "state", "tell", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "under",
    "university", "want", "what", "when", "where", "which", "while", "will",
    "with", "would", "your",
}

# "- Label: https://..." lines appended by fetch_page_content's action-link scan.
_ACTION_LINK_LINE = re.compile(r"^- (?P<label>[^:\n]{2,120}): (?P<url>https?://\S+)$", re.M)


def _question_terms(question: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9]+", (question or "").lower())
        if len(tok) > 3 and tok not in _URL_PRIORITY_STOPWORDS
    }


def _terms_match(terms: set[str], text: str) -> int:
    low = (text or "").lower()
    return sum(
        1
        for tok in terms
        if tok in low or (tok.endswith("s") and tok[:-1] in low)
    )


def _question_matched_action_links(
    question: str,
    evidence: list[RetrievedEvidence],
    read_urls: set[str],
    *,
    limit: int = 3,
) -> list[str]:
    """Second-hop browse targets: in-page links whose label matches the question."""
    terms = _question_terms(question)
    if not terms:
        return []
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for item in evidence:
        for match in _ACTION_LINK_LINE.finditer(item.text or ""):
            url = match.group("url").rstrip(").,;")
            key = (normalize_url(url) or url).rstrip("/").lower()
            if key in read_urls or key in seen:
                continue
            score = _terms_match(terms, match.group("label")) * 2 + _terms_match(terms, url)
            if score >= 2:
                seen.add(key)
                scored.append((score, url))
    scored.sort(key=lambda pair: -pair[0])
    return [url for _, url in scored[:limit]]


def _filter_question_relevant_items(
    question: str,
    items: list[RetrievedEvidence],
    *,
    limit: int = 3,
) -> list[str]:
    terms = _question_terms(question)
    if not terms:
        return []
    out: list[str] = []
    for item in items:
        blob = f"{item.url or ''} {item.title or ''} {item.text or ''}"
        if _terms_match(terms, blob) >= 1:
            out.append(item.url or "")
        if len(out) >= limit:
            break
    return out


async def _open_live_destination_pages(
    question: str,
    plan: RetrievalPlan,
    *,
    hits: list[str],
    on_activity=None,
    evidence_category: str,
) -> list[RetrievedEvidence]:
    """Fetch and read destination pages discovered by live search / registry hubs."""
    compiled = plan.compiled_query or {}
    scope = str(compiled.get("source_scope") or "")
    live = _compiled_live_discovery(plan)
    can_open = bool(plan.allow_open_web and plan.max_pages_to_open > 0) or live or scope in {
        "knowledge",
        "adaptive",
        "web",
    }
    if not can_open:
        return []

    from app.services.rccs.browse_plan import BrowseTarget
    from app.services.rccs.page_open_agent import open_and_scrape_urls
    from app.services.source_registry import get_source

    candidate_urls: list[str] = []
    for url in hits:
        if url:
            candidate_urls.append(url)
    for sid in plan.official_source_ids or []:
        try:
            hub = get_source(sid)
        except Exception:
            hub = None
        if hub and getattr(hub, "url", None):
            candidate_urls.append(hub.url)
    # Prefer pages whose URL matches the question's own words, then
    # child/application pages and affiliated housing/dining hosts.
    question_tokens = _question_terms(question)

    def _url_priority(url: str) -> tuple[int, int, int]:
        low = (url or "").lower()
        overlap = _terms_match(question_tokens, low)
        direct = any(
            marker in low
            for marker in (
                "/apply",
                "/rates",
                "/housing",
                "/apartment",
                "/job",
                "viewjob",
                "/dining",
                "/meal",
                "/calendar",
                "/events",
                "/scholarship",
            )
        )
        affiliated = any(
            host in low
            for host in (
                "mcneese.edu",
                "mcneesereslife.com",
                "mcneesedining",
                "catalog.mcneese.edu",
                "schedule.mcneese.edu",
                "mcneesesports.com",
            )
        )
        return (-overlap, 0 if direct else 1, 0 if affiliated else 1)

    candidate_urls = sorted(dict.fromkeys(candidate_urls), key=_url_priority)
    max_pages = max(int(plan.max_pages_to_open or 0), 4 if live else 3)
    if scope == "web":
        max_pages = max(max_pages, 5)
    if max_pages <= 0:
        return []

    target = BrowseTarget(
        domains=list(plan.browse_domains or [])
        or [
            "mcneese.edu",
            "www.mcneese.edu",
            "mcneesereslife.com",
            "www.mcneesereslife.com",
        ],
        allow_open_web=True,
        max_pages_to_open=max_pages,
        social=bool(plan.browse_social),
        reason="live-discovery page read",
    )

    planned = list((plan.compiled_query or {}).get("planned_queries") or [])
    if planned:
        preview = "; ".join(
            str(row.get("query") or "")[:80]
            for row in planned[:3]
            if row.get("query")
        )
        await _emit_activity(
            on_activity,
            RETRIEVAL_STARTED,
            {
                "skill": "query_planner",
                "planned_query_count": len(planned),
                "source_scope": (plan.compiled_query or {}).get("source_scope"),
            },
            message=f"Planning searches: {preview}" if preview else f"Planning {len(planned)} category searches",
        )

    async def _act(message: str, meta: dict | None = None) -> None:
        await _emit_activity(
            on_activity,
            RETRIEVAL_SOURCE_FOUND,
            meta,
            message=message,
        )

    opened = await open_and_scrape_urls(
        candidate_urls,
        target,
        on_activity=_act if on_activity else None,
    )
    now = utcnow()
    for item in opened:
        item.category = evidence_category or item.category
        item.retrieval_channel = "official_live" if (
            item.url and ("mcneese.edu" in item.url.lower() or "mcneesereslife.com" in item.url.lower())
        ) else "web_live"
        item.metadata = {
            **(item.metadata or {}),
            "last_verified": now.isoformat(),
            "source_groups": list(plan.source_group_ids),
            "page_read": True,
            "question": question[:180],
        }
        item.is_link_only = False
    return opened

async def _retrieve_companions(
    question: str,
    plan: RetrievalPlan,
    entities: list[DetectedEntity],
) -> tuple[list[RetrievedEvidence], str | None]:
    if not plan.companion_source_ids:
        return [], None
    errors: list[str] = []
    primary_entity = next(
        (e for e in entities if e.entity_type == "faculty_or_staff"),
        None,
    )
    org_entity = next(
        (e for e in entities if e.entity_type == "campus_organization"),
        None,
    )
    # Link-only social lookups should not burn the 15s fetch budget per host.
    per_timeout = (
        3.0
        if (not plan.allow_open_web or plan.max_pages_to_open <= 0)
        else cfg.fetch_timeout_seconds()
    )

    async def _one(sid: str) -> list[RetrievedEvidence]:
        src = get_companion(sid)
        if not src or not src.enabled:
            return []
        entity = primary_entity
        if src.category == "social":
            entity = org_entity or primary_entity
        return await asyncio.wait_for(
            retrieve_from_companion(src, question, entity, plan),
            timeout=per_timeout,
        )

    results = await asyncio.gather(
        *[_one(sid) for sid in plan.companion_source_ids],
        return_exceptions=True,
    )
    out: list[RetrievedEvidence] = []
    for sid, result in zip(plan.companion_source_ids, results):
        if isinstance(result, Exception):
            errors.append(f"{sid}:{result}")
            continue
        out.extend(result or [])
    return out[: cfg.max_companion_results()], ("; ".join(errors) if errors else None)


async def hybrid_retrieve(
    question: str,
    *,
    use_web_search: bool = False,
    source_scope: str | None = None,
    history: list[dict[str, Any]] | None = None,
    on_activity: OnActivity | None = None,
) -> HybridRetrievalResult:
    """Run selective hybrid retrieval according to classification + flags.

    When ``on_activity`` is provided, emits mid-retrieval progress so the live
    trail reflects what each channel is doing in realtime (not only a final summary).
    """
    t0 = time.perf_counter()

    from app.services.conversation_context import (
        normalize_source_scope,
        resolve_question_with_history,
    )
    from app.services.rccs.classify import (
        INTENT_ORG_ACTIVITY,
        INTENT_ORG_IDENTITY,
        INTENT_SOCIAL_PROFILE,
        INTENT_TERM_DEFINITION,
        looks_definitional,
        looks_social_link_lookup,
    )

    scope = normalize_source_scope(source_scope, use_web_search=use_web_search)
    # adaptive and web both enable live channels; knowledge stays official-first.
    effective_web = scope in {"adaptive", "web"} or bool(use_web_search)
    if scope == "knowledge":
        effective_web = False
    resolved_question, context_meta = resolve_question_with_history(question, history)
    if context_meta.get("followup"):
        await _emit_activity(
            on_activity,
            QUERY_CLASSIFIED,
            {"followup": True, "source_scope": scope},
            message="Using earlier conversation context for this follow-up",
        )

    rewritten = resolved_question
    rewrite_meta: dict[str, Any] = {"source_scope": scope, "context": context_meta}
    link_lookup = looks_social_link_lookup(resolved_question)
    # Classify the context-resolved question. A paid LLM rewrite is reserved for
    # structurally ambiguous/compound queries, never charged to every normal turn.
    _pre_classification = classify_retrieval(resolved_question)
    _pre_intent = _pre_classification.primary_intent
    org_fast = _pre_intent in {
        INTENT_ORG_IDENTITY,
        INTENT_ORG_ACTIVITY,
        INTENT_SOCIAL_PROFILE,
    } or link_lookup
    from app.services.query_rewrite import should_rewrite_question

    skip_rewrite = not should_rewrite_question(
        resolved_question,
        use_web_search=effective_web,
        classification_confidence=_pre_classification.confidence,
        secondary_intents=len(_pre_classification.secondary_intents),
    )
    if _pre_intent in {
        INTENT_POLICY_PROCEDURE, INTENT_FORM_LOOKUP, INTENT_CAREER_SERVICES,
        INTENT_COURSE_CATALOG, INTENT_FACULTY_IDENTITY, INTENT_DEGREE_PLAN,
    }:
        skip_rewrite = True
        rewrite_meta = {"skipped": "high_confidence_structured_route"}

    if not skip_rewrite:
        # Heartbeat before the LLM call so the live trail is not silent.
        await _emit_activity(
            on_activity,
            QUERY_REWRITTEN,
            {"mode": "rccs_hybrid", "status": "started"},
            message="Refining the search terms",
        )
        try:
            from app.services.query_rewrite import rewrite_question

            rq = await asyncio.to_thread(
                rewrite_question,
                resolved_question,
                use_web_search=effective_web,
            )
            rewritten = rq.primary or resolved_question
            rewrite_meta = {
                "original": rq.original,
                "rewritten": rq.rewritten,
                "subqueries": rq.subqueries,
                "provider": rq.provider,
            }
        except Exception as e:
            rewrite_meta = {"error": str(e)}
    else:
        if link_lookup:
            rewrite_meta = {"skipped": "social_link_fast_path"}
        elif _pre_intent == INTENT_ORG_IDENTITY:
            rewrite_meta = {"skipped": "org_presence_fast_path"}
        else:
            rewrite_meta = {"skipped": "direct_retrieval_fast_path"}

    if (
        rewritten
        and rewrite_meta.get("rewritten")
        and str(rewrite_meta.get("original") or "").strip()
        != str(rewritten).strip()
    ):
        await _emit_activity(
            on_activity,
            QUERY_REWRITTEN,
            {"mode": "rccs_hybrid", "provider": rewrite_meta.get("provider"), "status": "completed"},
            message="Clarified the search terms for better results",
        )

    # adaptive/web force live channels; knowledge stays official McNeese-first.
    classification = with_user_web_preference(
        classify_retrieval(rewritten),
        effective_web or scope == "knowledge",
    )
    if scope == "knowledge":
        # McNeese-only: keep official live, forbid open-web / companions expansion.
        classification.use_companions = False
        classification.companion_categories = []
    await _emit_activity(
        on_activity,
        QUERY_CLASSIFIED,
        {
            "mode": "rccs_hybrid",
            "primary_intent": getattr(classification, "primary_intent", None),
            "source_scope": scope,
        },
        message=(
            "Using McNeese sources only"
            if scope == "knowledge"
            else (
                "Using best available official sources first"
                if scope == "adaptive"
                else "Including the live web"
            )
        ),
    )
    plan = build_retrieval_plan(
        classification,
        use_web_search=effective_web or scope == "knowledge",
        question=rewritten,
    )
    # Persist UI scope on the compiled query so channels can specialize.
    if plan.compiled_query is not None:
        plan.compiled_query = {
            **dict(plan.compiled_query),
            "source_scope": scope,
            "conversation_followup": bool(context_meta.get("followup")),
            "original_user_question": question,
        }
    if scope == "knowledge":
        plan.allow_agentic_web = False
        plan.browse_social = False
        plan.companion_source_ids = []
        plan.allow_open_web = True
        plan.max_pages_to_open = max(int(plan.max_pages_to_open or 0), 3)
    elif scope == "web":
        plan.allow_agentic_web = True
        plan.allow_open_web = True
        plan.max_pages_to_open = max(int(plan.max_pages_to_open or 0), 5)
    else:  # adaptive
        plan.allow_open_web = True
        plan.max_pages_to_open = max(int(plan.max_pages_to_open or 0), 4)
    definition_fast = classification.primary_intent == INTENT_TERM_DEFINITION
    # Keep original + rewrite subqueries on the plan
    for sq in rewrite_meta.get("subqueries") or []:
        if isinstance(sq, str) and sq and sq not in plan.search_queries:
            plan.search_queries.append(sq)
    # Query planner is the commander for live categories: surface planned phrases.
    planned_rows = list((plan.compiled_query or {}).get("planned_queries") or [])
    if planned_rows:
        preview = "; ".join(str(row.get("query") or "")[:70] for row in planned_rows[:3] if row.get("query"))
        await _emit_activity(
            on_activity,
            RETRIEVAL_STARTED,
            {
                "skill": "query_planner",
                "planned_query_count": len(planned_rows),
                "source_scope": scope,
                "category": (plan.compiled_query or {}).get("category"),
            },
            message=f"Query planner selected searches: {preview}" if preview else "Query planner selected category searches",
        )
    meta: dict[str, Any] = {
        "activated_channels": [],
        "matched_registry_source_ids": list(plan.official_source_ids),
        "companion_source_ids": list(plan.companion_source_ids),
        "rejected_domains": [],
        "result_count_by_channel": {},
        "retrieval_latency_by_channel": {},
        "fallbacks_used": [],
        "query_rewrite": rewrite_meta,
        "campus_query": dict(plan.compiled_query),
        "route_policy": dict(plan.route_policy),
        "selected_source_groups": list(plan.source_group_ids),
        "answer_shape": plan.answer_shape,
        "source_scope": scope,
        "conversation_context": context_meta,
    }
    errors: dict[str, str] = {}
    evidence: list[RetrievedEvidence] = []
    # Only label activity as social when the plan actually browsed social hosts.
    agentic_social = bool(plan.browse_social) or (
        "social" in (plan.companion_categories or [])
    )

    async def _timed(name: str, coro):
        start = time.perf_counter()
        result = await coro
        meta["retrieval_latency_by_channel"][name] = int((time.perf_counter() - start) * 1000)
        return result

    async def _run_channel(name: str, coro):
        skill_id = _CHANNEL_SKILL.get(name, name)
        social_ctx = name == "agentic" and agentic_social
        await _emit_activity(
            on_activity,
            RETRIEVAL_STARTED,
            {"mode": "rccs_hybrid", "skill": skill_id, "channel": name},
            message=skill_start_message(skill_id, social=social_ctx),
        )
        try:
            result = await _timed(name, coro)
        except Exception as e:
            errors[name] = str(e)
            await _emit_activity(
                on_activity,
                RETRIEVAL_SOURCE_FOUND,
                {"sources_found": 0, "skill": skill_id, "channel": name},
                message=skill_result_message(skill_id, 0, social=social_ctx),
            )
            return [], str(e)

        if isinstance(result, Exception):
            errors[name] = str(result)
            await _emit_activity(
                on_activity,
                RETRIEVAL_SOURCE_FOUND,
                {"sources_found": 0, "skill": skill_id, "channel": name},
                message=skill_result_message(skill_id, 0, social=social_ctx),
            )
            return [], str(result)

        items, err = result
        if err:
            errors[name] = err
        count = len(items or [])
        meta["result_count_by_channel"][name] = count
        preview = _preview_from_evidence(items or [])
        found_meta: dict[str, Any] = {
            "sources_found": count,
            "skill": skill_id,
            "channel": name,
        }
        if preview:
            found_meta["source_preview"] = preview
        result_msg = skill_result_message(skill_id, count, social=social_ctx)
        if preview:
            result_msg = f"{result_msg}: {preview}"
        await _emit_activity(
            on_activity,
            RETRIEVAL_SOURCE_FOUND,
            found_meta,
            message=result_msg,
        )
        return items or [], err

    async def _run_wave(wave: dict[str, Any], budget: float) -> None:
        if not wave:
            return
        async_tasks = {
            asyncio.create_task(coro): name for name, coro in wave.items()
        }
        done, pending = await asyncio.wait(
            async_tasks.keys(),
            timeout=budget,
            return_when=asyncio.ALL_COMPLETED,
        )
        if pending:
            errors["budget"] = "retrieval_budget_exceeded"
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            name = async_tasks[task]
            try:
                items, err = task.result()
            except Exception as exc:
                errors[name] = str(exc)
                continue
            if err and name not in errors:
                errors[name] = err
            evidence.extend(items or [])

    # Wave 1 is deliberately cheap: local KB and explicitly requested structured
    # companions. It answers ordinary questions before any paid search or page fetch.
    first_wave: dict[str, Any] = {}
    specialist_decision = (plan.route_policy.get("channels") or {}).get("structured_specialist") or {}
    if plan.compiled_query and specialist_decision.get("state") in {"PRIMARY", "REQUIRED", "CONDITIONAL"}:
        first_wave["structured_specialist"] = _run_channel(
            "structured_specialist",
            _retrieve_structured_specialist(rewritten, plan),
        )
        meta["activated_channels"].append("structured_specialist")
    if plan.use_kb:
        first_wave["kb"] = _run_channel(
            "kb",
            _retrieve_kb(rewritten, cfg.max_kb_results()),
        )
        meta["activated_channels"].append("kb")

    # The plan is the authorization boundary. If it selected a companion (for
    # example Rate My Professors in adaptive faculty mode), execute it even when
    # the base classifier was official-first.
    companion_required = bool(plan.companion_source_ids)
    if companion_required:
        first_wave["companion"] = _run_channel(
            "companion",
            _retrieve_companions(rewritten, plan, classification.entities),
        )
        meta["activated_channels"].append("companion")

    # Required official verification races the local specialist instead of waiting
    # behind it. This preserves governance while removing a full sequential timeout.
    official_decision = (plan.route_policy.get("channels") or {}).get("governed_official_fetch") or {}
    if plan.use_official_live and (
        not first_wave or official_decision.get("state") == "REQUIRED"
    ):
        first_wave["official_live"] = _run_channel(
            "official_live",
            _retrieve_official(rewritten, plan, cfg.max_official_results()),
        )
        meta["activated_channels"].append("official_live")
    await _run_wave(
        first_wave,
        cfg.fast_retrieval_timeout_seconds()
        if "official_live" not in first_wave
        else (
            cfg.catalog_retrieval_timeout_seconds()
            if classification.primary_intent in {INTENT_DEGREE_PLAN, INTENT_COURSE_CATALOG}
            else cfg.total_retrieval_timeout_seconds()
        ),
    )

    # Volatile categories (jobs/events/housing) get a dedicated live-discovery wave.
    # Racing agentic page-opens against official search was cancelling vacancies on
    # budget timeout and leaving only HR portal hubs for generation.
    if (
        _compiled_live_discovery(plan)
        and plan.allow_agentic_web
        and effective_web
        and "agentic" not in meta["activated_channels"]
    ):
        meta["activated_channels"].append("agentic")
        meta["fallbacks_used"].append("live_discovery_dedicated_wave")
        await _run_wave(
            {
                "agentic": _run_channel(
                    "agentic",
                    _retrieve_agentic(
                        rewritten,
                        plan,
                        use_web_search=True,
                        on_activity=on_activity,
                    ),
                )
            },
            cfg.total_retrieval_timeout_seconds(),
        )

    entity_names = [entity.normalized_name for entity in classification.entities]
    fast_sufficient = has_sufficient_evidence(
        rewritten,
        evidence,
        entity_names=entity_names,
    )
    meta["fast_path_sufficient"] = fast_sufficient

    # Wave 2 escalates only when freshness, explicit web mode, or weak evidence
    # actually requires it. This is where the old pipeline spent most of its time.
    official_allowed = (
        plan.use_official_live
        or effective_web
        or (plan.use_kb and not fast_sufficient and cfg.hybrid_enabled())
    )
    # Do not burn a live fetch when the cheap KB wave already answered a stable
    # question. Live-discovery categories still escalate even after KB hits.
    need_official_live = (
        official_allowed
        and "official_live" not in meta["activated_channels"]
        and (
            _compiled_live_discovery(plan)
            or (
                not fast_sufficient
                and (
                    plan.freshness == "current"
                    or (effective_web and not definition_fast)
                )
            )
        )
    )
    if need_official_live:
        meta["fallbacks_used"].append("fast_to_official_live")
        meta["activated_channels"].append("official_live")
        await _run_wave(
            {
                "official_live": _run_channel(
                    "official_live",
                    _retrieve_official(
                        rewritten,
                        plan,
                        min(4, cfg.max_official_results()),
                    ),
                )
            },
            cfg.total_retrieval_timeout_seconds(),
        )

    # Perplexity agentic browse is a last-resort depth pass, not a parallel duplicate
    # of official search. Run it only for explicit web requests whose evidence remains
    # insufficient after the official wave.
    after_official_sufficient = has_sufficient_evidence(
        rewritten,
        evidence,
        entity_names=entity_names,
    )
    has_governed_destination = any(
        item.retrieval_channel == "structured_specialist" and item.url
        for item in evidence
    )
    # Current job discovery and historical leadership always need a depth pass.
    # A named faculty query skips it only when authoritative evidence already
    # contains both the person's name and an identity-bearing role.
    question_low = rewritten.lower()
    leadership_identity = (
        any(cue in question_low for cue in ("who is", "who was", "who were"))
        and any(role in question_low for role in ("dean", "chair", "head", "director"))
    )
    identity_roles = ("professor", "coordinator", "faculty", "instructor", "dean", "chair", "director")
    authoritative_named_identity = any(
        item.source_tier in {"A", "B"}
        and item.retrieval_channel != "structured_specialist"
        and any(name.lower() in f"{item.title} {item.text}".lower() for name in entity_names)
        and any(role in f"{item.title} {item.text}".lower() for role in identity_roles)
        for item in evidence
    ) if entity_names else False
    force_depth_intent = (
        _compiled_live_discovery(plan)
        or classification.primary_intent == INTENT_CAREER_SERVICES
        or leadership_identity
        or (
            classification.primary_intent == INTENT_FACULTY_IDENTITY
            and not authoritative_named_identity
        )
    )
    agentic_empty = meta["result_count_by_channel"].get("agentic", 0) == 0
    run_agentic = (
        plan.allow_agentic_web
        and effective_web
        and official_allowed
        and (
            "agentic" not in meta["activated_channels"]
            or (force_depth_intent and agentic_empty and not _evidence_has_job_vacancy(evidence))
        )
        and not link_lookup
        and (force_depth_intent or not after_official_sufficient)
        and (force_depth_intent or not has_governed_destination)
    )
    if has_governed_destination and not after_official_sufficient and not force_depth_intent:
        meta["fallbacks_used"].append("agentic_skipped_governed_destination_available")
    if run_agentic:
        meta["fallbacks_used"].append("official_to_agentic")
        if "agentic" not in meta["activated_channels"]:
            meta["activated_channels"].append("agentic")
        await _run_wave(
            {
                "agentic": _run_channel(
                    "agentic",
                    _retrieve_agentic(
                        rewritten,
                        plan,
                        use_web_search=True,
                        on_activity=on_activity,
                    ),
                )
            },
            cfg.total_retrieval_timeout_seconds(),
        )
    # Browse pass: open and read destination pages before answering.
    # 1) Hub/link-only destinations (classic Res Life / jobs portal failure).
    # 2) Second hop: action links found INSIDE already-read pages whose label
    #    matches the question (e.g. "Athletic Scholarships" for a sport
    #    scholarship question) — a link the answer would otherwise only cite.
    if _compiled_live_discovery(plan) or scope in {"adaptive", "web", "knowledge"}:
        read_urls = {
            (normalize_url(item.url) or item.url or "").rstrip("/").lower()
            for item in evidence
            if item.url and (item.metadata.get("page_read") or item.metadata.get("page_fetched"))
        }

        def _unread(url: str) -> bool:
            return (normalize_url(url) or url or "").rstrip("/").lower() not in read_urls

        link_only_items = [
            item
            for item in evidence
            if item.url
            and (item.is_link_only or item.metadata.get("snippet_only"))
            and _unread(item.url)
        ]
        followup_urls = _question_matched_action_links(rewritten, evidence, read_urls)
        already_read = bool(read_urls)
        if already_read:
            # Extra reads after a successful pass must earn their latency:
            # only question-relevant link-only destinations qualify. Match the
            # question against URL + title + registry text, so a governed
            # destination like /registrar/ still qualifies for a transcript
            # question even though the URL shares no literal token.
            link_only_urls = _filter_question_relevant_items(rewritten, link_only_items)
        else:
            link_only_urls = [item.url for item in link_only_items]
        to_read = list(dict.fromkeys([*followup_urls, *link_only_urls]))
        if to_read:
            page_reads = await _open_live_destination_pages(
                rewritten,
                plan,
                hits=to_read,
                on_activity=on_activity,
                evidence_category=str((plan.compiled_query or {}).get("answer_shape") or "live_discovery"),
            )
            if page_reads:
                evidence.extend(page_reads)
                meta["fallbacks_used"].append(
                    "followup_page_read" if already_read else "link_only_to_page_read"
                )
                if "page_open" not in meta["activated_channels"]:
                    meta["activated_channels"].append("page_open")
                meta["result_count_by_channel"]["page_open"] = (
                    meta["result_count_by_channel"].get("page_open", 0) + len(page_reads)
                )

    # Last-chance vacancy rescue: never let employment degrade to "check HR" when
    # live boards still have concrete listings.
    if (
        effective_web
        and plan.allow_agentic_web
        and _compiled_live_discovery(plan)
        and str((plan.compiled_query or {}).get("domain") or "") == "employment"
        and not _evidence_has_job_vacancy(evidence)
    ):
        meta["fallbacks_used"].append("employment_vacancy_rescue")
        await _run_wave(
            {
                "agentic": _run_channel(
                    "agentic",
                    _retrieve_agentic(
                        rewritten,
                        plan,
                        use_web_search=True,
                        on_activity=on_activity,
                    ),
                )
            },
            cfg.total_retrieval_timeout_seconds(),
        )

    _attach_governed_provenance(evidence)
    before = len(evidence)
    evidence = dedupe_evidence(evidence)
    entity_names = [e.normalized_name for e in classification.entities]
    evidence = rank_and_cap(
        evidence,
        entity_names=entity_names,
        freshness=plan.freshness,
        companion_requested=bool(plan.companion_source_ids),
        question=rewritten,
    )
    # Sanitize all texts once more
    for ev in evidence:
        ev.text = sanitize_evidence_text(ev.text)

    # Shared domain-intent sufficiency rejects topical drift before generation.
    precise_failure = ""
    if plan.compiled_query:
        try:
            from app.services.campus_intelligence.compiler import compile_campus_query
            from app.services.campus_intelligence.evidence import evaluate_evidence
            from app.services.campus_intelligence.failures import render_precise_failure
            from app.services.campus_intelligence.route_policy import resolve_route_policy

            campus_query = compile_campus_query(rewritten)
            resolved_policy = resolve_route_policy(campus_query)
            sufficiency = evaluate_evidence(campus_query, evidence, policy=resolved_policy)
            sufficiency_dict = sufficiency.to_dict()
            meta["evidence_sufficiency"] = sufficiency_dict
            meta["rejected_evidence"] = list(sufficiency.rejected_evidence)
            accepted_ids = set(sufficiency.accepted_evidence_ids)
            vacancy_keep = [
                ev
                for ev in evidence
                if looks_like_job_vacancy(title=ev.title, text=ev.text, url=ev.url or "")
            ]
            inventory_keep = [
                ev for ev in evidence if ev.category == "program_inventory"
            ]
            evidence = [ev for ev in evidence if ev.evidence_id in accepted_ids]
            # Concrete vacancies / majors inventories can fail token overlap — keep them.
            kept_ids = {ev.evidence_id for ev in evidence}
            for ev in [*vacancy_keep, *inventory_keep]:
                if ev.evidence_id not in kept_ids:
                    evidence.append(ev)
                    kept_ids.add(ev.evidence_id)
            core_fields_by_shape = {
                "job_list": {"category", "last_verified"},
                "form_result": {"form", "active_url", "owner"},
                "deadline_card": {"date", "deadline", "term", "last_verified"},
                "calendar_list": {"events", "term", "last_verified"},
                "event_list": {"events", "last_verified"},
                "categorized_list": {"categories", "last_verified"},
                "contact_card": {"contact_method", "role"},
                "policy_plus_steps": {"policy", "owner"},
                "steps_with_action_link": {"application_url", "active_url", "owner"},
                "course_result": {"course", "description", "catalog_year"},
                "degree_requirement_summary": {"program", "catalog_year", "requirements"},
                "location_card": {"place", "location"},
                "troubleshooting_steps": {"steps", "escalation_contact"},
                "action_link_result": {"active_url", "owner"},
                "precise_partial": {"last_verified"},
            }
            candidates = core_fields_by_shape.get(campus_query.answer_shape, set())
            configured = set(campus_query.required_fields)
            core = candidates & configured
            # Alternate action fields satisfy the same material contract.
            portal_partial_shapes = {
                "job_list",
                "event_list",
                "calendar_list",
                "categorized_list",
                "precise_partial",
                "action_link_result",
            }
            if sufficiency.passed:
                # The authoritative check already confirmed every configured
                # required field is covered by matching, in-scope evidence.
                # The shape-specific heuristics below exist only to grant a
                # *partial* pass when that full check fails; they must never
                # re-reject evidence that already fully passed.
                blocking_missing = False
            elif campus_query.answer_shape in portal_partial_shapes and campus_query.requires_live_discovery:
                # A governed official destination is useful even when volatile
                # listing rows could not be verified yet.
                blocking_missing = not (
                    sufficiency.field_coverage.get("category")
                    or sufficiency.field_coverage.get("categories")
                    or sufficiency.field_coverage.get("verified_portal")
                    or sufficiency.field_coverage.get("active_url")
                    or sufficiency.field_coverage.get("event")
                    or sufficiency.field_coverage.get("events")
                    or sufficiency.partial_allowed
                    or bool(vacancy_keep)
                )
            elif campus_query.answer_shape == "job_list":
                # Only enforce fields this query actually required; a field
                # this domain/intent never configured must not become a
                # phantom blocker.
                blocking_missing = (
                    not vacancy_keep
                    and (
                        ("category" in configured and not sufficiency.field_coverage.get("category"))
                        or ("verified_portal" in configured and not sufficiency.field_coverage.get("verified_portal"))
                    )
                )
            elif campus_query.answer_shape == "steps_with_action_link":
                action_fields = {"application_url", "active_url"} & configured
                action_ok = not action_fields or any(sufficiency.field_coverage.get(field) for field in action_fields)
                blocking_missing = ({"owner"} & configured and not sufficiency.field_coverage.get("owner")) or not action_ok
            elif campus_query.answer_shape == "deadline_card":
                date_fields = {"date", "deadline"} & configured
                date_ok = not date_fields or any(sufficiency.field_coverage.get(field) for field in date_fields)
                blocking_missing = (not date_ok) or any(not sufficiency.field_coverage.get(field) for field in core - {"date", "deadline"})
            else:
                blocking_missing = any(not sufficiency.field_coverage.get(field) for field in core)
            if campus_query.freshness == "personal":
                evidence = []
            elif blocking_missing and not vacancy_keep and not inventory_keep:
                # Keep portal-partial employment evidence; only hard-wipe dead ends.
                if not (
                    campus_query.answer_shape in portal_partial_shapes
                    and sufficiency.partial_allowed
                ):
                    evidence = []
            elif inventory_keep and not evidence:
                evidence = list(inventory_keep)
            precise_failure = render_precise_failure(
                campus_query,
                sufficiency,
                policy=resolved_policy,
                attempted_routes=list(meta["activated_channels"]),
            )
        except Exception as exc:
            meta["evidence_sufficiency_error"] = str(exc)[:300]

    meta["evidence_count_before_dedup"] = before
    meta["evidence_count_after_dedup"] = len(evidence)
    meta["total_retrieval_latency"] = int((time.perf_counter() - t0) * 1000)
    meta["routing_reason"] = plan.reason
    meta["classification"] = {
        "primary_intent": classification.primary_intent,
        "freshness": classification.freshness,
        "use_companions": classification.use_companions,
        "companion_categories": classification.companion_categories,
        "entities": [
            {"name": e.normalized_name, "type": e.entity_type}
            for e in classification.entities
        ],
    }
    route_attempts: list[dict[str, Any]] = []
    channel_to_runtime = {
        "structured_specialist": "structured_specialist",
        "indexed_kb": "kb",
        "governed_official_fetch": "official_live",
        "approved_companion": "companion",
        "agentic_web": "agentic",
    }
    for channel, decision in (plan.route_policy.get("channels") or {}).items():
        runtime_channel = channel_to_runtime.get(channel)
        if runtime_channel and runtime_channel in meta["activated_channels"]:
            status = "executed"
            route_reason = decision.get("reason")
        elif decision.get("state") in {"FORBIDDEN", "NOT_APPLICABLE"}:
            status = decision.get("state", "skipped").lower()
            route_reason = decision.get("reason")
        else:
            status = "skipped"
            route_reason = decision.get("reason")
        route_attempts.append({
            "route": channel,
            "state": decision.get("state"),
            "status": status,
            "reason": route_reason,
            "condition": decision.get("condition"),
            "latency_ms": meta["retrieval_latency_by_channel"].get(runtime_channel, 0) if runtime_channel else 0,
            "result_count": meta["result_count_by_channel"].get(runtime_channel, 0) if runtime_channel else 0,
        })
    meta["route_trace"] = {
        "compiled_query": dict(plan.compiled_query),
        "route_policy": dict(plan.route_policy),
        "source_groups": list(plan.source_group_ids),
        "attempts": route_attempts,
        "rejected_evidence": list(meta.get("rejected_evidence") or []),
        "evidence_sufficiency": dict(meta.get("evidence_sufficiency") or {}),
        "answer_shape": plan.answer_shape,
    }
    meta["safe_response"] = {
        "retrieval_mode": "rccs_hybrid",
        "requested_mode": scope,
        "effective_mode": (
            "official_web"
            if "official_live" in meta["activated_channels"]
            or "agentic" in meta["activated_channels"]
            or "page_open" in meta["activated_channels"]
            else ("knowledge" if "kb" in meta["activated_channels"] else "none")
        ),
        "retrieval_channels": list(meta["activated_channels"]),
        "web_search_executed": (
            "official_live" in meta["activated_channels"]
            or "agentic" in meta["activated_channels"]
        ),
        "web_search_status": (
            "success"
            if (
                meta["result_count_by_channel"].get("official_live", 0) > 0
                or meta["result_count_by_channel"].get("agentic", 0) > 0
            )
            else (
                "error"
                if errors.get("official_live")
                or errors.get("official_live_fallback")
                or errors.get("agentic")
                else (
                    "no_results"
                    if "official_live" in meta["activated_channels"]
                    or "agentic" in meta["activated_channels"]
                    else "not_requested"
                )
            )
        ),
        "checked_source_categories": list(
            {
                *(["knowledge_base"] if plan.use_kb else []),
                *(["official_live"] if plan.use_official_live else []),
                *(["agentic"] if "agentic" in meta["activated_channels"] else []),
                *plan.companion_categories,
            }
        ),
        "used_companion_sources": list(plan.companion_source_ids),
        "freshness_status": plan.freshness,
        "source_count": len(evidence),
        "matched_source_ids": list(plan.official_source_ids),
        "knowledge_evidence_supplied": meta["result_count_by_channel"].get("kb", 0) > 0,
        "official_live_web_search_executed": "official_live" in meta["activated_channels"],
        "companion_retrieval_executed": "companion" in meta["activated_channels"],
        "agentic_retrieval_executed": "agentic" in meta["activated_channels"],
        "official_web_search_available": True,
        "campus_query": dict(plan.compiled_query),
        "answer_shape": plan.answer_shape,
        "evidence_sufficiency": dict(meta.get("evidence_sufficiency") or {}),
        "precise_failure": precise_failure,
        "route_trace": dict(meta.get("route_trace") or {}),
    }

    return HybridRetrievalResult(
        evidence=evidence,
        classification=classification,
        plan=plan,
        metadata=meta,
        errors_by_channel=errors,
    )


# Public channel runners for the supervisor skill wrappers (same implementations).
retrieve_kb_channel = _retrieve_kb
retrieve_official_channel = _retrieve_official
retrieve_companions_channel = _retrieve_companions
retrieve_agentic_channel = _retrieve_agentic







