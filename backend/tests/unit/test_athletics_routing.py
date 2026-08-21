"""Registry-driven routing: whole seed registry + child leaves."""

from __future__ import annotations

import unittest

from app.services.query_expansion import expand_query
from app.services.rccs.classify import INTENT_ATHLETICS, classify_retrieval
from app.services.rccs.plan import build_retrieval_plan
from app.services.search_providers import _site_scoped_query
from app.services.source_registry import match_child_urls, match_registry


class TestRegistryDrivenRouting(unittest.TestCase):
    def test_football_matches_athletics_registry_source(self):
        q = "When is the next McNeese football game?"
        matched = match_registry(q, max_sources=3)
        self.assertIn("SRC-028", matched.source_ids)
        self.assertEqual(matched.source_ids[0], "SRC-028")
        self.assertTrue(any("mcneesesports.com" in d for d in matched.browse_domains))
        self.assertTrue(
            any("/sports/football/schedule" in u for u in matched.seed_urls),
            matched.seed_urls,
        )

    def test_housing_matches_reslife_registry_source(self):
        matched = match_registry("What are the McNeese residence hall floor plans?", max_sources=3)
        self.assertIn("SRC-036", matched.source_ids)
        self.assertEqual(matched.source_ids[0], "SRC-036")

    def test_bookstore_matches_cowboy_store(self):
        matched = match_registry("Where can I buy McNeese textbooks?", max_sources=3)
        self.assertTrue(
            any(sid in matched.source_ids for sid in ("SRC-035", "SRC-027")),
            matched.source_ids,
        )

    def test_plan_uses_registry_official_ids(self):
        q = "When is the next McNeese football game?"
        c = classify_retrieval(q)
        self.assertEqual(c.primary_intent, INTENT_ATHLETICS)
        plan = build_retrieval_plan(c, use_web_search=False, question=q)
        self.assertIn("SRC-028", plan.official_source_ids)
        self.assertTrue(any("mcneesesports.com" in d for d in plan.browse_domains))

    def test_football_when_does_not_expand_to_admissions_deadline(self):
        subs = expand_query("When is the next McNeese football game?")
        joined = " | ".join(subs).lower()
        self.assertNotIn("application deadline", joined)

    def test_child_url_picker(self):
        urls = match_child_urls(
            "When is the next McNeese football game?",
            ["SRC-028"],
            max_urls=3,
        )
        self.assertTrue(any("/sports/football/schedule" in u for u in urls))

    def test_serper_site_prefers_sports_domain(self):
        q = _site_scoped_query(
            "When is the next McNeese football game?",
            ["mcneese.edu", "mcneesesports.com", "mcneesereslife.com"],
        )
        self.assertTrue(q.startswith("site:mcneesesports.com "))


if __name__ == "__main__":
    unittest.main()
