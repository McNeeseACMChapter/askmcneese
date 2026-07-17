"""Hybrid retrieval orchestration for RCCS.

Selective channels: KB, official live (search+fetch), companions, and agentic
Sonar + page-open scrape for classifier-selected URLs.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from app.services.activity_events import (
    QUERY_REWRITTEN,
    RETRIEVAL_SOURCE_FOUND,
    RETRIEVAL_STARTED,
    skill_result_message,
    skill_start_message,
    source_preview_from_citations,
)
from app.services.rccs import config as cfg
from app.services.rccs.adapters import retrieve_from_companion
from app.services.rccs.allowlist import is_allowed_url, normalize_url
from app.services.rccs.classify import classify_retrieval, with_user_web_preference
from app.services.rccs.companion_registry import get_companion, match_companions
from app.services.rccs.evidence import (
    dedupe_evidence,
    from_fetched_page,
    from_kb_chunk,
    rank_and_cap,
    sanitize_evidence_text,
)
from app.services.rccs.models import (
    DetectedEntity,
    HybridRetrievalResult,
    RetrievedEvidence,
    RetrievalPlan,
    utcnow,
)
from app.services.rccs.plan import build_retrieval_plan

# Keep local to avoid circular import with orchestrator.skills → hybrid.
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


_CHANNEL_SKILL = {
    "kb": "kb_retrieve",
    "official_live": "official_web",
    "companion": "companion",
    "agentic": "agentic_web",
}


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
        from app.services.search_providers import search_web, web_browsing_enabled
        from app.services.source_registry import match_sources
        from app.services.web_search import fetch_page_content

        urls: list[str] = []
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

        for sq in plan.search_queries[:4] or [question]:
            for src in match_sources(sq, max_sources=3):
                _add(src.url)

        # Paid web search APIs (Tavily/Serper/Perplexity) — McNeese domains
        if web_browsing_enabled():
            try:
                mcneese_domains = [
                    "mcneese.edu",
                    "www.mcneese.edu",
                    "catalog.mcneese.edu",
                    "schedule.mcneese.edu",
                    "mcneesesports.com",
                    "mcneese.presence.io",
                ]
                # One search query only — cascading 3×provider timeouts was 45s+ alone.
                sq = (plan.search_queries[:1] or [question])[0]
                hits = await asyncio.wait_for(
                    search_web(
                        sq if "mcneese" in sq.lower() else f"McNeese {sq}",
                        max_results=limit,
                        include_domains=mcneese_domains,
                        providers=["tavily", "serper", "perplexity"],
                    ),
                    timeout=min(12.0, cfg.fetch_timeout_seconds()),
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
                                source_tier="B",
                                trust_level="campus_live",
                                category="official_live",
                                retrieval_channel="official_live",
                                published_at=None,
                                fetched_at=utcnow(),
                                relevance_score=0.72,
                                metadata={
                                    "citation_label": f"Live web ({hit.provider})",
                                    "provider": hit.provider,
                                },
                            )
                        )
            except Exception as e:
                print(f"Official provider search failed: {e}")

        # Legacy DDG still attempted inside search_web cascade

        if not urls and not snippet_evidence:
            return [], "no_official_urls"

        evidence: list[RetrievedEvidence] = list(snippet_evidence)
        if urls:
            tasks = [fetch_page_content(u) for u in urls[: limit + 2]]
            pages = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=cfg.total_retrieval_timeout_seconds(),
            )
            for i, page in enumerate(pages):
                if isinstance(page, Exception) or not getattr(page, "success", False):
                    continue
                if not is_allowed_url(page.url, channel="official_live"):
                    continue
                evidence.append(from_fetched_page(page, i, tier="B"))
        return evidence[:limit], None
    except Exception as e:
        return [], str(e)


async def _retrieve_agentic(
    question: str,
    plan: RetrievalPlan,
    *,
    use_web_search: bool = False,
    on_activity=None,
) -> tuple[list[RetrievedEvidence], str | None]:
    """Perplexity Sonar agentic channel + page-open scrape for selected URLs."""
    if not use_web_search or not plan.use_official_live:
        return [], None
    try:
        from app.services.perplexity_agentic import agentic_enabled, perplexity_agentic_research

        if not agentic_enabled():
            return [], None
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
        return items, None
    except Exception as e:
        return [], str(e)


async def _retrieve_companions(
    question: str,
    plan: RetrievalPlan,
    entities: list[DetectedEntity],
) -> tuple[list[RetrievedEvidence], str | None]:
    if not plan.companion_source_ids:
        return [], None
    errors: list[str] = []
    out: list[RetrievedEvidence] = []
    primary_entity = next(
        (e for e in entities if e.entity_type == "faculty_or_staff"),
        None,
    )
    org_entity = next(
        (e for e in entities if e.entity_type == "campus_organization"),
        None,
    )

    for sid in plan.companion_source_ids:
        src = get_companion(sid)
        if not src or not src.enabled:
            continue
        entity = primary_entity
        if src.category == "social":
            entity = org_entity or primary_entity
        try:
            items = await asyncio.wait_for(
                retrieve_from_companion(src, question, entity, plan),
                timeout=cfg.fetch_timeout_seconds(),
            )
            out.extend(items)
        except Exception as e:
            errors.append(f"{sid}:{e}")
    return out[: cfg.max_companion_results()], ("; ".join(errors) if errors else None)


async def hybrid_retrieve(
    question: str,
    *,
    use_web_search: bool = False,
    on_activity: OnActivity | None = None,
) -> HybridRetrievalResult:
    """Run selective hybrid retrieval according to classification + flags.

    When ``on_activity`` is provided, emits mid-retrieval progress so the live
    trail reflects what each channel is doing in realtime (not only a final summary).
    """
    t0 = time.perf_counter()

    # LLM rewrite before classify/retrieve (improves entity + search queries).
    # Skip for definitional questions — rewrite alone was ~4s and often hurts.
    from app.services.rccs.classify import INTENT_TERM_DEFINITION, looks_definitional

    rewritten = question
    rewrite_meta: dict[str, Any] = {}
    skip_rewrite = looks_definitional(question)
    if not skip_rewrite:
        try:
            from app.services.query_rewrite import rewrite_question

            rq = rewrite_question(question, use_web_search=use_web_search)
            rewritten = rq.primary or question
            rewrite_meta = {
                "original": rq.original,
                "rewritten": rq.rewritten,
                "subqueries": rq.subqueries,
                "provider": rq.provider,
            }
        except Exception as e:
            rewrite_meta = {"error": str(e)}
    else:
        rewrite_meta = {"skipped": "definitional_fast_path"}

    if (
        rewritten
        and rewrite_meta.get("rewritten")
        and str(rewrite_meta.get("original") or "").strip()
        != str(rewritten).strip()
    ):
        await _emit_activity(
            on_activity,
            QUERY_REWRITTEN,
            {"mode": "rccs_hybrid", "provider": rewrite_meta.get("provider")},
            message="Clarified the search terms for better results",
        )

    classification = with_user_web_preference(
        classify_retrieval(rewritten),
        use_web_search,
    )
    plan = build_retrieval_plan(
        classification,
        use_web_search=use_web_search,
        question=rewritten,
    )
    definition_fast = classification.primary_intent == INTENT_TERM_DEFINITION
    # Keep original + rewrite subqueries on the plan
    for sq in rewrite_meta.get("subqueries") or []:
        if isinstance(sq, str) and sq and sq not in plan.search_queries:
            plan.search_queries.append(sq)
    meta: dict[str, Any] = {
        "activated_channels": [],
        "matched_registry_source_ids": list(plan.official_source_ids),
        "companion_source_ids": list(plan.companion_source_ids),
        "rejected_domains": [],
        "result_count_by_channel": {},
        "retrieval_latency_by_channel": {},
        "fallbacks_used": [],
        "query_rewrite": rewrite_meta,
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

    tasks = {}
    if plan.use_kb:
        tasks["kb"] = _run_channel("kb", _retrieve_kb(rewritten, cfg.max_kb_results()))
        meta["activated_channels"].append("kb")

    # Definition fast-path: KB only in the first wave (no parallel agentic/official).
    if not definition_fast:
        if plan.use_official_live:
            tasks["official_live"] = _run_channel(
                "official_live",
                _retrieve_official(rewritten, plan, cfg.max_official_results()),
            )
            meta["activated_channels"].append("official_live")
        if plan.companion_source_ids:
            tasks["companion"] = _run_channel(
                "companion",
                _retrieve_companions(rewritten, plan, classification.entities),
            )
            meta["activated_channels"].append("companion")

        # Perplexity Sonar agentic pass (web mode) — skipped for definitions.
        run_agentic = use_web_search and plan.use_official_live
        if run_agentic:
            tasks["agentic"] = _run_channel(
                "agentic",
                _retrieve_agentic(
                    rewritten,
                    plan,
                    use_web_search=use_web_search,
                    on_activity=on_activity,
                ),
            )
            meta["activated_channels"].append("agentic")

    if tasks:
        keys = list(tasks.keys())
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[tasks[k] for k in keys],
                    return_exceptions=True,
                ),
                timeout=cfg.total_retrieval_timeout_seconds()
                if definition_fast
                else max(cfg.total_retrieval_timeout_seconds(), 35.0),
            )
        except asyncio.TimeoutError:
            results = [TimeoutError("retrieval_budget_exceeded")] * len(keys)
            errors["budget"] = "retrieval_budget_exceeded"
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                errors[key] = str(result)
                continue
            items, err = result
            if err and key not in errors:
                errors[key] = err
            evidence.extend(items)

    # KB insufficient → official live fallback (not companions / not agentic)
    kb_count = meta["result_count_by_channel"].get("kb", 0)
    need_official_fallback = (
        plan.use_kb
        and kb_count < cfg.kb_min_results()
        and "official_live" not in meta["activated_channels"]
        and cfg.hybrid_enabled()
    )
    # Definitions in web mode: escalate once if KB is thin or off-topic.
    if definition_fast and use_web_search:
        title_blob = " ".join((e.title or "").lower() for e in evidence)
        kb_looks_on_topic = any(
            k in title_blob
            for k in (
                "faculty",
                "appointment",
                "tenure",
                "credential",
                "professor",
                "policy",
                "staff",
                "handbook",
            )
        )
        if kb_count < 2 or not kb_looks_on_topic:
            need_official_fallback = True
    if need_official_fallback:
        meta["fallbacks_used"].append("kb_to_official_live")
        items, err = await _run_channel(
            "official_live",
            _retrieve_official(rewritten, plan, min(3, cfg.max_official_results())),
        )
        if err:
            errors["official_live_fallback"] = err
        evidence.extend(items)
        if "official_live" not in meta["activated_channels"]:
            meta["activated_channels"].append("official_live")

    before = len(evidence)
    evidence = dedupe_evidence(evidence)
    entity_names = [e.normalized_name for e in classification.entities]
    evidence = rank_and_cap(
        evidence,
        entity_names=entity_names,
        freshness=plan.freshness,
        companion_requested=bool(plan.companion_source_ids),
    )
    # Sanitize all texts once more
    for ev in evidence:
        ev.text = sanitize_evidence_text(ev.text)

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
    meta["safe_response"] = {
        "retrieval_mode": "rccs_hybrid",
        "requested_mode": "web" if use_web_search else "knowledge",
        "effective_mode": (
            "official_web"
            if "official_live" in meta["activated_channels"]
            or "agentic" in meta["activated_channels"]
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
