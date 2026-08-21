"""Reflection / refinement gate after skill execution.

Heuristic by default; optional Claude critique when SUPERVISOR_REFLECT_LLM=1.
Honors at most one retry skill suggestion (supervisor enforces single pass).
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.services.orchestrator.config import reflect_llm_enabled
from app.services.orchestrator.models import (
    SKILL_AGENTIC,
    SKILL_COMPANION,
    SKILL_KB,
    SKILL_OFFICIAL,
    Critique,
    SkillContext,
)
from app.services.rccs import config as rccs_cfg
from app.services.rccs.models import RetrievedEvidence


def _channel_counts(evidence: list[RetrievedEvidence]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ev in evidence:
        ch = ev.retrieval_channel or "unknown"
        counts[ch] = counts.get(ch, 0) + 1
    return counts


def _heuristic_critique(
    question: str,
    evidence: list[RetrievedEvidence],
    ctx: SkillContext,
) -> Critique:
    counts = _channel_counts(evidence)
    kb_n = counts.get("kb", 0)
    official_n = counts.get("official_live", 0)
    companion_n = counts.get("companion", 0)
    agentic_n = counts.get("agentic", 0)
    total = len(evidence)
    plan = ctx.retrieval_plan

    if total == 0:
        if plan.use_official_live and official_n == 0:
            return Critique(
                ok=False,
                needs_more=True,
                retry_skill=SKILL_OFFICIAL if not ctx.use_web_search else SKILL_AGENTIC,
                retry_query=ctx.rewritten or question,
                reason="no_evidence",
                coverage_notes="No evidence returned from planned channels.",
            )
        if plan.use_kb:
            return Critique(
                ok=False,
                needs_more=True,
                retry_skill=SKILL_OFFICIAL if rccs_cfg.hybrid_enabled() else SKILL_KB,
                retry_query=ctx.rewritten or question,
                reason="no_evidence",
                coverage_notes="Empty retrieval; attempting fallback channel.",
            )
        return Critique(
            ok=False,
            needs_more=False,
            reason="no_evidence_no_retry",
            coverage_notes="No evidence and no safe retry channel.",
        )

    # Knowledge mode: thin KB → one official live retry (mirrors hybrid fallback).
    if (
        not ctx.use_web_search
        and plan.use_kb
        and kb_n < rccs_cfg.kb_min_results()
        and official_n == 0
        and rccs_cfg.hybrid_enabled()
    ):
        return Critique(
            ok=False,
            needs_more=True,
            retry_skill=SKILL_OFFICIAL,
            retry_query=ctx.rewritten or question,
            reason="kb_insufficient",
            coverage_notes=f"KB returned {kb_n} item(s); retry official live.",
        )

    # Web mode: official empty but agentic not yet run / empty → try agentic once.
    if (
        ctx.use_web_search
        and plan.use_official_live
        and official_n == 0
        and agentic_n == 0
    ):
        return Critique(
            ok=False,
            needs_more=True,
            retry_skill=SKILL_AGENTIC,
            retry_query=ctx.rewritten or question,
            reason="official_empty_try_agentic",
            coverage_notes="Official live empty; retry agentic web.",
        )

    # Faculty/companion requested but missing companion evidence.
    if plan.companion_source_ids and companion_n == 0 and total < 2:
        return Critique(
            ok=False,
            needs_more=True,
            retry_skill=SKILL_COMPANION,
            retry_query=(
                plan.entity_queries[0]
                if plan.entity_queries
                else (ctx.rewritten or question)
            ),
            reason="companion_missing",
            coverage_notes="Companion sources planned but returned nothing.",
        )

    return Critique(
        ok=True,
        needs_more=False,
        reason="sufficient",
        coverage_notes=(
            f"channels={counts} total={total} "
            f"intent={ctx.classification.primary_intent}"
        ),
    )


def _parse_llm_critique(raw: str, fallback: Critique) -> Critique:
    text = (raw or "").strip()
    if not text:
        return fallback
    # Prefer fenced or raw JSON object
    match = re.search(r"\{[^{}]*\}", text, flags=re.DOTALL)
    if not match:
        return fallback
    try:
        data: dict[str, Any] = json.loads(match.group(0))
    except json.JSONDecodeError:
        return fallback

    needs_more = bool(data.get("needs_more"))
    retry = data.get("retry_skill")
    if retry is not None:
        retry = str(retry).strip() or None
    if retry not in {
        None,
        SKILL_KB,
        SKILL_OFFICIAL,
        SKILL_COMPANION,
        SKILL_AGENTIC,
    }:
        retry = fallback.retry_skill if needs_more else None

    return Critique(
        ok=not needs_more and bool(data.get("ok", not needs_more)),
        needs_more=needs_more,
        retry_skill=retry if needs_more else None,
        retry_query=(str(data["retry_query"]).strip() if data.get("retry_query") else None)
        or fallback.retry_query,
        reason=str(data.get("reason") or "llm_critique"),
        coverage_notes=str(data.get("coverage_notes") or fallback.coverage_notes),
    )


def _llm_critique(
    question: str,
    evidence: list[RetrievedEvidence],
    ctx: SkillContext,
    heuristic: Critique,
) -> Critique:
    try:
        from app.services.llm import CLAUDE_MODEL, _extract_text_blocks, _get_client
    except Exception:
        return heuristic

    summaries = []
    for ev in evidence[:8]:
        summaries.append(
            {
                "channel": ev.retrieval_channel,
                "tier": ev.source_tier,
                "title": (ev.title or "")[:120],
                "snippet": (ev.text or "")[:180],
            }
        )
    prompt = (
        "You are a retrieval quality checker for AskMcNeese (campus Q&A).\n"
        "Decide if the evidence is enough to answer the user, or if ONE extra "
        "retrieval skill should run.\n"
        "Allowed retry_skill values: kb_retrieve, official_web, companion, agentic_web, or null.\n"
        "Never suggest open-web or unrestricted browsing. Prefer official_web over agentic_web "
        "unless web mode is on and official is empty.\n"
        "Return ONLY compact JSON:\n"
        '{"ok":bool,"needs_more":bool,"retry_skill":string|null,'
        '"retry_query":string|null,"reason":string,"coverage_notes":string}\n\n'
        f"use_web_search={ctx.use_web_search}\n"
        f"primary_intent={ctx.classification.primary_intent}\n"
        f"planned_channels="
        f"kb={ctx.retrieval_plan.use_kb},"
        f"official={ctx.retrieval_plan.use_official_live},"
        f"companions={bool(ctx.retrieval_plan.companion_source_ids)}\n"
        f"Question: {question}\n"
        f"Evidence summaries: {json.dumps(summaries)}\n"
        f"Heuristic hint: {heuristic.reason} / {heuristic.coverage_notes}"
    )
    try:
        client = _get_client()
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _extract_text_blocks(list(resp.content or []))
        return _parse_llm_critique(raw, heuristic)
    except Exception:
        return heuristic


async def reflect(
    question: str,
    evidence: list[RetrievedEvidence],
    ctx: SkillContext,
) -> Critique:
    """Review raw evidence for coverage; optionally refine via Claude."""
    heuristic = _heuristic_critique(question, evidence, ctx)
    if reflect_llm_enabled():
        return _llm_critique(question, evidence, ctx, heuristic)
    return heuristic
