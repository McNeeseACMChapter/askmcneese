from __future__ import annotations

import unittest

from app.services.ask_execution import outcome_status
from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.evidence import evaluate_evidence
from app.services.campus_intelligence.route_validator import (
    correct_campus_spelling,
    extract_goal_signals,
    route_matches_goal,
)
from app.services.campus_intelligence.specialists import retrieve_registry_records
from app.services.conversation_context import (
    looks_like_followup,
    looks_like_slot_value,
    resolve_question_with_history,
)
from app.services.rccs.models import RetrievedEvidence, utcnow


def _evidence(
    *,
    evidence_id: str,
    title: str,
    text: str,
    url: str,
    source_group: str,
    link_only: bool = False,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=evidence_id,
        title=title,
        url=url,
        text=text,
        source_id=evidence_id,
        source_name=title,
        source_tier="A",
        trust_level="official",
        category="test",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.9,
        is_link_only=link_only,
        metadata={"source_groups": [source_group]},
    )


class InternationalApplicationRouteTests(unittest.TestCase):
    def test_compound_apply_and_register_uses_admissions_not_student_services(self) -> None:
        questions = (
            "I want to register the class but now i am interantional student tell me the exact steps to apply?",
            "I am an internationl student. What are the exact steps to apply?",
            "Registering classes later — I am an international applicant, how do I apply?",
        )
        for question in questions:
            compiled = compile_campus_query(question)
            self.assertEqual(compiled.domain, "admissions", question)
            self.assertEqual(compiled.intent, "apply", question)
            self.assertNotEqual(compiled.domain, "student_services", question)
            self.assertTrue(
                set(compiled.required_source_groups)
                & {"international_admissions", "official_admissions", "application_portal"},
                question,
            )
            self.assertFalse(
                set(compiled.required_source_groups) & {"housing", "dining", "bookstore"},
                question,
            )
            self.assertIn("steps", compiled.required_fields, question)
            self.assertNotIn("answer", compiled.required_fields, question)
            self.assertTrue(route_matches_goal(compiled), question)

    def test_status_document_questions_stay_on_international_services(self) -> None:
        compiled = compile_campus_query(
            "I'm an interantional student and my I-20 is going to expire before I graduate. What should I do?"
        )
        self.assertEqual(compiled.domain, "international_services")
        self.assertIn("international_services", compiled.required_source_groups)
        self.assertNotIn("bookstore", compiled.required_source_groups)

    def test_near_miss_international_spelling_is_normalized(self) -> None:
        corrected, reasons = correct_campus_spelling("i am an interantional student")
        self.assertIn("international", corrected)
        self.assertTrue(any("interantional" in reason for reason in reasons))
        self.assertTrue(extract_goal_signals(corrected).international)

    def test_regular_plurals_are_not_collapsed_to_campus_stems(self) -> None:
        corrected, reasons = correct_campus_spelling(
            "what documents do international students need?"
        )
        self.assertIn("documents", corrected)
        self.assertIn("students", corrected)
        self.assertFalse(reasons)


class AcademicCalendarContinuityTests(unittest.TestCase):
    def test_season_semester_year_is_an_explicit_term(self) -> None:
        questions = (
            "when does the fall semester 2026 starts?",
            "When does Fall semester 2026 start?",
            "when does the spring semester 2027 start?",
        )
        for question in questions:
            compiled = compile_campus_query(question)
            self.assertEqual(compiled.domain, "academic_calendar", question)
            self.assertEqual(compiled.intent, "check_deadline", question)
            self.assertFalse(compiled.clarification_required, question)
            self.assertTrue(compiled.entities.get("term"), question)

    def test_season_without_year_still_asks_for_the_term(self) -> None:
        compiled = compile_campus_query("when does the fall semester start?")
        self.assertEqual(compiled.domain, "academic_calendar")
        self.assertTrue(compiled.clarification_required)


