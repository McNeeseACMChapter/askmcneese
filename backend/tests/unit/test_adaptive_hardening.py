from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
import time
import unittest
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.evidence import evaluate_evidence
from app.services.campus_intelligence.registry import source_groups_for
from app.services.campus_intelligence.specialists import (
    retrieve_current_service_snapshots,
    retrieve_registry_records,
)
from app.services.class_planner.models import SubjectOption, TermOption
from app.services.class_planner.pipeline import parse_sections
from app.services.class_planner.db import metadata
from app.services.class_planner.store import ClassPlannerStore
from app.services.conversation_context import (
    build_request_context,
    looks_like_followup,
    resolve_question_with_history,
)
from app.services.rccs.classify import (
    INTENT_COURSE_SCHEDULE,
    classify_retrieval,
)
from app.routers.ask import _planner_actions, ask_stream
from app.services.rccs.models import RetrievedEvidence, utcnow
from app.services.rccs.hybrid import hybrid_retrieve


FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "mcneese_class_search"
)


class RequestContextHardeningTests(unittest.TestCase):
    def test_request_context_uses_campus_timezone_and_stable_turn_identity(self) -> None:
        now = datetime(2026, 8, 14, 16, 30, tzinfo=ZoneInfo("America/Chicago"))
        context = build_request_context(
            "What time does the Registrar close today?",
            conversation_id="conversation-1",
            turn_id="turn-2",
            parent_turn_id="turn-1",
            request_id="request-2",
            now=now,
        )
        self.assertEqual(context["campus_timezone"], "America/Chicago")
        self.assertEqual(context["current_date"], "2026-08-14")
        self.assertEqual(context["current_day"], "Friday")
        self.assertEqual(context["conversation_id"], "conversation-1")
        self.assertEqual(context["turn_id"], "turn-2")
        self.assertEqual(context["parent_turn_id"], "turn-1")

    def test_interrupted_and_slot_followups_reconstruct_prior_task(self) -> None:
        history = [
            {
                "role": "user",
                "content": "What is the deadline to drop a Fall 2026 class without receiving an F?",
            },
            {
                "role": "assistant",
                "content": "I could not finish verifying the term deadline.",
            },
        ]
        for question in ("Why did you stop?", "How much?", "Where exactly?"):
            self.assertTrue(looks_like_followup(question, history))
            resolved, metadata = resolve_question_with_history(question, history)
            self.assertTrue(metadata["followup"])
            self.assertIn("fall 2026", resolved.lower())

    def test_five_digit_crn_completes_pending_schedule_slot(self) -> None:
        history = [
            {
                "role": "user",
                "content": "Find all Fall 2026 CSCI courses that do not conflict with Calculus II.",
            },
            {
                "role": "assistant",
                "content": "Here are the Calculus II sections. Which CRN do you want to use?",
            },
        ]
        followup = "61066 I want to use this Calculus II course."
        self.assertTrue(looks_like_followup(followup, history))
        resolved, _ = resolve_question_with_history(followup, history)
        compiled = compile_campus_query(resolved)
        self.assertEqual(compiled.entities["constraint_section"], "61066")
        self.assertEqual(compiled.entities["constraint_course"], "Calculus II")
        self.assertEqual(compiled.entities["subject"], "CSCI")

    def test_selected_csci_crns_preserve_prior_calculus_constraint(self) -> None:
        history = [
            {
                "role": "user",
                "content": "Find all Fall 2026 CSCI courses that do not conflict with Calculus II.",
            },
            {
                "role": "assistant",
                "content": "Which Calculus II CRN do you want to use?",
            },
            {"role": "user", "content": "61066 i want to register this calculus course"},
            {"role": "assistant", "content": "Here are 21 non-conflicting CSCI sections."},
        ]
        resolved, metadata = resolve_question_with_history(
            "Keep CSCI CRNs 61154 and 61162",
            history,
        )
        compiled = compile_campus_query(resolved)
        self.assertTrue(metadata["followup"])
        self.assertEqual(compiled.entities["constraint_section"], "61066")
        self.assertEqual(compiled.entities["subject"], "CSCI")
        self.assertEqual(compiled.entities["term"], "fall 2026")

        action_history = history + [
            {"role": "user", "content": "Keep CSCI CRNs 61154 and 61162"},
            {"role": "assistant", "content": "Ready for Class Planner."},
        ]
        action_resolved, _ = resolve_question_with_history(
            "Please put these in Class Planner",
            action_history,
        )
        self.assertIn("selected CSCI CRNs 61154, 61162", action_resolved)
        self.assertEqual(compile_campus_query(action_resolved).entities["constraint_section"], "61066")


class SSEIdentityTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_stream_frame_has_stable_turn_identity_and_sequence(self) -> None:
        context = build_request_context(
            "hello",
            conversation_id="conversation-sse",
            turn_id="turn-sse",
            request_id="request-sse",
        )
        frames = [
            frame
            async for frame in ask_stream(
                "hello",
                request_id="request-sse",
                run_id="attempt-sse",
                request_context=context,
            )
        ]
        payloads = [
            json.loads(next(line[6:] for line in frame.splitlines() if line.startswith("data: ")))
            for frame in frames
        ]
        self.assertGreaterEqual(len(payloads), 3)
        self.assertEqual([item["sequence"] for item in payloads], list(range(1, len(payloads) + 1)))
        self.assertEqual(len({item["event_id"] for item in payloads}), len(payloads))
        for payload in payloads:
            self.assertEqual(payload["request_id"], "request-sse")
            self.assertEqual(payload["conversation_id"], "conversation-sse")
            self.assertEqual(payload["turn_id"], "turn-sse")
            self.assertEqual(payload["attempt_id"], "attempt-sse")


class VerifiedSnapshotFastPathTests(unittest.IsolatedAsyncioTestCase):
    async def test_today_service_snapshot_skips_redundant_kb_and_live_fetch(self) -> None:
        question = "I'm feeling sick and need to see someone on campus. Where can I get medical help?"
        with (
            patch("app.services.rccs.hybrid._retrieve_kb", new=AsyncMock()) as kb,
            patch("app.services.rccs.hybrid._retrieve_official", new=AsyncMock()) as official,
        ):
            result = await hybrid_retrieve(
                question,
                source_scope="adaptive",
                request_context={"current_date": "2026-08-14"},
            )
        self.assertTrue(result.metadata.get("verified_snapshot_shortcut"))
        self.assertEqual([item.source_id for item in result.evidence], ["CUR-HEALTH-SERVICES"])
        kb.assert_not_awaited()
        official.assert_not_awaited()

    async def test_parking_permit_does_not_use_citation_appeal_snapshot(self) -> None:
        question = "How do I get a parking permit?"
        with (
            patch("app.services.rccs.hybrid._retrieve_kb", new=AsyncMock(return_value=([], None))),
            patch("app.services.rccs.hybrid._retrieve_official", new=AsyncMock(return_value=([], None))),
            patch(
                "app.services.rccs.hybrid._retrieve_structured_specialist",
                new=AsyncMock(return_value=([], None)),
            ),
        ):
            result = await hybrid_retrieve(
                question,
                source_scope="adaptive",
                request_context={"current_date": "2026-08-14"},
            )
        self.assertFalse(result.metadata.get("verified_snapshot_shortcut"))
        self.assertNotEqual(
            [item.source_id for item in result.evidence],
            ["CUR-PARKING-APPEALS"],
        )

    def test_recent_service_snapshot_remains_fast_after_midnight(self) -> None:
        question = "I'm feeling sick and need medical help on campus."
        compiled = compile_campus_query(question)
        evidence = retrieve_current_service_snapshots(
            question,
            compiled,
            current_date="2026-08-15",
        )
        self.assertEqual([item.source_id for item in evidence], ["CUR-HEALTH-SERVICES"])
        self.assertEqual(evidence[0].metadata["last_verified"], "2026-08-14")
        self.assertEqual(evidence[0].metadata["snapshot_age_days"], 1)

    async def test_one_turn_budget_prevents_serial_live_timeout_multiplication(self) -> None:
        async def slow_official(*_args, **_kwargs):
            await asyncio.sleep(2)
            return [], "upstream_timeout"

        official = AsyncMock(side_effect=slow_official)
        started = time.perf_counter()
        with (
            patch("app.services.rccs.config.turn_retrieval_budget_seconds", return_value=1.0),
            patch("app.services.rccs.hybrid._retrieve_official", new=official),
        ):
            result = await hybrid_retrieve(
                "What is the deadline to drop a Fall 2026 class without receiving an F?",
                source_scope="adaptive",
                request_context={"current_date": "2026-08-30"},
            )
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 10.0)
        self.assertEqual(official.await_count, 1)
        self.assertLessEqual(result.metadata["total_retrieval_latency"], 1_200)
        self.assertTrue(result.metadata["retrieval_budget_exhausted"])
        self.assertEqual(
            result.metadata["targeted_recovery"]["skipped"],
            "turn_retrieval_budget_exhausted",
        )

    async def test_turn_returns_without_waiting_for_slow_cancellation_cleanup(self) -> None:
        async def cancellation_resistant_official(*_args, **_kwargs):
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                # Model a network adapter that needs time to close its transport.
                await asyncio.sleep(5)
            return [], "upstream_timeout"

        started = time.perf_counter()
        with (
            patch("app.services.rccs.config.turn_retrieval_budget_seconds", return_value=0.2),
            patch(
                "app.services.rccs.hybrid._retrieve_official",
                new=AsyncMock(side_effect=cancellation_resistant_official),
            ),
        ):
            result = await hybrid_retrieve(
                "What is the deadline to drop a Fall 2026 class without receiving an F?",
                source_scope="adaptive",
                request_context={"current_date": "2026-08-30"},
            )
        elapsed = time.perf_counter() - started

        # Local classification can take a few seconds on constrained Windows
        # runners, but the five-second cancellation cleanup must not be added.
        self.assertLess(elapsed, 4.5)
        self.assertTrue(result.metadata["retrieval_budget_exhausted"])


