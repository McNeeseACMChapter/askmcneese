"""Classification tests for RCCS — broad intents, not org-specific hardcodes."""

from __future__ import annotations

import unittest

from app.services.rccs.classify import (
    INTENT_ADMISSIONS_POLICY,
    INTENT_ATHLETICS,
    INTENT_FACULTY_IDENTITY,
    INTENT_FACULTY_RATINGS,
    INTENT_ORG_ACTIVITY,
    INTENT_ORG_IDENTITY,
    INTENT_SOCIAL_PROFILE,
    INTENT_CAMPUS_SERVICES,
    INTENT_ACADEMIC_PROGRAMS,
    INTENT_TERM_DEFINITION,
    classify_retrieval,
    with_user_web_preference,
)
from app.services.rccs.plan import build_retrieval_plan


class TestRetrievalClassification(unittest.TestCase):
    def test_faculty_identity_no_rmp(self):
        c = classify_retrieval("Who is Dr Menon?")
        self.assertEqual(c.primary_intent, INTENT_FACULTY_IDENTITY)
        self.assertTrue(c.use_kb)
        self.assertTrue(c.use_official_live)
        self.assertFalse(c.use_companions)
        self.assertEqual(c.companion_categories, [])
        self.assertTrue(any(e.entity_type == "faculty_or_staff" for e in c.entities))
        self.assertIn("Menon", c.entities[0].normalized_name)

    def test_faculty_ratings_enables_companion_category(self):
        c = classify_retrieval("What do students say about Dr Menon?")
        self.assertEqual(c.primary_intent, INTENT_FACULTY_RATINGS)
        self.assertTrue(c.use_companions)
        self.assertIn("student_rating", c.companion_categories)
        self.assertTrue(c.use_official_live)

    def test_rate_professor(self):
        c = classify_retrieval("Rate Dr Menon.")
        self.assertEqual(c.primary_intent, INTENT_FACULTY_RATINGS)
        self.assertIn("student_rating", c.companion_categories)

    def test_org_identity_generic(self):
        c = classify_retrieval("What is NSA at McNeese?")
        self.assertEqual(c.primary_intent, INTENT_ORG_IDENTITY)
        self.assertTrue(c.use_official_live)
        self.assertTrue(any(e.entity_type == "campus_organization" for e in c.entities))

    def test_org_activity_freshness(self):
        c = classify_retrieval("What is going on with NSA?")
        self.assertEqual(c.primary_intent, INTENT_ORG_ACTIVITY)
        self.assertEqual(c.freshness, "current")
        self.assertTrue(c.use_official_live)
        self.assertIn("social", c.companion_categories)

    def test_lowercase_acm_organization_entity(self):
        c = classify_retrieval(
            "what is going on mcneese state university acm organization. updated events list only"
        )
        self.assertEqual(c.primary_intent, INTENT_ORG_ACTIVITY)
        self.assertTrue(
            any(
                e.entity_type == "campus_organization" and e.normalized_name.upper() == "ACM"
                for e in c.entities
            )
        )

    def test_assistant_professor_means_is_definition_not_faculty(self):
        q = "what is assistant professor means?"
        c = classify_retrieval(q)
        self.assertEqual(c.primary_intent, INTENT_TERM_DEFINITION)
        self.assertFalse(c.use_companions)
        self.assertFalse(c.use_official_live)
        self.assertFalse(any(e.entity_type == "faculty_or_staff" for e in c.entities))
        cw = with_user_web_preference(c, True)
        self.assertFalse(cw.use_official_live)
        plan = build_retrieval_plan(cw, use_web_search=True, question=q)
        self.assertEqual(plan.companion_source_ids, [])
        self.assertFalse(plan.use_official_live)

    def test_social_profile(self):
        c = classify_retrieval("Does NSA have an Instagram?")
        self.assertEqual(c.primary_intent, INTENT_SOCIAL_PROFILE)
        self.assertIn("social", c.companion_categories)

    def test_clubs_available(self):
        c = classify_retrieval("What clubs are available at McNeese?")
        self.assertEqual(c.primary_intent, INTENT_ORG_IDENTITY)
        self.assertFalse(c.use_companions and "student_rating" in c.companion_categories)

    def test_tuition_no_companions(self):
        c = classify_retrieval("What is the tuition deadline?")
        self.assertEqual(c.primary_intent, INTENT_ADMISSIONS_POLICY)
        self.assertFalse(c.use_companions)
        self.assertEqual(c.companion_categories, [])

    def test_library_hours_today(self):
        c = classify_retrieval("What are the library hours today?")
        self.assertEqual(c.primary_intent, INTENT_CAMPUS_SERVICES)
        self.assertEqual(c.freshness, "current")
        self.assertTrue(c.use_official_live)
        self.assertFalse(c.use_companions)

    def test_computer_science_program(self):
        c = classify_retrieval("Tell me about computer science.")
        self.assertEqual(c.primary_intent, INTENT_ACADEMIC_PROGRAMS)
        self.assertTrue(c.use_kb)
        self.assertFalse(c.use_companions)

    def test_plan_faculty_identity_strips_companions_in_knowledge_mode(self):
        c = classify_retrieval("Who is Professor Smith?")
        plan = build_retrieval_plan(c, use_web_search=False, question="Who is Professor Smith?")
        self.assertEqual(plan.companion_source_ids, [])
        self.assertEqual(plan.companion_categories, [])

    def test_plan_faculty_ratings_includes_rmp_category_when_flags_on(self):
        from unittest.mock import patch

        c = classify_retrieval("What do students say about Dr Menon?")
        with patch("app.services.rccs.plan.cfg.companions_enabled", return_value=True), patch(
            "app.services.rccs.plan.cfg.rmp_enabled", return_value=True
        ):
            plan = build_retrieval_plan(
                c, use_web_search=False, question="What do students say about Dr Menon?"
            )
        self.assertIn("student_rating", plan.companion_categories)
        self.assertIn("SRC-C-RMP-001", plan.companion_source_ids)

    def test_web_mode_faculty_identity_adds_rmp(self):
        from unittest.mock import patch

        c = classify_retrieval("Who is Dr Menon?")
        with patch("app.services.rccs.plan.cfg.companions_enabled", return_value=True), patch(
            "app.services.rccs.plan.cfg.rmp_enabled", return_value=True
        ):
            plan = build_retrieval_plan(c, use_web_search=True, question="Who is Dr Menon?")
        self.assertTrue(plan.use_official_live)
        self.assertIn("student_rating", plan.companion_categories)
        self.assertIn("SRC-C-RMP-001", plan.companion_source_ids)

    def test_historical_dean_query_searches_official_people_sources_without_rmp(self):
        q = "Who was the dean of ENSC department at McNeese?"
        c = classify_retrieval(q)
        self.assertEqual(c.primary_intent, INTENT_FACULTY_IDENTITY)
        self.assertEqual(c.entities, [])
        plan = build_retrieval_plan(c, use_web_search=True, question=q)
        self.assertEqual(plan.companion_source_ids, [])
        self.assertNotIn("student_rating", plan.companion_categories)

    def test_student_jobs_web_plan_is_not_polluted_by_rmp(self):
        q = "What are the jobs available to students?"
        c = classify_retrieval(q)
        plan = build_retrieval_plan(c, use_web_search=True, question=q)
        self.assertTrue(plan.allow_agentic_web)
        self.assertTrue(plan.allow_open_web)
        self.assertFalse(any("ratemyprofessors" in d for d in plan.browse_domains))
    def test_football_game_is_athletics_live_not_kb(self):
        q = "When is the next McNeese football game?"
        c = classify_retrieval(q)
        self.assertEqual(c.primary_intent, INTENT_ATHLETICS)
        self.assertTrue(c.use_official_live)
        self.assertFalse(c.use_kb)
        self.assertEqual(c.freshness, "current")
        plan = build_retrieval_plan(c, use_web_search=False, question=q)
        self.assertIn("SRC-028", plan.official_source_ids)
        self.assertTrue(plan.use_official_live)
        self.assertFalse(plan.use_kb)
        self.assertTrue(
            any("mcneesesports.com" in d for d in (plan.browse_domains or [])),
            plan.browse_domains,
        )


if __name__ == "__main__":
    unittest.main()