class TopicResetTests(unittest.TestCase):
    def test_unrelated_language_does_not_inherit_awaiting_calendar_task(self) -> None:
        state = {
            "task_type": "academic_calendar:check_deadline",
            "status": "awaiting_input",
            "domain": "academic_calendar",
            "pending_field": "clarification",
            "query_anchor": "when does the fall semester 2026 starts?",
        }
        for question in ("what the fuck?", "Where is the bookstore?", "How do I apply?"):
            self.assertFalse(looks_like_slot_value(question, state), question)
            self.assertFalse(looks_like_followup(question, None, state), question)
            resolved, metadata = resolve_question_with_history(question, None, state)
            self.assertFalse(metadata["task_state_used"], question)
            self.assertEqual(resolved, question)

    def test_slot_replies_still_continue_the_pending_task(self) -> None:
        state = {
            "task_type": "academic_calendar:check_deadline",
            "status": "awaiting_input",
            "query_anchor": "What is the withdrawal deadline for the autumn term?",
            "pending_field": "clarification",
        }
        self.assertTrue(looks_like_followup("Fall 2026", None, state))
        resolved, metadata = resolve_question_with_history("Fall 2026", None, state)
        self.assertTrue(metadata["task_state_used"])
        compiled = compile_campus_query(resolved)
        self.assertEqual(compiled.entities["term"], "fall 2026")
        self.assertFalse(compiled.clarification_required)

    def test_complete_course_question_does_not_inherit_dining_history(self) -> None:
        history = [
            {"role": "user", "content": "How does dual enrollment work?"},
            {"role": "assistant", "content": "Dual enrollment lets undergraduate students take college courses."},
            {"role": "user", "content": "What dining meal plans are available?"},
            {"role": "assistant", "content": "Check the dining portal for current meal plans."},
        ]
        question = "What are the calculus courses offered at spring 2026 at mcneese?"
        self.assertFalse(looks_like_followup(question, history))
        resolved, metadata = resolve_question_with_history(question, history)
        self.assertFalse(metadata["followup"])
        self.assertEqual(resolved, question)
        compiled = compile_campus_query(resolved)
        self.assertEqual(compiled.domain, "registration")
        self.assertEqual(compiled.answer_shape, "course_offering_result")
        self.assertNotEqual(compiled.domain, "student_services")
        self.assertNotEqual(compiled.domain, "catalog")
        self.assertNotIn("dining", compiled.required_source_groups)
        self.assertNotIn("official_catalog", compiled.required_source_groups)

    def test_standalone_question_ignores_prior_planner_task_state(self) -> None:
        question = "What are the library location and hours today?"
        state = {
            "schema_version": 1,
            "task_type": "course_schedule_conflict",
            "status": "active",
            "domain": "registration",
            "term": "fall 2026",
            "subject": "CSCI",
            "constraint_course": "Calculus II",
            "query_anchor": "Find CSCI courses that do not conflict with Calculus II.",
        }
        self.assertFalse(looks_like_followup(question, None, state))
        resolved, metadata = resolve_question_with_history(question, None, state)
        self.assertFalse(metadata["followup"])
        self.assertFalse(metadata["task_state_used"])
        self.assertEqual(resolved, question)


class TermCourseOfferingRouteTests(unittest.TestCase):
    def test_term_offerings_use_class_search_for_any_subject(self) -> None:
        questions = {
            "What are the calculus courses offered at spring 2026 at mcneese?": "calculus",
            "What ENGL courses are offered in Fall 2026?": "ENGL",
            "What biology classes are available in Fall 2026?": "biology",
            "What CSCI courses are offered in Fall 2026?": "CSCI",
            "What nursing courses are offered in Fall 2026?": "nursing",
        }
        for question, needle in questions.items():
            compiled = compile_campus_query(question)
            self.assertEqual(compiled.domain, "registration", question)
            self.assertEqual(compiled.intent, "list", question)
            self.assertEqual(compiled.answer_shape, "course_offering_result", question)
            self.assertEqual(compiled.entities["course_query"], needle, question)
            self.assertNotEqual(compiled.domain, "catalog", question)

    def test_course_description_stays_on_catalog(self) -> None:
        compiled = compile_campus_query("What is CSCI 180?")
        self.assertEqual(compiled.domain, "catalog")
        self.assertEqual(compiled.intent, "find_course")
        self.assertNotEqual(compiled.answer_shape, "course_offering_result")

    def test_conflict_questions_stay_on_conflict_shape(self) -> None:
        compiled = compile_campus_query(
            "Can you find all CSCI courses offered in Fall 2026 that do not conflict with Calculus II?"
        )
        self.assertEqual(compiled.answer_shape, "schedule_conflict_result")
        self.assertNotEqual(compiled.answer_shape, "course_offering_result")