class RoutingHardeningTests(unittest.TestCase):
    def test_registrar_uses_the_generic_named_office_contract(self) -> None:
        compiled = compile_campus_query(
            "Where is the McNeese Registrar's Office, and what time does it close today?"
        )
        self.assertEqual(compiled.domain, "registration")
        self.assertEqual(
            compiled.required_fields,
            ["contact_method", "role", "location", "hours"],
        )
        self.assertIn("registration", compiled.required_source_groups)
        self.assertIn("official_directory", compiled.required_source_groups)

    def test_international_office_uses_the_same_generic_location_hours_contract(self) -> None:
        compiled = compile_campus_query(
            "Where is the International Office, and what time does it close today?"
        )
        self.assertEqual(compiled.domain, "international_services")
        self.assertEqual(compiled.entities["office"], "International Student Services")
        self.assertEqual(
            compiled.required_fields,
            ["role", "contact_method", "location", "hours"],
        )
        self.assertIn("international_services", compiled.required_source_groups)

    def test_health_request_routes_to_wellbeing_health(self) -> None:
        compiled = compile_campus_query(
            "I'm feeling sick and need to see someone on campus. Where can I get medical help?"
        )
        self.assertEqual((compiled.domain, compiled.subdomain), ("wellbeing", "health"))
        self.assertEqual(compiled.intent, "locate")
        self.assertEqual(compiled.required_source_groups, ["health_services"])
        self.assertEqual(
            compiled.required_fields,
            ["services", "location", "contact_method", "hours", "emergency_guidance"],
        )

    def test_expiring_i20_routes_to_international_services(self) -> None:
        compiled = compile_campus_query(
            "I'm an international student and my I-20 is going to expire before I graduate. What should I do?"
        )
        self.assertEqual(compiled.domain, "international_services")
        self.assertIn("international_services", compiled.required_source_groups)
        self.assertNotIn("academic_standing", compiled.required_source_groups)
        self.assertEqual(compiled.required_fields, ["current_student_guidance", "contact_method"])

    def test_parking_appeal_routes_to_parking_not_academic_policy(self) -> None:
        compiled = compile_campus_query(
            "I received a parking ticket on campus but I think it was issued incorrectly. How can I appeal it?"
        )
        self.assertEqual((compiled.domain, compiled.subdomain), ("locations", "parking"))
        self.assertEqual(compiled.required_source_groups, ["parking_transportation"])
        self.assertNotIn("academic_standing", compiled.required_source_groups)

    def test_lost_id_extracts_all_material_answer_requirements(self) -> None:
        compiled = compile_campus_query(
            "I lost my McNeese ID card. What should I do, where should I go, and is there a replacement fee?"
        )
        self.assertEqual(compiled.domain, "registration")
        self.assertEqual(
            compiled.required_fields,
            ["replacement_process", "replacement_location", "replacement_fee"],
        )
        self.assertEqual(compiled.required_source_groups, ["student_id_cards"])

    def test_exact_frontend_starters_have_supported_routes_and_evidence(self) -> None:
        governed_starters = [
            (
                "Where is the Office of the Registrar, and what time does it close today?",
                "contact_card",
                "official_directory",
            ),
            (
                "I lost my McNeese ID card. Where do I get a replacement and how much does it cost?",
                "policy_plus_steps",
                "student_id_cards",
            ),
            (
                "How do I appeal a parking citation?",
                "policy_plus_steps",
                "parking_transportation",
            ),
        ]
        for question, answer_shape, source_group in governed_starters:
            with self.subTest(question=question):
                compiled = compile_campus_query(question)
                self.assertEqual(compiled.answer_shape, answer_shape)
                self.assertIn(source_group, compiled.required_source_groups)
                evidence = retrieve_registry_records(question, compiled)
                result = evaluate_evidence(compiled, evidence)
                self.assertTrue(result.passed, result.missing_fields)
                self.assertTrue(result.accepted_evidence_ids)

        schedule_question = (
            "Find Fall 2026 CSCI sections that do not conflict with Calculus II."
        )
        compiled = compile_campus_query(schedule_question)
        classified = classify_retrieval(schedule_question)
        self.assertEqual(compiled.answer_shape, "schedule_conflict_result")
        self.assertEqual(classified.primary_intent, INTENT_COURSE_SCHEDULE)

    def test_course_conflict_uses_structured_schedule_intent(self) -> None:
        question = (
            "Can you find me all CSCI courses being offered in Fall 2026 "
            "that do not conflict with Calculus II?"
        )
        compiled = compile_campus_query(question)
        classified = classify_retrieval(question)
        self.assertEqual(compiled.domain, "registration")
        self.assertEqual(compiled.answer_shape, "schedule_conflict_result")
        self.assertEqual(compiled.entities["term"], "fall 2026")
        self.assertEqual(compiled.entities["subject"], "CSCI")
        self.assertEqual(compiled.entities["constraint_course"], "Calculus II")
        self.assertEqual(classified.primary_intent, INTENT_COURSE_SCHEDULE)
        self.assertFalse(classified.use_kb)
        self.assertFalse(classified.use_official_live)

    def test_term_drop_deadline_routes_to_academic_calendar(self) -> None:
        compiled = compile_campus_query(
            "What is the deadline to drop a Fall 2026 class without receiving an F?"
        )
        self.assertEqual((compiled.domain, compiled.intent), ("academic_calendar", "check_deadline"))
        self.assertEqual(compiled.required_source_groups, ["official_calendar"])

    def test_unknown_advisor_routes_to_identification_workflow(self) -> None:
        compiled = compile_campus_query(
            "How can I contact my academic advisor if I don't know who my advisor is?"
        )
        self.assertEqual((compiled.domain, compiled.intent), ("registration", "find_process"))
        self.assertEqual(compiled.action, "identify_advisor")
        self.assertEqual(compiled.required_fields, ["advisor_identification_steps", "contact_method"])
        self.assertEqual(compiled.required_source_groups, ["academic_advising"])

    def test_overlapping_classes_route_to_resolution_workflow_not_computation(self) -> None:
        compiled = compile_campus_query(
            "I have two classes scheduled at the same time. Who should I contact, and what are my options?"
        )
        self.assertEqual((compiled.domain, compiled.intent), ("registration", "find_process"))
        self.assertEqual(compiled.action, "resolve_schedule_conflict")
        self.assertEqual(compiled.required_fields, ["resolution_options", "contact_method"])


class ClassPlannerAskIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        metadata.create_all(engine)
        self.store = ClassPlannerStore(engine)
        records = list(
            parse_sections(
                (FIXTURE_ROOT / "fall_2026_representative.html").read_text(encoding="utf-8"),
                "202660",
            )
        )
        base = records[0]
        records.extend(
            [
                replace(
                    base,
                    id=f"202660:{crn}",
                    crn=crn,
                    subject="MATH",
                    course_number="190",
                    section_code=section,
                    title="CALCULUS II",
                ).with_hash()
                for crn, section in (("62001", "A"), ("62002", "B"))
            ]
        )
        unique = {record.id: record for record in records}
        self.store.publish(
            term=TermOption("202660", "Fall 2026"),
            records=unique.values(),
            fetched_at="2026-08-14T12:00:00+00:00",
            source_url="https://schedule.mcneese.edu/",
            parser_version="test",
            subject_options=(
                SubjectOption("CSCI", "Computer Science"),
                SubjectOption("MATH", "Mathematics"),
            ),
        )

    def tearDown(self) -> None:
        self.store.engine.dispose()

    def test_schedule_query_requires_exact_constraint_section_when_ambiguous(self) -> None:
        result = self.store.compute_nonconflicting_sections(
            term_label="Fall 2026",
            subject="CSCI",
            constraint_course="Calculus II",
        )
        self.assertEqual(result["status"], "clarification_required")
        self.assertGreater(len(result["constraintSections"]), 1)
        self.assertIn("Which Calculus II section", result["message"])

    def test_schedule_query_uses_deterministic_meeting_overlap_filter(self) -> None:
        result = self.store.compute_nonconflicting_sections(
            term_label="Fall 2026",
            subject="CSCI",
            constraint_course="Calculus II",
            constraint_section="62001",
        )
        self.assertEqual(result["status"], "complete")
        crns = {section["crn"] for section in result["sections"]}
        self.assertNotIn("61166", crns)
        self.assertIn("61154", crns)

    def test_explicit_class_planner_handoff_keeps_constraint_and_selected_crns(self) -> None:
        result = self.store.compute_nonconflicting_sections(
            term_label="Fall 2026",
            subject="CSCI",
            constraint_course="Calculus II",
            constraint_section="62001",
        )
        selected_crn = str(result["sections"][0]["crn"])
        actions = _planner_actions(
            f"Put CRN {selected_crn} in Class Planner",
            {
                "chunk_dicts": [{
                    "metadata": {
                        "structured_execution": "class_planner_conflict",
                        "result": result,
                    }
                }]
            },
        )
        self.assertEqual(len(actions), 1)
        saved_crns = {section["crn"] for section in actions[0]["sections"]}
        self.assertEqual(saved_crns, {"62001", selected_crn})

    def test_class_planner_handoff_resolves_these_from_latest_user_crns(self) -> None:
        result = self.store.compute_nonconflicting_sections(
            term_label="Fall 2026",
            subject="CSCI",
            constraint_course="Calculus II",
            constraint_section="62001",
        )
        selected_crn = str(result["sections"][0]["crn"])
        actions = _planner_actions(
            "Please put these in Class Planner",
            {
                "chunk_dicts": [{
                    "metadata": {
                        "structured_execution": "class_planner_conflict",
                        "result": result,
                    }
                }]
            },
            [
                {"role": "user", "content": f"Keep CSCI CRN {selected_crn}"},
                {"role": "assistant", "content": "Ready when you are."},
            ],
        )
        self.assertEqual(len(actions), 1)
        saved_crns = {section["crn"] for section in actions[0]["sections"]}
        self.assertEqual(saved_crns, {"62001", selected_crn})


