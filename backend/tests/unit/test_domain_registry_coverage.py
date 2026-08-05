"""Coverage and routing tests for the governed McNeese web ecosystem."""

from __future__ import annotations

import unittest

from app.services.domain_registry import (
    domains_for_question,
    official_domains,
    record_for_url,
    trust_tier_for_url,
)
from app.services.rccs.allowlist import is_allowed_url
from app.services.retrieval import _domain_relevance_adjustment
from app.services.source_registry import load_registry, match_registry


class TestDomainRegistryCoverage(unittest.TestCase):
    def test_affiliated_public_domains_are_governed(self) -> None:
        domains = set(official_domains())
        self.assertIn("mcneesedining.sodexomyway.com", domains)
        self.assertIn("mcneesefoundation.org", domains)
        self.assertIn("mcneesealumni.com", domains)
        self.assertIn("app.suitable.co", domains)

    def test_unreviewed_partner_remains_blocked(self) -> None:
        self.assertIsNone(record_for_url("https://www2.lsbdc.org/mcneese"))
        self.assertFalse(
            is_allowed_url("https://www2.lsbdc.org/mcneese", channel="official_live")
        )

    def test_affiliate_tier_is_preserved(self) -> None:
        self.assertEqual(trust_tier_for_url("https://mcneesefoundation.org/about/"), "B")
        self.assertEqual(trust_tier_for_url("https://catalog.mcneese.edu/"), "A")

    def test_question_domains_are_intent_ordered(self) -> None:
        self.assertEqual(
            domains_for_question("What are the McNeese dining hours?")[0],
            "mcneesedining.sodexomyway.com",
        )
        self.assertEqual(
            domains_for_question("When is the next football game?")[0],
            "mcneesesports.com",
        )

    def test_merged_registry_is_loaded_not_seed_only(self) -> None:
        sources = load_registry()
        self.assertGreater(len(sources), 500)
        self.assertGreater(
            sum(1 for source in sources if "catalog.mcneese.edu" in source.url),
            200,
        )

    def test_mechanical_degree_routes_to_specific_catalog_program(self) -> None:
        match = match_registry(
            "what courses complete the whole mechanical engineering degree",
            max_sources=4,
        )
        self.assertIn("Mechanical Engineering", match.sources[0].name)
        self.assertIn("preview_program.php", match.sources[0].url)

    def test_domain_prior_prefers_authoritative_intent_channel(self) -> None:
        question = "When is the next McNeese football game?"
        sports = _domain_relevance_adjustment(
            question, "https://mcneesesports.com/sports/football/schedule"
        )
        store = _domain_relevance_adjustment(
            question, "https://mcneesecowboystore.com/HOME"
        )
        self.assertGreater(sports, store)
    def test_semester_question_cannot_route_to_summer_sports_camp(self) -> None:
        match = match_registry("when is summer semester 2026 ending?", max_sources=3)
        self.assertEqual(match.source_ids[0], "SRC-012")
        self.assertFalse(any("mcneesesports.com" in url for url in match.seed_urls))


    def test_exact_policy_leaf_outranks_generic_housing_hub(self) -> None:
        match = match_registry(
            "What is the process for getting an emotional support animal in campus housing?",
            max_sources=5,
        )
        self.assertIn("emotional-support-animals", match.sources[0].url)

if __name__ == "__main__":
    unittest.main()
