from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.conversation_context import (
    looks_like_followup,
    normalize_source_scope,
    resolve_question_with_history,
)
from app.services.rccs.hybrid import _compiled_live_discovery, _open_live_destination_pages
from app.services.rccs.models import RetrievalPlan, RetrievedEvidence, utcnow


class TestConversationContext(unittest.TestCase):
    def test_source_scopes_normalize(self):
        self.assertEqual(normalize_source_scope("adaptive", use_web_search=False), "adaptive")
        self.assertEqual(normalize_source_scope("knowledge", use_web_search=True), "knowledge")
        self.assertEqual(normalize_source_scope("web", use_web_search=False), "web")
        self.assertEqual(normalize_source_scope(None, use_web_search=True), "web")
        self.assertEqual(normalize_source_scope(None, use_web_search=False), "knowledge")

    def test_followup_resolution_uses_prior_user_question(self):
        history = [
            {"role": "user", "content": "How do I apply for McNeese campus housing?"},
            {"role": "assistant", "content": "Residence Life handles housing applications."},
        ]
        self.assertTrue(looks_like_followup("what about parking there?", history))
        resolved, meta = resolve_question_with_history("what about parking there?", history)
        self.assertTrue(meta["followup"])
        self.assertIn("housing", resolved.lower())
        self.assertIn("parking", resolved.lower())
        self.assertIn("continuing from", resolved.lower())

    def test_degree_400_level_followup_anchors_to_prior_major(self):
        history = [
            {
                "role": "user",
                "content": (
                    "how many credits do we have to complete for undergrad "
                    "computer science degree at mcneese?"
                ),
            },
            {
                "role": "assistant",
                "content": "Computer Science BS requires 120 total credit hours.",
            },
        ]
        question = "How man 400 level of course do I need to earn?"
        self.assertTrue(looks_like_followup(question, history))
        resolved, meta = resolve_question_with_history(question, history)
        self.assertTrue(meta["followup"])
        self.assertIn("computer science", resolved.lower())
        self.assertIn("how many", resolved.lower())
        self.assertIn("300/400", resolved)
        self.assertNotIn("\n", resolved)

    def test_sticky_topic_survives_intervening_turn(self):
        history = [
            {
                "role": "user",
                "content": "how many credits for the computer science degree?",
            },
            {
                "role": "assistant",
                "content": "Computer Science BS requires 120 credit hours.",
            },
            {
                "role": "user",
                "content": "what about parking on campus?",
            },
            {
                "role": "assistant",
                "content": "Parking Services handles permits.",
            },
        ]
        # Curriculum cue after a mixed thread should still latch to CS when asked.
        question = "how many 400 level courses do I need?"
        self.assertTrue(looks_like_followup(question, history))
        resolved, meta = resolve_question_with_history(question, history)
        self.assertTrue(meta["followup"])
        self.assertIn("computer science", resolved.lower())


class TestPageReadCommander(unittest.IsolatedAsyncioTestCase):
    async def test_open_live_destination_pages_reads_urls(self):
        plan = RetrievalPlan(
            use_kb=True,
            use_official_live=True,
            companion_source_ids=[],
            official_source_ids=[],
            search_queries=["housing"],
            entity_queries=[],
            freshness="current",
            max_results_per_channel=4,
            reason="test",
            allow_open_web=True,
            max_pages_to_open=3,
            compiled_query={
                "domain": "student_services",
                "freshness": "live",
                "answer_shape": "precise_partial",
                "requires_live_discovery": True,
                "source_scope": "adaptive",
                "category": "Campus Housing and Residential Life",
                "planned_queries": [
                    {
                        "query_id": "MSQ-1",
                        "query": "McNeese campus housing apply",
                        "source_mode": "official_first",
                        "preferred_domains": ["mcneesereslife.com"],
                    }
                ],
            },
        )
        fake_page = RetrievedEvidence(
            evidence_id="ev-page-1",
            title="Residence Life",
            url="https://mcneesereslife.com/",
            text="Apply for housing online. Rates start at $example.",
            source_id="PAGE",
            source_name="Residence Life",
            source_tier="A",
            trust_level="official",
            category="live_discovery",
            retrieval_channel="official_live",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=0.9,
            metadata={},
        )
        with patch(
            "app.services.rccs.page_open_agent.open_and_scrape_urls",
            new=AsyncMock(return_value=[fake_page]),
        ):
            opened = await _open_live_destination_pages(
                "how to apply for McNeese campus housing",
                plan,
                hits=["https://mcneesereslife.com/"],
                evidence_category="precise_partial",
            )
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0].metadata.get("page_read"))
        self.assertFalse(opened[0].is_link_only)

    def test_live_discovery_flag_from_compiled_query(self):
        plan = RetrievalPlan(
            use_kb=False,
            use_official_live=True,
            companion_source_ids=[],
            official_source_ids=[],
            search_queries=[],
            entity_queries=[],
            freshness="current",
            max_results_per_channel=2,
            reason="t",
            compiled_query={"requires_live_discovery": True, "domain": "employment", "freshness": "live", "answer_shape": "job_list"},
        )
        self.assertTrue(_compiled_live_discovery(plan))


if __name__ == "__main__":
    unittest.main()
