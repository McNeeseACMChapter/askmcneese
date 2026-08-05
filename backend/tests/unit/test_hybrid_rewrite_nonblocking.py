"""Ensure query rewrite does not block the event loop / SSE heartbeats."""

from __future__ import annotations

import asyncio
import time
import unittest
from unittest.mock import MagicMock, patch

from app.services.activity_events import QUERY_CLASSIFIED, QUERY_REWRITTEN
from app.services.query_rewrite import RewrittenQuery
from app.services.rccs.hybrid import hybrid_retrieve
from app.services.rccs.models import RetrievalClassification


def _slow_rewrite(question: str, *, use_web_search: bool = False) -> RewrittenQuery:
    time.sleep(0.25)
    return RewrittenQuery(
        original=question,
        rewritten=f"{question} (McNeese)",
        subqueries=[question],
        provider="test",
    )


class TestHybridRewriteNonBlocking(unittest.IsolatedAsyncioTestCase):
    async def test_rewrite_emits_refining_before_llm_and_keeps_loop_responsive(self) -> None:
        events: list[tuple[str, str | None]] = []

        async def on_activity(event, metadata=None, message=None):
            events.append((event, message))

        classification = RetrievalClassification(
            primary_intent="policy_or_procedure",
            secondary_intents=[],
            entities=[],
            freshness="any",
            use_kb=True,
            use_official_live=False,
            use_companions=False,
            companion_categories=[],
            registry_topics=[],
            routing_reason="test",
            confidence=0.9,
        )

        plan = MagicMock(
            use_kb=False,
            use_official_live=False,
            companion_source_ids=[],
            companion_categories=[],
            official_source_ids=[],
            search_queries=[],
            browse_social=False,
            freshness="any",
        )

        with (
            patch(
                "app.services.rccs.classify.looks_definitional",
                return_value=False,
            ),
            patch(
                "app.services.query_rewrite.should_rewrite_question",
                return_value=True,
            ),
            patch(
                "app.services.query_rewrite.rewrite_question",
                side_effect=_slow_rewrite,
            ),
            patch(
                "app.services.rccs.hybrid.classify_retrieval",
                return_value=classification,
            ),
            patch(
                "app.services.rccs.hybrid.with_user_web_preference",
                side_effect=lambda c, _w: c,
            ),
            patch(
                "app.services.rccs.hybrid.build_retrieval_plan",
                return_value=plan,
            ),
        ):
            tick = {"n": 0}

            async def _ticker():
                while tick["n"] < 3:
                    await asyncio.sleep(0.05)
                    tick["n"] += 1

            ticker_task = asyncio.create_task(_ticker())
            result = await hybrid_retrieve(
                "When is fall registration?",
                use_web_search=False,
                on_activity=on_activity,
            )
            await ticker_task

        self.assertGreaterEqual(tick["n"], 3)
        self.assertEqual(events[0][0], QUERY_REWRITTEN)
        self.assertEqual(events[0][1], "Refining the search terms")
        self.assertTrue(any(e[0] == QUERY_CLASSIFIED for e in events))
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