class ParkingProcessRouteTests(unittest.TestCase):
    def test_parking_permit_is_a_process_not_a_citation_contact(self) -> None:
        compiled = compile_campus_query("How do I get a parking permit?")
        self.assertEqual(compiled.domain, "locations")
        self.assertEqual(compiled.intent, "find_process")
        self.assertIn("parking_transportation", compiled.required_source_groups)
        destinations = retrieve_registry_records(
            "How do I get a parking permit?",
            compiled,
        )
        self.assertNotIn(
            "CUR-PARKING-APPEALS",
            [item.source_id for item in destinations],
        )


class CrossIntentGuardrailTests(unittest.TestCase):
    def test_main_campus_contact_does_not_become_registrar_contact(self) -> None:
        compiled = compile_campus_query(
            "What is the main campus address and phone number?"
        )
        self.assertEqual(compiled.domain, "locations")
        self.assertEqual(compiled.intent, "locate")
        self.assertEqual(compiled.required_source_groups, ["maps_and_locations"])
        self.assertNotIn("official_directory", compiled.required_source_groups)

    def test_course_timing_does_not_parse_preposition_as_subject(self) -> None:
        compiled = compile_campus_query(
            "Can you let me know the timing for 291 calculus?"
        )
        self.assertEqual(compiled.domain, "registration")
        self.assertEqual(compiled.answer_shape, "course_offering_result")
        self.assertEqual(compiled.entities["course"], "MATH 291")
        self.assertEqual(compiled.entities["course_query"], "MATH 291")
        self.assertTrue(compiled.clarification_required)
        self.assertIn("term and year", compiled.ambiguities[0])

    def test_low_confidence_general_route_clarifies_instead_of_guessing(self) -> None:
        compiled = compile_campus_query(
            "How many tests are there to skip math 177?"
        )
        self.assertEqual(compiled.domain, "general_campus")
        self.assertTrue(compiled.clarification_required)
        self.assertIn("not certain", compiled.ambiguities[0])


class LibraryHoursContractTests(unittest.TestCase):
    def test_library_hours_question_requires_hours_and_place(self) -> None:
        compiled = compile_campus_query("Library location and hours")
        self.assertEqual(compiled.domain, "academic_support")
        self.assertIn("place", compiled.required_fields)
        self.assertIn("hours", compiled.required_fields)


