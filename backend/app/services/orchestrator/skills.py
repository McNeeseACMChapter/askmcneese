"""Typed skill wrappers around existing RCCS retrieval channels."""

from __future__ import annotations

from app.services.orchestrator.models import (
    SKILL_AGENTIC,
    SKILL_COMPANION,
    SKILL_KB,
    SKILL_OFFICIAL,
    SkillContext,
    SkillStep,
)
from app.services.rccs import config as rccs_cfg
from app.services.rccs.hybrid import (
    retrieve_agentic_channel,
    retrieve_companions_channel,
    retrieve_kb_channel,
    retrieve_official_channel,
)
from app.services.rccs.models import RetrievedEvidence


class KbRetrieveSkill:
    skill_id = SKILL_KB

    async def execute(
        self,
        step: SkillStep,
        ctx: SkillContext,
    ) -> list[RetrievedEvidence]:
        items, _err = await retrieve_kb_channel(
            step.query or ctx.rewritten,
            rccs_cfg.max_kb_results(),
        )
        return list(items or [])


class OfficialWebSkill:
    skill_id = SKILL_OFFICIAL

    async def execute(
        self,
        step: SkillStep,
        ctx: SkillContext,
    ) -> list[RetrievedEvidence]:
        items, _err = await retrieve_official_channel(
            step.query or ctx.rewritten,
            ctx.retrieval_plan,
            rccs_cfg.max_official_results(),
        )
        return list(items or [])


class CompanionSkill:
    skill_id = SKILL_COMPANION

    async def execute(
        self,
        step: SkillStep,
        ctx: SkillContext,
    ) -> list[RetrievedEvidence]:
        if not ctx.retrieval_plan.companion_source_ids:
            return []
        items, _err = await retrieve_companions_channel(
            step.query or ctx.rewritten,
            ctx.retrieval_plan,
            ctx.classification.entities,
        )
        return list(items or [])


class AgenticWebSkill:
    skill_id = SKILL_AGENTIC

    async def execute(
        self,
        step: SkillStep,
        ctx: SkillContext,
    ) -> list[RetrievedEvidence]:
        items, _err = await retrieve_agentic_channel(
            step.query or ctx.rewritten,
            ctx.retrieval_plan,
            use_web_search=ctx.use_web_search,
        )
        return list(items or [])


SKILLS: dict[str, KbRetrieveSkill | OfficialWebSkill | CompanionSkill | AgenticWebSkill] = {
    SKILL_KB: KbRetrieveSkill(),
    SKILL_OFFICIAL: OfficialWebSkill(),
    SKILL_COMPANION: CompanionSkill(),
    SKILL_AGENTIC: AgenticWebSkill(),
}


async def execute_skill(
    skill_id: str,
    step: SkillStep,
    ctx: SkillContext,
) -> list[RetrievedEvidence]:
    skill = SKILLS.get(skill_id)
    if skill is None:
        return []
    return await skill.execute(step, ctx)
