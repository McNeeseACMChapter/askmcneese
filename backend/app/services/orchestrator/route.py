"""Route a SkillStep to an allowed skill id under mode / policy constraints."""

from __future__ import annotations

from app.services.orchestrator.models import (
    KNOWN_SKILLS,
    SKILL_AGENTIC,
    SKILL_COMPANION,
    SKILL_KB,
    SKILL_OFFICIAL,
    SkillContext,
    SkillStep,
)


def route_step(step: SkillStep, ctx: SkillContext) -> str | None:
    """Return the skill id to execute, or None if the step is blocked.

    Routing is deterministic: the planner already chose skill_id; this gate
    enforces web-mode and plan constraints so a bad/LLM plan cannot open
    disallowed channels.
    """
    skill_id = (step.skill_id or "").strip()
    if skill_id not in KNOWN_SKILLS:
        return None

    plan = ctx.retrieval_plan

    if skill_id == SKILL_KB:
        return skill_id if plan.use_kb else None

    if skill_id == SKILL_OFFICIAL:
        return skill_id if plan.use_official_live else None

    if skill_id == SKILL_COMPANION:
        if not plan.companion_source_ids:
            return None
        return skill_id

    if skill_id == SKILL_AGENTIC:
        if not ctx.use_web_search or not plan.use_official_live:
            return None
        return skill_id

    return None


def route_retry_skill(skill_id: str | None, ctx: SkillContext) -> str | None:
    """Validate a reflection-suggested retry skill against the same policy gates."""
    if not skill_id:
        return None
    probe = SkillStep(
        step_id="retry",
        skill_id=skill_id,
        query=ctx.rewritten,
        reason="reflection_retry",
    )
    return route_step(probe, ctx)
