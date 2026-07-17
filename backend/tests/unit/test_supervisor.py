"""Unit tests for the thin RCCS supervisor (plan / route / reflect / dispatch)."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.services.orchestrator.models import (
    SKILL_AGENTIC,
    SKILL_COMPANION,
    SKILL_KB,
    SKILL_OFFICIAL,
    SkillContext,
    SkillStep,
)
from app.services.orchestrator.plan import build_skill_plan
from app.services.orchestrator.route import route_retry_skill, route_step
from app.services.orchestrator.reflect import _heuristic_critique
from app.services.rccs.classify import classify_retrieval, with_user_web_preference
from app.services.rccs.models import (
    DetectedEntity,
    RetrievedEvidence,
    RetrievalClassification,
    RetrievalPlan,
    utcnow,
)
from app.services.rccs.plan import build_retrieval_plan


def _ctx(
    *,
    use_web_search: bool = False,
    use_kb: bool = True,
    use_official: bool = False,
    companions: list[str] | None = None,
) -> SkillContext:
    classification = RetrievalClassification(
        primary_intent="admissions_policy",
        secondary_intents=[],
        entities=[],
        freshness="stable",
        use_kb=use_kb,
        use_official_live=use_official,
        use_companions=bool(companions),
        companion_categories=[],
        registry_topics=[],
        routing_reason="test",
        confidence=0.9,
    )
    plan = RetrievalPlan(
        use_kb=use_kb,
        use_official_live=use_official,
        companion_source_ids=list(companions or []),
        official_source_ids=[],
        search_queries=["tuition deadline McNeese"],
        entity_queries=[],
        freshness="stable",
        max_results_per_channel=5,
        reason="test",
        companion_categories=[],
        primary_intent="admissions_policy",
    )
    return SkillContext(
        question="What is the tuition deadline?",
        rewritten="McNeese tuition deadline",
        use_web_search=use_web_search,
        classification=classification,
        retrieval_plan=plan,
    )


def _ev(channel: str, *, text: str = "x") -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=f"ev-{channel}",
        title="t",
        url="https://www.mcneese.edu/",
        text=text,
        source_id="TEST",
        source_name="Test",
        source_tier="A",
        trust_level="official",
        category="test",
        retrieval_channel=channel,
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.8,
    )


class TestSkillPlan(unittest.TestCase):
    def test_knowledge_plan_kb_only(self):
        c = classify_retrieval("What is the tuition deadline?")
        c = with_user_web_preference(c, False)
        plan = build_retrieval_plan(c, use_web_search=False, question="What is the tuition deadline?")
        skill_plan = build_skill_plan(
            rewritten_question="tuition deadline",
            classification=c,
            retrieval_plan=plan,
            use_web_search=False,
        )
        ids = [s.skill_id for s in skill_plan.steps]
        self.assertIn(SKILL_KB, ids)
        self.assertNotIn(SKILL_AGENTIC, ids)

    def test_web_plan_includes_official_and_agentic(self):
        c = classify_retrieval("What is the tuition deadline?")
        c = with_user_web_preference(c, True)
        plan = build_retrieval_plan(c, use_web_search=True, question="What is the tuition deadline?")
        skill_plan = build_skill_plan(
            rewritten_question="tuition deadline",
            classification=c,
            retrieval_plan=plan,
            use_web_search=True,
        )
        ids = [s.skill_id for s in skill_plan.steps]
        self.assertIn(SKILL_OFFICIAL, ids)
        self.assertIn(SKILL_AGENTIC, ids)


class TestRoute(unittest.TestCase):
    def test_blocks_agentic_in_knowledge_mode(self):
        ctx = _ctx(use_web_search=False, use_official=True)
        step = SkillStep(step_id="1", skill_id=SKILL_AGENTIC, query="q")
        self.assertIsNone(route_step(step, ctx))

    def test_allows_agentic_in_web_mode(self):
        ctx = _ctx(use_web_search=True, use_official=True)
        step = SkillStep(step_id="1", skill_id=SKILL_AGENTIC, query="q")
        self.assertEqual(route_step(step, ctx), SKILL_AGENTIC)

    def test_blocks_unknown_skill(self):
        ctx = _ctx()
        step = SkillStep(step_id="1", skill_id="open_web", query="q")
        self.assertIsNone(route_step(step, ctx))

    def test_retry_route_respects_policy(self):
        ctx = _ctx(use_web_search=False, use_official=False)
        self.assertIsNone(route_retry_skill(SKILL_AGENTIC, ctx))


class TestReflectHeuristic(unittest.TestCase):
    def test_empty_evidence_requests_retry(self):
        ctx = _ctx(use_kb=True, use_official=False)
        critique = _heuristic_critique(ctx.question, [], ctx)
        self.assertTrue(critique.needs_more)
        self.assertIsNotNone(critique.retry_skill)

    def test_sufficient_evidence_ok(self):
        ctx = _ctx(use_kb=True)
        critique = _heuristic_critique(ctx.question, [_ev("kb")], ctx)
        self.assertTrue(critique.ok)
        self.assertFalse(critique.needs_more)


class TestSupervisorDispatch(unittest.TestCase):
    def test_run_rccs_retrieval_uses_supervisor_when_flagged(self):
        from app.services.rccs.ask_integration import run_rccs_retrieval
        from app.services.rccs.models import HybridRetrievalResult

        fake = HybridRetrievalResult(
            evidence=[],
            classification=_ctx().classification,
            plan=_ctx().retrieval_plan,
            metadata={"supervisor": {"enabled": True}},
        )

        async def _main():
            with patch(
                "app.services.rccs.ask_integration.supervisor_enabled",
                return_value=True,
            ), patch(
                "app.services.orchestrator.supervisor.run",
                new_callable=AsyncMock,
                return_value=fake,
            ) as mocked:
                result = await run_rccs_retrieval("hello", use_web_search=False)
                mocked.assert_awaited_once()
                self.assertTrue((result.metadata.get("supervisor") or {}).get("enabled"))

        asyncio.run(_main())

    def test_run_rccs_retrieval_uses_hybrid_when_off(self):
        from app.services.rccs.ask_integration import run_rccs_retrieval
        from app.services.rccs.models import HybridRetrievalResult

        fake = HybridRetrievalResult(
            evidence=[],
            classification=_ctx().classification,
            plan=_ctx().retrieval_plan,
            metadata={"supervisor": False},
        )

        async def _main():
            with patch(
                "app.services.rccs.ask_integration.supervisor_enabled",
                return_value=False,
            ), patch(
                "app.services.rccs.ask_integration.hybrid_retrieve",
                new_callable=AsyncMock,
                return_value=fake,
            ) as mocked:
                await run_rccs_retrieval("hello", use_web_search=False)
                mocked.assert_awaited_once()

        asyncio.run(_main())


if __name__ == "__main__":
    unittest.main()