class EvidenceContractTests(unittest.TestCase):
    def test_exact_course_query_rejects_a_different_course_number(self) -> None:
        query = compile_campus_query("What is MATH 199?")
        wrong_course = _evidence(
            evidence_id="math-191",
            title="MATH 191 - Calculus II",
            text=(
                "MATH 191 is Calculus II. It carries four credit hours and has "
                "a prerequisite of MATH 190."
            ),
            url="https://catalog.mcneese.edu/preview_course_nopop.php?catoid=1&coid=191",
            source_group="official_catalog",
        )

        result = evaluate_evidence(query, [wrong_course])

        self.assertEqual(query.entities["course"], "MATH 199")
        self.assertEqual(result.accepted_evidence_ids, [])
        self.assertFalse(result.passed)

    def test_broad_source_group_without_subject_overlap_is_rejected(self) -> None:
        query = compile_campus_query("How can alumni support McNeese?")
        evidence = _evidence(
            evidence_id="general-news",
            title="Faculty research award",
            text=(
                "A faculty member received a research award for laboratory work "
                "and presented the project at a regional conference."
            ),
            url="https://www.mcneese.edu/news/research-award/",
            source_group="general_official",
        )
        result = evaluate_evidence(query, [evidence])
        self.assertFalse(result.passed)
        self.assertEqual(result.accepted_evidence_ids, [])

    def test_destination_only_record_cannot_satisfy_generic_answer_field(self) -> None:
        query = compile_campus_query("Tell me about the McNeese bookstore.")
        self.assertIn("answer", query.required_fields)
        destination = _evidence(
            evidence_id="bookstore-dest",
            title="McNeese Bookstore",
            text=(
                "Visit the official McNeese bookstore destination for textbooks, "
                "supplies, and merchandise. This page is a governed pointer only."
            ),
            url="https://www.mcneese.edu/bookstore",
            source_group="bookstore",
            link_only=True,
        )
        result = evaluate_evidence(query, [destination])
        self.assertIn("answer", result.field_coverage)
        self.assertFalse(result.field_coverage["answer"])
        self.assertFalse(result.passed)

    def test_bookstore_destination_cannot_release_an_admissions_apply_contract(self) -> None:
        query = compile_campus_query(
            "I am an international student. Tell me the exact steps to apply."
        )
        destination = _evidence(
            evidence_id="bookstore-dest",
            title="McNeese Bookstore",
            text=(
                "The bookstore sells textbooks and supplies. Visit the official "
                "store homepage for hours, contact information, and merchandise."
            ),
            url="https://www.mcneese.edu/bookstore",
            source_group="bookstore",
            link_only=True,
        )
        result = evaluate_evidence(query, [destination])
        self.assertEqual(query.domain, "admissions")
        self.assertEqual(query.intent, "apply")
        self.assertFalse(result.passed)
        self.assertTrue(result.missing_source_groups or result.missing_fields)

    def test_official_page_read_counts_named_hall_as_location(self) -> None:
        query = compile_campus_query(
            "Where is the Cashier's Office, and what time does it close today?"
        )
        page = RetrievedEvidence(
            evidence_id="cashier-page",
            title="Cashiers Office",
            url="https://www.mcneese.edu/cashiers/",
            text=(
                "The Cashiers Office is located in Smith Hall. "
                "Monday - Thursday 7:45 a.m. - 12:00 p.m. and 1:00 p.m. - 4:30 p.m. "
                "Friday 7:45 a.m. - 11:00 a.m. Call 337-475-5098."
            ),
            source_id="PAGE_OPEN_OFFICIAL",
            source_name="Cashiers Office",
            source_tier="A",
            trust_level="official",
            category="student_finance",
            retrieval_channel="official_live",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=0.99,
            metadata={"page_read": True, "source_groups": ["student_accounts"]},
        )
        result = evaluate_evidence(query, [page])
        self.assertIn("cashier-page", result.accepted_evidence_ids)
        self.assertTrue(result.field_coverage.get("location") or result.partial_allowed)
        self.assertTrue(result.field_coverage.get("hours") or result.partial_allowed)
        self.assertTrue(result.passed or result.partial_allowed)


class OutcomeMetricTests(unittest.TestCase):
    def test_clarification_is_not_logged_as_success(self) -> None:
        self.assertEqual(
            outcome_status(
                {"status": "CAN_RELEASE", "reasons": ["CLARIFICATION_REQUIRED"]},
                "clarification",
            ),
            "clarification",
        )
        self.assertEqual(
            outcome_status({"status": "CAN_RELEASE_PARTIAL", "reasons": []}, "grounded-partial-fast"),
            "partial",
        )
        self.assertEqual(
            outcome_status({"status": "BLOCKED", "reasons": ["UNSUPPORTED_MATERIAL_CLAIM"]}, "release-gated"),
            "release_blocked",
        )
        self.assertEqual(
            outcome_status({"status": "CAN_RELEASE", "reasons": []}, "Claude"),
            "success",
        )


if __name__ == "__main__":
    unittest.main()
