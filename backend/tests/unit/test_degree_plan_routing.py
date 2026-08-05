import unittest

from app.services.catalog_retrieval import _program_score, _safe_program_url
from app.services.llm import (
    _direct_degree_plan_answer,
    _direct_upper_division_answer,
    _is_complex_query,
    _prepare_context_chunks,
)
from app.services.rccs.classify import (
    INTENT_DEGREE_PLAN,
    INTENT_FACULTY_IDENTITY,
    classify_retrieval,
)
from app.services.rccs.plan import build_retrieval_plan


class DegreePlanRoutingTests(unittest.TestCase):
    def test_full_mechanical_engineering_plan_routes_to_current_catalog(self):
        question = "what are the courses i need to study to complete whole mechanical engineering degree list it"
        classification = classify_retrieval(question)
        plan = build_retrieval_plan(
            classification,
            use_web_search=False,
            question=question,
        )

        self.assertEqual(classification.primary_intent, INTENT_DEGREE_PLAN)
        self.assertEqual(classification.freshness, "current")
        self.assertFalse(plan.use_kb)
        self.assertTrue(plan.use_official_live)
        self.assertEqual(plan.official_source_ids[:2], ["SRC-011", "SRC-007"])
        self.assertEqual(plan.companion_source_ids, [])

    def test_professor_course_question_is_not_a_degree_plan(self):
        classification = classify_retrieval("What courses does Professor Menon teach?")
        self.assertEqual(classification.primary_intent, INTENT_FACULTY_IDENTITY)

    def test_program_match_prefers_bachelors_over_minor_and_graduate(self):
        question = "list every course for the complete mechanical engineering degree"
        bachelor = _program_score(question, "Mechanical Engineering, BSME")
        minor = _program_score(question, "Mechanical Engineering Minor")
        graduate = _program_score(question, "Mechanical Engineering, MEng")
        self.assertGreater(bachelor, minor)
        self.assertGreater(bachelor, graduate)


    def test_generic_computer_science_prefers_general_concentration(self):
        question = "list all courses required to complete the computer science degree"
        general = _program_score(
            question, "Computer Science, General Computer Science Concentration, BS"
        )
        ai = _program_score(
            question, "Computer Science, Artificial Intelligence Concentration, BS"
        )
        cybersecurity = _program_score(
            question, "Computer Science, Cybersecurity Concentration, BS"
        )
        self.assertGreater(general, ai)
        self.assertGreater(general, cybersecurity)
        self.assertGreater(
            _program_score(
                "complete the cybersecurity computer science degree",
                "Computer Science, Cybersecurity Concentration, BS",
            ),
            _program_score(
                "complete the cybersecurity computer science degree",
                "Computer Science, General Computer Science Concentration, BS",
            ),
        )
    def test_catalog_url_is_derived_only_from_current_official_catalog(self):
        valid = _safe_program_url(
            "/preview_program.php?catoid=102&poid=61753&returnto=8461"
        )
        self.assertEqual(
            valid,
            "https://catalog.mcneese.edu/preview_program.php?catoid=102&poid=61753&returnto=8461",
        )
        self.assertIsNone(_safe_program_url("https://evil.example/preview_program.php?catoid=102&poid=1"))
        self.assertIsNone(_safe_program_url("/preview_program.php?catoid=99&poid=61753"))
        self.assertIsNone(_safe_program_url("/content.php?catoid=102&poid=61753"))

    def test_complete_plan_is_complex_and_keeps_final_semester(self):
        question = "list all courses required to complete the mechanical engineering degree"
        plan_text = (
            "Freshman Year Fall\nENGR 101\n"
            + ("Course requirement detail\n" * 160)
            + "Senior Year Spring\nMEEN 491 - Senior Design Project II\nTotal Hours: 128"
        )
        prepared = _prepare_context_chunks(
            question,
            [{"title": "Mechanical Engineering, BSME", "text": plan_text}],
        )
        self.assertTrue(_is_complex_query(question))
        self.assertIn("Senior Year Spring", prepared[0]["text"])
        self.assertIn("Total Hours: 128", prepared[0]["text"])


    def test_catalog_degree_plan_is_formatted_without_model_rewriting(self):
        answer = _direct_degree_plan_answer(
            [
                {
                    "category": "degree_plan",
                    "title": "Mechanical Engineering, BSME — 2026-2027 Academic Catalog",
                    "text": (
                        "Official McNeese 2026-2027 academic catalog curriculum.\n"
                        "Mechanical Engineering, BSME\n"
                        "Total Hours Required for Degree: 128\n"
                        "Freshman Fall - 17 hours\n"
                        "ENGR 101 - Engineering Graphics Cr: 2\n"
                        "Senior Spring - 17 hours\n"
                        "MEEN 491 - Senior Design Project II Cr: 3\n"
                        "Note\nStudents must earn a grade of C or better."
                    ),
                }
            ]
        )
        self.assertIsNotNone(answer)
        self.assertIn("128 total credit hours", answer)
        self.assertIn("**Freshman Fall - 17 hours**", answer)
        self.assertIn("- ENGR 101 - Engineering Graphics Cr: 2", answer)
        self.assertIn("**Senior Spring - 17 hours**", answer)
        self.assertIn("- MEEN 491 - Senior Design Project II Cr: 3", answer)

    def test_400_level_followup_routes_to_degree_plan_not_course_catalog(self):
        question = (
            "how many 400 level of course do I need to earn? "
            "(upper-division 300/400-level credit hours required for this degree plan) "
            "about computer science "
            "(continuing from: how many credits do we have to complete for undergrad "
            "computer science degree at mcneese?)"
        )
        classification = classify_retrieval(question)
        self.assertEqual(classification.primary_intent, INTENT_DEGREE_PLAN)

    def test_upper_division_question_answers_hours_not_course_count(self):
        chunks = [
            {
                "category": "degree_plan",
                "title": "Computer Science, General Computer Science Concentration, BS",
                "source_url": "https://catalog.mcneese.edu/preview_program.php?catoid=102&poid=61487",
                "text": (
                    "All bachelor's degrees must include 40 hours at the 300/400 level.\n"
                    "Approved Electives (300/400 Level) Cr: 12\n"
                    "Total Hours Required for Degree: 120"
                ),
            }
        ]
        answer = _direct_upper_division_answer(
            "How man 400 level of course do I need to earn?",
            chunks,
        )
        self.assertIsNotNone(answer)
        self.assertIn("40 credit hours at the 300/400 level", answer)
        self.assertIn("credit hours", answer)
        self.assertIn("Approved Electives (300/400 Level) Cr: 12", answer)


if __name__ == "__main__":
    unittest.main()
