"""Typed models for the thin RCCS supervisor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from app.services.rccs.models import (
    HybridRetrievalResult,
    RetrievedEvidence,
    RetrievalClassification,
    RetrievalPlan,
)

# SSE activity callback: event name must be a frozen activity_events key.
# Signature: on_activity(event, metadata=None, message=None)
# May be sync or async; supervisor awaits if needed.
OnActivity = Callable[..., Awaitable[None] | None]

SKILL_KB = "kb_retrieve"
SKILL_OFFICIAL = "official_web"
SKILL_COMPANION = "companion"
SKILL_AGENTIC = "agentic_web"

KNOWN_SKILLS = frozenset({SKILL_KB, SKILL_OFFICIAL, SKILL_COMPANION, SKILL_AGENTIC})


@dataclass
class SkillStep:
    """One planned retrieval action."""

    step_id: str
    skill_id: str
    query: str
    reason: str = ""
    parallel_group: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillPlan:
    """Ordered (or parallel-grouped) steps derived from RCCS RetrievalPlan."""

    steps: list[SkillStep]
    rewritten_question: str
    classification: RetrievalClassification
    retrieval_plan: RetrievalPlan
    reason: str = ""


@dataclass
class SkillContext:
    """Shared execution context passed to every skill."""

    question: str
    rewritten: str
    use_web_search: bool
    classification: RetrievalClassification
    retrieval_plan: RetrievalPlan
    history: list[dict[str, Any]] | None = None


@dataclass
class Critique:
    """Reflection result — at most one retry skill is honored by the supervisor."""

    ok: bool
    needs_more: bool = False
    retry_skill: str | None = None
    retry_query: str | None = None
    reason: str = ""
    coverage_notes: str = ""


class Skill(Protocol):
    """Base skill interface: execute(step) → evidence list."""

    skill_id: str

    async def execute(
        self,
        step: SkillStep,
        ctx: SkillContext,
    ) -> list[RetrievedEvidence]:
        ...


@dataclass
class SupervisorResult:
    """Supervisor output — same HybridRetrievalResult shape ask.py already consumes."""

    hybrid: HybridRetrievalResult
    skill_plan: SkillPlan
    critique: Critique | None = None
    retried_skill: str | None = None
