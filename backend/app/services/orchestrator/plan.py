"""Build a SkillPlan from RCCS classification + RetrievalPlan."""

from __future__ import annotations

from app.services.orchestrator.models import (
    SKILL_AGENTIC,
    SKILL_COMPANION,
    SKILL_KB,
    SKILL_OFFICIAL,
    SkillPlan,
    SkillStep,
)
from app.services.rccs.models import RetrievalClassification, RetrievalPlan


def build_skill_plan(
    *,
    rewritten_question: str,
    classification: RetrievalClassification,
    retrieval_plan: RetrievalPlan,
    use_web_search: bool = False,
) -> SkillPlan:
    """Deterministic planner: map RCCS channels onto ordered parallel skill steps.

    No LLM planner — keeps allowlists and trust tiers under policy control.
    Steps in the same parallel_group may run concurrently.
    """
    q = (rewritten_question or "").strip()
    primary_q = (retrieval_plan.search_queries[0] if retrieval_plan.search_queries else q) or q
    steps: list[SkillStep] = []
    n = 0

    def _add(skill_id: str, query: str, reason: str, group: str = "retrieve") -> None:
        nonlocal n
        n += 1
        steps.append(
            SkillStep(
                step_id=f"s{n}",
                skill_id=skill_id,
                query=query,
                reason=reason,
                parallel_group=group,
            )
        )

    if retrieval_plan.use_kb:
        _add(SKILL_KB, primary_q, "RCCS plan requests knowledge-base channel")

    if retrieval_plan.use_official_live:
        _add(
            SKILL_OFFICIAL,
            primary_q,
            "RCCS plan requests official live / registry web channel",
        )

    if retrieval_plan.companion_source_ids:
        entity_q = (
            retrieval_plan.entity_queries[0]
            if retrieval_plan.entity_queries
            else primary_q
        )
        _add(
            SKILL_COMPANION,
            entity_q,
            f"Companions: {', '.join(retrieval_plan.companion_source_ids)}",
        )

    # Agentic only in explicit web mode with official live (same gate as hybrid.py).
    if use_web_search and retrieval_plan.use_official_live:
        _add(
            SKILL_AGENTIC,
            primary_q,
            "Web mode: Perplexity Sonar agentic research",
            group="agentic",
        )

    reason = retrieval_plan.reason or classification.routing_reason or "rccs_plan"
    if not steps:
        # Fail-soft: always attempt KB so ask.py still has a path.
        _add(SKILL_KB, primary_q or q or "McNeese", "Fallback KB step (empty RCCS plan)")
        reason = f"{reason}; empty_plan_fallback_kb"

    return SkillPlan(
        steps=steps,
        rewritten_question=rewritten_question,
        classification=classification,
        retrieval_plan=retrieval_plan,
        reason=reason,
    )
