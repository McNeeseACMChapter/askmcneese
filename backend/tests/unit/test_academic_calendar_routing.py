import unittest

from app.services.llm import _persona_line, _prepare_context_chunks
from app.services.rccs.classify import (
    INTENT_ACADEMIC_CALENDAR,
    INTENT_ATHLETICS,
    classify_retrieval,
)
from app.services.rccs.plan import build_retrieval_plan
from app.services.source_registry import (
    academic_schedule_page_candidates,
    match_registry,
)


class AcademicCalendarRoutingTests(unittest.TestCase):
    def test_term_year_end_question_routes_to_live_registrar_schedule(self):
        question = "when is summer semester 2026 ending?"
        classification = classify_retrieval(question)
        plan = build_retrieval_plan(
            classification,
            use_web_search=False,
            question=question,
        )

        self.assertEqual(classification.primary_intent, INTENT_ACADEMIC_CALENDAR)
        self.assertEqual(classification.freshness, "current")
        self.assertFalse(plan.use_kb)
        self.assertTrue(plan.use_official_live)
        self.assertEqual(plan.official_source_ids[0], "SRC-012")
        self.assertIn("/schedule/summer-2026/", academic_schedule_page_candidates(question)[0])

    def test_final_exam_question_prioritizes_final_exam_page(self):
        urls = academic_schedule_page_candidates(
            "When are Summer 2026 final exams?"
        )
        self.assertIn("summer-2026-final-exam-schedule", urls[0])
        self.assertIn("summer-2026", urls[1])

    def test_registry_matches_schedule_for_semester_language(self):
        match = match_registry("when does the summer semester end", max_sources=3)
        self.assertEqual(match.source_ids[0], "SRC-012")

    def test_athletics_schedule_is_not_misclassified_as_academic_calendar(self):
        classification = classify_retrieval("When is the next football game?")
        self.assertEqual(classification.primary_intent, INTENT_ATHLETICS)

    def test_term_course_section_inventory_is_not_calendar_intent(self):
        classification = classify_retrieval(
            "Show me Calculus II sections for Fall 2026."
        )
        self.assertNotEqual(classification.primary_intent, INTENT_ACADEMIC_CALENDAR)


    def test_calendar_question_does_not_invent_applicant_category_scope(self):
        instruction = _persona_line(None, "when is summer semester 2026 ending?")
        self.assertIn("No applicant category is implied", instruction)
        self.assertNotIn("Answer for every applicant category", instruction)
    def test_context_excerpt_keeps_relevant_date_rows_beyond_page_navigation(self):
        navigation = "Navigation and unrelated campus content.\n" * 120
        schedule = (
            "| Regular Summer Session | |\n"
            "| Classes begin | June 10 |\n"
            "| Classes end | July 21 |\n"
            "| Final examinations end | July 24 |\n"
        )
        prepared = _prepare_context_chunks(
            "when is summer semester 2026 ending?",
            [{"title": "Summer 2026", "text": navigation + schedule}],
        )
        excerpt = prepared[0]["text"]
        self.assertIn("Classes end | July 21", excerpt)
        self.assertIn("Final examinations end | July 24", excerpt)
        self.assertLessEqual(len(excerpt), 6000)


if __name__ == "__main__":
    unittest.main()
