"""Unit tests for search providers (mocked HTTP) and query decompose."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rccs.adapters import RateMyProfessorsAdapter
from app.services.rccs.decompose import decompose_question
from app.services.search_providers import ProviderHit, provider_status, search_web


class TestDecompose(unittest.TestCase):
    def test_faculty_ratings_compound(self):
        d = decompose_question(
            "Who is Dr Menon and what is his Rate My Professors rating and how many reviews?"
        )
        intents = {sq.intent for sq in d.subquestions}
        self.assertIn("faculty_identity", intents)
        self.assertIn("faculty_ratings", intents)
        self.assertTrue(any(sq.needs_companion_rating for sq in d.subquestions))


class TestProviderStatus(unittest.TestCase):
    def test_status_no_secrets(self):
        st = provider_status()
        blob = str(st).lower()
        self.assertNotIn("tvly-", blob)
        self.assertNotIn("pplx-", blob)
        self.assertIn("tavily_configured", st)
        self.assertIn("web_browsing_enabled", st)


class TestSearchWebCascade(unittest.IsolatedAsyncioTestCase):
    async def test_stops_after_first_paid_provider(self):
        hit = ProviderHit(
            url="https://www.mcneese.edu/admissions",
            title="Admissions",
            snippet="Transfer students",
            provider="tavily",
        )

        async def fake_tavily(*_a, **_k):
            return [hit]

        serper = AsyncMock(return_value=[])
        with (
            patch("app.services.search_providers._tavily_search", side_effect=fake_tavily),
            patch("app.services.search_providers._serper_search", serper),
            patch("app.services.search_providers._perplexity_search", AsyncMock(return_value=[])),
            patch("app.services.search_providers._ddg_search", AsyncMock(return_value=[])),
            patch("app.services.search_providers.web_browsing_enabled", return_value=True),
        ):
            out = await search_web(
                "McNeese admissions",
                max_results=3,
                include_domains=["mcneese.edu"],
                providers=["tavily", "serper", "perplexity", "ddg"],
            )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].provider, "tavily")
        serper.assert_not_awaited()


class TestRatingExtract(unittest.TestCase):
    def test_snippet_numbers(self):
        text = "Dr. Menon at McNeese — quality 4.2 / 5 · 18 ratings · difficulty 3.1"
        extracted = RateMyProfessorsAdapter._extract_rating_bits(text)
        self.assertIn("Verified fields:", extracted)
        self.assertIn("quality:", extracted)
        self.assertIn("ratings_count:", extracted)


if __name__ == "__main__":
    unittest.main()
