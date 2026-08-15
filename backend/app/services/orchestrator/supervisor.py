"""Thin custom supervisor: Plan → Route → Execute → Reflect (one retry max).

Returns HybridRetrievalResult so ask.py / SSE stay unchanged.
Activity callbacks use only frozen activity_events names.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections import defaultdict
from typing import Any

from app.services.activity_events import (
    QUERY_CLASSIFIED,
    QUERY_REWRITTEN,
    RERANKING_COMPLETED,
    RERANKING_STARTED,
    RETRIEVAL_SOURCE_FOUND,
    RETRIEVAL_STARTED,
    skill_result_message,
    skill_start_message,
)
from app.services.orchestrator.config import reflect_enabled
from app.services.orchestrator.models import (
    Critique,
    OnActivity,
    SkillContext,
    SkillPlan,
    SkillStep,
)
from app.services.orchestrator.plan import build_skill_plan
from app.services.orchestrator.reflect import reflect
from app.services.orchestrator.route import route_retry_skill, route_step
from app.services.orchestrator.skills import execute_skill
from app.services.rccs import config as rccs_cfg
from app.services.rccs.classify import classify_retrieval, with_user_web_preference
from app.services.rccs.evidence import dedupe_evidence, rank_and_cap, sanitize_evidence_text
from app.services.rccs.models import HybridRetrievalResult, RetrievedEvidence
from app.services.rccs.plan import build_retrieval_plan


async def _emit(
    on_activity: OnActivity | None,
    event: str,
    metadata: dict[str, Any] | None = None,
    *,
    message: str | None = None,
) -> None:
    if on_activity is None:
        return
    try:
        result = on_activity(event, metadata, message)
    except TypeError:
        # Backward-compatible 2-arg callbacks
        result = on_activity(event, metadata)
    if inspect.isawaitable(result):
        await result


async def _rewrite(question: str, *, use_web_search: bool) -> tuple[str, dict[str, Any]]:
    """Rewrite off the event loop so SSE can keep flushing during the LLM call."""
    rewrite_meta: dict[str, Any] = {}
    rewritten = question
    try:
        from app.services.query_rewrite import rewrite_question

        rq = await asyncio.to_thread(
            rewrite_question,
            question,
            use_web_search=use_web_search,
        )
        rewritten = rq.primary or question
        rewrite_meta = {
            "original": rq.original,
            "rewritten": rq.rewritten,
            "subqueries": rq.subqueries,
            "provider": rq.provider,
        }
    except Exception as e:
        rewrite_meta = {"error": str(e)}
    return rewritten, rewrite_meta


def _build_safe_response(
    *,
    use_web_search: bool,
    plan,
    activated: list[str],
    counts: dict[str, int],
    errors: dict[str, str],
    evidence_n: int,
) -> dict[str, Any]:
    return {
        "retrieval_mode": "supervisor_rccs",
        "requested_mode": "web" if use_web_search else "knowledge",
        "effective_mode": (
            "official_web"
            if "official_live" in activated or "agentic" in activated
            else ("knowledge" if "kb" in activated else "none")
        ),
        "retrieval_channels": list(activated),
        "web_search_executed": (
            "official_live" in activated or "agentic" in activated
        ),
        "web_search_status": (
            "success"
            if counts.get("official_live", 0) > 0 or counts.get("agentic", 0) > 0
            else (
                "error"
                if errors.get("official_web")
                or errors.get("official_live")
                or errors.get("agentic_web")
                or errors.get("agentic")
                else (
                    "no_results"
                    if "official_live" in activated or "agentic" in activated
                    else "not_requested"
                )
            )
        ),
        "checked_source_categories": list(
            {
                *(["knowledge_base"] if plan.use_kb else []),
                *(["official_live"] if plan.use_official_live else []),
                *(["agentic"] if "agentic" in activated else []),
                *plan.companion_categories,
            }
        ),
        "used_companion_sources": list(plan.companion_source_ids),
        "freshness_status": plan.freshness,
        "source_count": evidence_n,
        "matched_source_ids": list(plan.official_source_ids),
        "knowledge_evidence_supplied": counts.get("kb", 0) > 0,
        "official_live_web_search_executed": "official_live" in activated,
        "companion_retrieval_executed": "companion" in activated,
        "agentic_retrieval_executed": "agentic" in activated,
        "official_web_search_available": True,
        "supervisor": True,
    }


def _skill_to_channel(skill_id: str) -> str:
    return {
        "kb_retrieve": "kb",
        "official_web": "official_live",
        "companion": "companion",
        "agentic_web": "agentic",
    }.get(skill_id, skill_id)


async def _run_step(
    step: SkillStep,
    ctx: SkillContext,
    *,
    errors: dict[str, str],
    activated: list[str],
    counts: dict[str, int],
    latency: dict[str, int],
    on_activity: OnActivity | None = None,
) -> list[RetrievedEvidence]:
    skill_id = route_step(step, ctx)
    if not skill_id:
        errors[step.step_id] = f"blocked:{step.skill_id}"
        return []

    channel = _skill_to_channel(skill_id)
    if channel not in activated:
        activated.append(channel)

    social_ctx = skill_id == "agentic_web" and (
        "social" in (ctx.plan.companion_categories or [])
    )
    await _emit(
        on_activity,
        RETRIEVAL_STARTED,
        {"mode": "supervisor_rccs", "skill": skill_id, "channel": channel},
        message=skill_start_message(skill_id, social=social_ctx),
    )

    t0 = time.perf_counter()
    try:
        items = await execute_skill(skill_id, step, ctx)
    except Exception as e:
        errors[skill_id] = str(e)
        latency[channel] = int((time.perf_counter() - t0) * 1000)
        await _emit(
            on_activity,
            RETRIEVAL_SOURCE_FOUND,
            {"sources_found": 0, "skill": skill_id, "channel": channel},
            message=skill_result_message(skill_id, 0, social=social_ctx),
        )
        return []
    latency[channel] = int((time.perf_counter() - t0) * 1000)
    counts[channel] = counts.get(channel, 0) + len(items)
    await _emit(
        on_activity,
        RETRIEVAL_SOURCE_FOUND,
        {"sources_found": len(items), "skill": skill_id, "channel": channel},
        message=skill_result_message(skill_id, len(items), social=social_ctx),
    )
    return items


async def run(
    question: str,
    *,
    use_web_search: bool = False,
    history: list[dict[str, Any]] | None = None,
    request_context: dict[str, Any] | None = None,
    on_activity: OnActivity | None = None,
    campus_query=None,
    conversation_context: dict[str, Any] | None = None,
) -> HybridRetrievalResult:
    """Plan → Route → Execute → Reflect (single retry) over RCCS skills."""
    t0 = time.perf_counter()
    from app.services.conversation_context import resolve_question_with_history

    if campus_query is None:
        q, resolved_context = resolve_question_with_history(question, history)
        from app.services.campus_intelligence.compiler import compile_campus_query

        campus_query = compile_campus_query(q)
    else:
        q = str(campus_query.original_query or question)
        resolved_context = dict(conversation_context or {})
        resolved_context.setdefault("original_question", question)
        resolved_context.setdefault("resolved_question", q)
    resolved_context["request_context"] = dict(request_context or {})

    # Outer QUERY_ANALYZING / RETRIEVAL_STARTED / RETRIEVAL_COMPLETED stay in ask.py
    # so the SSE shell is unchanged; we only emit mid-retrieval progress here.
    # Heartbeat before the sync Claude rewrite (runs in a worker thread).
    await _emit(
        on_activity,
        QUERY_REWRITTEN,
        {"mode": "supervisor_rccs", "status": "started"},
        message="Refining the search terms",
    )
    rewritten, rewrite_meta = await _rewrite(q, use_web_search=use_web_search)
    if (
        rewritten
        and rewrite_meta.get("rewritten")
        and str(rewrite_meta.get("original") or "").strip()
        != str(rewritten).strip()
    ):
        await _emit(
            on_activity,
            QUERY_REWRITTEN,
            {
                "mode": "supervisor_rccs",
                "provider": rewrite_meta.get("provider"),
                "status": "completed",
            },
            message="Clarified the search terms for better results",
        )

    classification = with_user_web_preference(
        classify_retrieval(rewritten, campus_query=campus_query),
        use_web_search,
    )
    await _emit(
        on_activity,
        QUERY_CLASSIFIED,
        {
            "mode": "supervisor_rccs",
            "primary_intent": getattr(classification, "primary_intent", None),
        },
        message="Choosing the right search path",
    )
    retrieval_plan = build_retrieval_plan(
        classification,
        use_web_search=use_web_search,
        question=rewritten,
        campus_query=campus_query,
    )
    for sq in rewrite_meta.get("subqueries") or []:
        if isinstance(sq, str) and sq and sq not in retrieval_plan.search_queries:
            retrieval_plan.search_queries.append(sq)

    skill_plan: SkillPlan = build_skill_plan(
        rewritten_question=rewritten,
        classification=classification,
        retrieval_plan=retrieval_plan,
        use_web_search=use_web_search,
    )

    ctx = SkillContext(
        question=q,
        rewritten=rewritten,
        use_web_search=use_web_search,
        classification=classification,
        retrieval_plan=retrieval_plan,
        history=history,
    )

    errors: dict[str, str] = {}
    activated: list[str] = []
    counts: dict[str, int] = {}
    latency: dict[str, int] = {}
    evidence: list[RetrievedEvidence] = []

    # Execute by parallel_group (retrieve skills together; agentic may be separate).
    groups: dict[str, list[SkillStep]] = defaultdict(list)
    order: list[str] = []
    for step in skill_plan.steps:
        if step.parallel_group not in groups:
            order.append(step.parallel_group)
        groups[step.parallel_group].append(step)

    for group_name in order:
        steps = groups[group_name]
        results = await asyncio.gather(
            *[
                _run_step(
                    step,
                    ctx,
                    errors=errors,
                    activated=activated,
                    counts=counts,
                    latency=latency,
                    on_activity=on_activity,
                )
                for step in steps
            ],
            return_exceptions=True,
        )
        for step, result in zip(steps, results):
            if isinstance(result, Exception):
                errors[step.skill_id] = str(result)
                continue
            evidence.extend(result)

        if evidence:
            await _emit(
                on_activity,
                RETRIEVAL_SOURCE_FOUND,
                {"sources_found": len(evidence)},
                message=(
                    f"Gathered {len(evidence)} useful source"
                    f"{'s' if len(evidence) != 1 else ''} so far"
                ),
            )

    # Reflect once; optional single retry.
    critique: Critique | None = None
    retried_skill: str | None = None
    if reflect_enabled():
        await _emit(
            on_activity,
            RERANKING_STARTED,
            {"mode": "reflect"},
            message="Checking whether we have enough good sources",
        )
        critique = await reflect(q, evidence, ctx)
        if critique.needs_more and critique.retry_skill:
            retry_id = route_retry_skill(critique.retry_skill, ctx)
            # Allow official fallback even if plan.use_official_live was false
            # (mirrors hybrid kb→official fallback) when hybrid is on.
            if (
                retry_id is None
                and critique.retry_skill == "official_web"
                and rccs_cfg.hybrid_enabled()
                and not ctx.use_web_search
            ):
                retry_id = "official_web"
            if retry_id:
                retried_skill = retry_id
                retry_step = SkillStep(
                    step_id="reflect_retry",
                    skill_id=retry_id,
                    query=critique.retry_query or rewritten,
                    reason=critique.reason or "reflection_retry",
                    parallel_group="retry",
                )
                # Temporarily widen plan for official fallback retry.
                if retry_id == "official_web" and not retrieval_plan.use_official_live:
                    retrieval_plan.use_official_live = True
                await _emit(
                    on_activity,
                    RETRIEVAL_STARTED,
                    {"mode": "reflect_retry", "skill": retry_id},
                    message="Searching again for a bit more detail…",
                )
                more = await _run_step(
                    retry_step,
                    ctx,
                    errors=errors,
                    activated=activated,
                    counts=counts,
                    latency=latency,
                    on_activity=on_activity,
                )
                evidence.extend(more)
                if more:
                    await _emit(
                        on_activity,
                        RETRIEVAL_SOURCE_FOUND,
                        {"sources_found": len(evidence)},
                        message=(
                            f"After a second look, we now have {len(evidence)} source"
                            f"{'s' if len(evidence) != 1 else ''}"
                        ),
                    )
        await _emit(
            on_activity,
            RERANKING_COMPLETED,
            {"status": "ok" if (critique and critique.ok) else "retry"},
            message=(
                "Sources look ready for an answer"
                if critique and critique.ok
                else "Finished the extra source check"
            ),
        )

    before = len(evidence)
    evidence = dedupe_evidence(evidence)
    entity_names = [e.normalized_name for e in classification.entities]
    evidence = rank_and_cap(
        evidence,
        entity_names=entity_names,
        freshness=retrieval_plan.freshness,
        companion_requested=bool(retrieval_plan.companion_source_ids),
    )
    for ev in evidence:
        ev.text = sanitize_evidence_text(ev.text)

    evidence_sufficiency: dict[str, Any] = {}
    precise_failure = ""
    if retrieval_plan.compiled_query:
        try:
            from app.services.campus_intelligence.evidence import evaluate_evidence
            from app.services.campus_intelligence.failures import render_precise_failure
            from app.services.campus_intelligence.route_policy import resolve_route_policy

            sufficiency = evaluate_evidence(
                campus_query,
                evidence,
                policy=resolve_route_policy(campus_query),
            )
            evidence_sufficiency = sufficiency.to_dict()
            accepted_ids = set(sufficiency.accepted_evidence_ids)
            evidence = [item for item in evidence if item.evidence_id in accepted_ids]
            if not sufficiency.passed:
                precise_failure = render_precise_failure(campus_query, sufficiency)
        except Exception as exc:
            errors["evidence_sufficiency"] = str(exc)

    total_ms = int((time.perf_counter() - t0) * 1000)

    safe_response = _build_safe_response(
        use_web_search=use_web_search,
        plan=retrieval_plan,
        activated=activated,
        counts=counts,
        errors=errors,
        evidence_n=len(evidence),
    )
    safe_response.update(
        {
            "request_context": dict(request_context or {}),
            "evidence_sufficiency": evidence_sufficiency,
            "precise_failure": precise_failure,
        }
    )
    meta: dict[str, Any] = {
        "activated_channels": list(activated),
        "matched_registry_source_ids": list(retrieval_plan.official_source_ids),
        "companion_source_ids": list(retrieval_plan.companion_source_ids),
        "rejected_domains": [],
        "result_count_by_channel": dict(counts),
        "retrieval_latency_by_channel": dict(latency),
        "fallbacks_used": ([f"reflect:{retried_skill}"] if retried_skill else []),
        "query_rewrite": rewrite_meta,
        "evidence_count_before_dedup": before,
        "evidence_count_after_dedup": len(evidence),
        "total_retrieval_latency": total_ms,
        "routing_reason": skill_plan.reason,
        "conversation_context": resolved_context,
        "evidence_sufficiency": evidence_sufficiency,
        "supervisor": {
            "enabled": True,
            "steps": [
                {"step_id": s.step_id, "skill_id": s.skill_id, "reason": s.reason}
                for s in skill_plan.steps
            ],
            "retried_skill": retried_skill,
            "critique": (
                {
                    "ok": critique.ok,
                    "needs_more": critique.needs_more,
                    "retry_skill": critique.retry_skill,
                    "reason": critique.reason,
                }
                if critique
                else None
            ),
        },
        "classification": {
            "primary_intent": classification.primary_intent,
            "freshness": classification.freshness,
            "use_companions": classification.use_companions,
            "companion_categories": classification.companion_categories,
            "entities": [
                {"name": e.normalized_name, "type": e.entity_type}
                for e in classification.entities
            ],
        },
        "safe_response": safe_response,
    }

    return HybridRetrievalResult(
        evidence=evidence,
        classification=classification,
        plan=retrieval_plan,
        metadata=meta,
        errors_by_channel=errors,
    )