class GovernedOperationalEvidenceTests(unittest.TestCase):
    def _evidence(self, title: str, text: str, group: str, *, evidence_id: str) -> RetrievedEvidence:
        return RetrievedEvidence(
            evidence_id=evidence_id,
            title=title,
            url="https://www.mcneese.edu/example/",
            text=text,
            source_id=evidence_id,
            source_name=title,
            source_tier="A",
            trust_level="official",
            category="service",
            retrieval_channel="structured_specialist",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=1.0,
            metadata={"source_groups": [group]},
        )

    def test_canonical_operational_pages_are_in_their_source_groups(self) -> None:
        cases = {
            "https://www.mcneese.edu/health-services/": "health_services",
            "https://my.mcneese.edu/advising/": "academic_advising",
            "https://www.mcneese.edu/police/university-ids/": "student_id_cards",
            "https://www.mcneese.edu/police/parking/appeals/": "parking_transportation",
            "https://www.mcneese.edu/international/current_students/": "international_services",
        }
        for url, expected in cases.items():
            self.assertIn(expected, source_groups_for(url=url))

    def test_advisor_workflow_requires_banner_and_student_profile_steps(self) -> None:
        query = compile_campus_query(
            "How can I contact my academic advisor if I don't know who my advisor is?"
        )
        generic = self._evidence(
            "Student Central",
            "Contact Student Central and ask about your assigned advisor at 337-475-5065.",
            "academic_advising",
            evidence_id="generic",
        )
        result = evaluate_evidence(query, [generic])
        self.assertFalse(result.passed)
        self.assertIn("advisor_identification_steps", result.missing_fields)

        workflow = self._evidence(
            "Find Your Academic Advisor",
            "Open Banner 9, select the STUDENTS tab, then STUDENT PROFILE. Your academic advisor is listed at the bottom. Call 337-475-5065 if access fails.",
            "academic_advising",
            evidence_id="workflow",
        )
        self.assertTrue(evaluate_evidence(query, [workflow]).passed)

    def test_international_route_rejects_unrelated_academic_appeal_page(self) -> None:
        query = compile_campus_query(
            "I'm an international student and my I-20 will expire before I graduate. What should I do?"
        )
        international = self._evidence(
            "Current International Students",
            "Current international students can use the International Student Guide for visa status questions and contact International Student Services at internationaloffice@mcneese.edu.",
            "international_services",
            evidence_id="international",
        )
        appeal = self._evidence(
            "How to Appeal Academic Suspension",
            "International students may also have financial aid questions about an academic appeal.",
            "academic_standing",
            evidence_id="appeal",
        )
        result = evaluate_evidence(query, [international, appeal])
        self.assertTrue(result.passed)
        self.assertEqual(result.accepted_evidence_ids, ["international"])

    def test_office_query_rejects_other_office_facts_even_from_a_read_page(self) -> None:
        query = compile_campus_query(
            "Where is the International Office, and what time does it close today?"
        )
        international = self._evidence(
            "International Student Services",
            "International Student Services is at 300 Joe Dumars Dr., Room 102. "
            "Call 337-475-5243. Office hours are Monday-Friday 7:30 a.m.-5:00 p.m.",
            "international_services",
            evidence_id="international",
        )
        registrar = self._evidence(
            "Office of the Registrar",
            "The Registrar is at 4435 Ryan Street. Call 337-475-5065. "
            "Hours are Monday-Thursday 7:30 a.m.-5:00 p.m.",
            "registration",
            evidence_id="registrar",
        )
        registrar.metadata["page_read"] = True

        result = evaluate_evidence(query, [international, registrar])

        self.assertTrue(result.passed, result.missing_fields)
        self.assertEqual(result.accepted_evidence_ids, ["international"])

    def test_verified_health_snapshot_satisfies_operational_fields(self) -> None:
        query = compile_campus_query(
            "I'm feeling sick and need to see someone on campus. Where can I get medical help?"
        )
        records = retrieve_registry_records(query.original_query, query)
        health = [item for item in records if item.metadata.get("curated_snapshot")]
        self.assertEqual([item.source_id for item in health], ["CUR-HEALTH-SERVICES"])
        result = evaluate_evidence(query, health)
        self.assertTrue(result.passed, result.missing_fields)

    def test_verified_records_are_not_shared_across_strict_operations(self) -> None:
        query = compile_campus_query(
            "I lost my McNeese ID card. What should I do, where should I go, and is there a replacement fee?"
        )
        records = retrieve_registry_records(query.original_query, query)
        snapshots = [item for item in records if item.metadata.get("curated_snapshot")]
        self.assertEqual([item.source_id for item in snapshots], ["CUR-ID-CARDS"])
        self.assertTrue(evaluate_evidence(query, snapshots).passed)


if __name__ == "__main__":
    unittest.main()
