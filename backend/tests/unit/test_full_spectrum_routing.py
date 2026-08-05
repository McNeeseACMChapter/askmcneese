from __future__ import annotations

import unittest

from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.full_spectrum import (
    corpus_available,
    load_taxonomy_categories,
    match_taxonomy,
    pack_available,
    plan_corpus_queries,
    requires_live_discovery,
)
from app.services.rccs.hybrid import _compiled_live_discovery, _planned_search_phrases
from app.services.rccs.models import RetrievalPlan


class TestFullSpectrumRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pack_available():
            raise unittest.SkipTest("full-spectrum research pack is not installed")

    def test_taxonomy_covers_university_breadth(self):
        categories = load_taxonomy_categories()
        self.assertGreaterEqual(len(categories), 100)
        parents = {item.parent_domain for item in categories.values()}
        self.assertIn("Careers and Employment", parents)
        self.assertIn("Health and Wellness", parents)
        self.assertIn("Housing and Dining", parents)
        self.assertIn("Admissions and Enrollment", parents)
        self.assertIn("Athletics and Recreation", parents)

    def test_taxonomy_match_is_not_jobs_only(self):
        cases = {
            "how to apply for McNeese campus housing": "housing",
            "McNeese counseling center appointment": "counsel",
            "McNeese meal plan cost fall 2026": "dining",
            "McNeese athletics tickets": "athlet",
            "FAFSA requirements for McNeese students": "financial",
            "parking permit McNeese official": "police",
        }
        for question, needle in cases.items():
            match = match_taxonomy(question)
            self.assertIsNotNone(match, question)
            blob = f"{match.category} {match.parent_domain}".lower()
            self.assertIn(needle, blob, question)

    def test_compiler_attaches_category_and_planned_queries_beyond_jobs(self):
        compiled = compile_campus_query("how to apply for McNeese campus housing")
        self.assertEqual(compiled.domain, "student_services")
        self.assertTrue(compiled.category_id)
        self.assertTrue(compiled.planned_queries)
        self.assertTrue(compiled.preferred_domains)
        self.assertIn("mcneese.edu", " ".join(compiled.preferred_domains).lower())

    def test_employment_still_live(self):
        compiled = compile_campus_query("What are the jobs available to students?")
        self.assertEqual(compiled.domain, "employment")
        self.assertTrue(compiled.requires_live_discovery)
        self.assertTrue(compiled.planned_queries or compiled.freshness == "live")

    def test_live_discovery_applies_to_events_and_safety(self):
        housing = compile_campus_query("McNeese campus housing availability")
        self.assertTrue(
            housing.requires_live_discovery
            or requires_live_discovery(
                domain=housing.domain,
                freshness=housing.freshness,
                freshness_class=housing.freshness_class,
                answer_shape=housing.answer_shape,
            )
        )
        emergency = compile_campus_query("McNeese emergency closure latest update")
        self.assertTrue(emergency.category_id or emergency.domain in {"safety", "general_campus", "events"})
        self.assertTrue(
            emergency.requires_live_discovery
            or emergency.freshness in {"live", "current"}
            or (emergency.freshness_class or "") in {"hourly", "daily"}
        )

    def test_query_planner_returns_corpus_phrases(self):
        match = match_taxonomy("McNeese transfer admission requirements 2026")
        self.assertIsNotNone(match)
        planned = plan_corpus_queries(
            category_id=match.category_id,
            campus_intent="check_requirements",
            question="McNeese transfer admission requirements 2026",
            limit=4,
        )
        self.assertTrue(planned)
        self.assertTrue(all(item.query for item in planned))
        if corpus_available():
            self.assertTrue(any(not item.query_id.startswith("synth-") for item in planned))
        else:
            self.assertTrue(all(item.query_id.startswith("synth-") for item in planned))

    def test_hybrid_uses_planned_phrases_for_non_job_live_domains(self):
        compiled = compile_campus_query("Banners Cultural Series tickets Lake Charles")
        plan = RetrievalPlan(
            use_kb=True,
            use_official_live=True,
            companion_source_ids=[],
            official_source_ids=[],
            search_queries=[],
            entity_queries=[],
            freshness="current",
            max_results_per_channel=4,
            reason="test",
            primary_intent="campus_services",
            allow_agentic_web=True,
            compiled_query=compiled.to_dict(),
        )
        self.assertTrue(_compiled_live_discovery(plan))
        phrases = _planned_search_phrases(compiled.original_query, plan)
        self.assertGreaterEqual(len(phrases), 1)
        joined = " ".join(query for query, _domains, _mode in phrases).lower()
        self.assertTrue("banner" in joined or "mcneese" in joined)


if __name__ == "__main__":
    unittest.main()
