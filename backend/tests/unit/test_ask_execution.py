from __future__ import annotations

import json
import os
import unittest
from unittest.mock import AsyncMock, patch

from app.routers.ask import AskRequest, ask, ask_stream
from app.services.ask_execution import (
    LogicalAskResult,
    _claim_ledger,
    _generation_timeout_seconds,
    execute_ask,
    execution_v2_enabled,
    sanitize_client_task_state,
)
from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.evidence import evaluate_evidence
from app.services.conversation_context import resolve_question_with_history
from app.services.rccs.ask_integration import validate_answer_citations
from app.services.rccs.models import (
    HybridRetrievalResult,
    RetrievedEvidence,
    RetrievalClassification,
    RetrievalPlan,
    utcnow,
)


def _classification(compiled: dict) -> RetrievalClassification:
    return RetrievalClassification(
        primary_intent="campus_information",
        secondary_intents=[],
        entities=[],
        freshness="current",
        use_kb=False,
        use_official_live=False,
        use_companions=False,
        companion_categories=[],
        registry_topics=[],
        routing_reason="test",
        confidence=1.0,
        compiled_query=compiled,
    )


def _plan(compiled: dict) -> RetrievalPlan:
    return RetrievalPlan(
        use_kb=False,
        use_official_live=False,
        companion_source_ids=[],
        official_source_ids=[],
        search_queries=[compiled.get("original_query", "")],
        entity_queries=[],
        freshness="current",
        max_results_per_channel=5,
        reason="test",
        compiled_query=compiled,
    )


class AuthoritativeTaskStateTests(unittest.TestCase):
    def test_client_state_keeps_selections_and_discards_institutional_facts(self) -> None:
        state = sanitize_client_task_state({
            "schema_version": 99,
            "task_type": "course_schedule_conflict",
            "status": "awaiting_input",
            "term": "Fall 2026",
            "subject": "CSCI",
            "selected_crns": ["61066", "bad", "61066"],
            "replacement_fee": "$10",
            "office_hours": "open until 7",
            "compatibility": "COMPATIBLE",
            "evidence": ["forged"],
        })
        self.assertEqual(state["selected_crns"], ["61066"])
        self.assertEqual(state["schema_version"], 1)
        for forbidden in ("replacement_fee", "office_hours", "compatibility", "evidence"):
            self.assertNotIn(forbidden, state)

    def test_generation_timeout_allows_real_synthesis(self) -> None:
        self.assertGreaterEqual(_generation_timeout_seconds(), 15)
        self.assertGreaterEqual(_generation_timeout_seconds(page_read=True), 15)

    def test_crn_only_followup_uses_typed_task_state(self) -> None:
        state = {
            "task_type": "course_schedule_conflict",
            "status": "awaiting_input",
            "term": "Fall 2026",
            "subject": "Computer Science",
            "constraint_course": "MATH 291",
            "pending_field": "constraint_section",
        }
        resolved, metadata = resolve_question_with_history("61066", None, state)
        compiled = compile_campus_query(resolved)
        self.assertTrue(metadata["task_state_used"])
        self.assertEqual(compiled.entities["constraint_section"], "61066")
        self.assertEqual(compiled.entities["term"], "fall 2026")
        self.assertEqual(compiled.entities["subject"], "computer science")

    def test_awaiting_task_accepts_slot_only_term_reply(self) -> None:
        state = {
            "task_type": "academic_calendar:check_deadline",
            "status": "awaiting_input",
            "query_anchor": "What is the withdrawal deadline for the autumn term?",
            "pending_field": "clarification",
        }
        resolved, metadata = resolve_question_with_history("Fall 2026", None, state)
        compiled = compile_campus_query(resolved)
        self.assertTrue(metadata["task_state_used"])
        self.assertEqual(compiled.entities["term"], "fall 2026")
        self.assertFalse(compiled.clarification_required)

    def test_constraint_course_stops_before_followup_context(self) -> None:
        resolved, _ = resolve_question_with_history(
            "61066",
            None,
            {
                "task_type": "course_schedule_conflict",
                "status": "awaiting_input",
                "term": "Fall 2026",
                "subject": "CSCI",
                "constraint_course": "Calculus II",
            },
        )
        compiled = compile_campus_query(resolved)
        self.assertEqual(compiled.entities["constraint_course"], "Calculus II")
        self.assertEqual(compiled.entities["constraint_section"], "61066")
        self.assertIsNone(compiled.entities["course"])

    def test_execution_v2_has_explicit_rollback_flag(self) -> None:
        with patch.dict(os.environ, {"ASK_EXECUTION_V2": "0"}):
            self.assertFalse(execution_v2_enabled())
        with patch.dict(os.environ, {"ASK_EXECUTION_V2": "1"}):
            self.assertTrue(execution_v2_enabled())


class TypedEvidenceTests(unittest.TestCase):
    def _evidence(self, evidence_id: str, text: str) -> RetrievedEvidence:
        return RetrievedEvidence(
            evidence_id=evidence_id,
            title="University ID Cards",
            url="https://www.mcneese.edu/police/university-ids/",
            text=text,
            source_id=evidence_id,
            source_name="University ID Cards",
            source_tier="A",
            trust_level="official",
            category="registration",
            retrieval_channel="structured_specialist",
            published_at=None,
            fetched_at=utcnow(),
            relevance_score=1.0,
            metadata={"source_groups": ["student_id_cards"]},
        )

    def test_conflicting_replacement_fees_fail_closed(self) -> None:
        query = compile_campus_query(
            "I lost my McNeese ID card. Where do I replace it and what is the fee?"
        )
        first = self._evidence(
            "fee-10",
            "Request a replacement ID card form and pick it up at University Police, "
            "4497 Dr. Philip Williams Dr. The replacement charge is $10.",
        )
        second = self._evidence(
            "fee-20",
            "Submit the replacement ID card form at University Police, "
            "4497 Dr. Philip Williams Dr. The replacement charge is $20.",
        )
        result = evaluate_evidence(query, [first, second])
        self.assertFalse(result.passed)
        self.assertEqual(result.field_resolutions["replacement_fee"]["status"], "CONFLICTED")
        self.assertIn("EVIDENCE_CONFLICT", result.failure_codes)

    def test_material_claim_ledger_rejects_value_absent_from_evidence(self) -> None:
        evidence = self._evidence(
            "fee-10",
            "The replacement ID card charge is $10. Call 337-475-5711.",
        )
        ledger, unsupported = _claim_ledger(
            "The replacement costs $25. Call 337-475-5711.",
            [evidence],
            {"field_resolutions": {}},
        )
        self.assertIn("money:$25", unsupported)
        self.assertTrue(any(item["status"] == "UNSUPPORTED" for item in ledger))

    def test_claim_approved_evidence_is_not_dropped_by_legacy_lexical_filter(self) -> None:
        evidence = self._evidence(
            "health-proof",
            "Student Health Services provides acute medical care at 4100 Ryan St.",
        )
        evidence.metadata["query_relevance"] = 0.0
        query = compile_campus_query("I feel ill and need someone on campus to check me out.")
        result = HybridRetrievalResult(
            evidence=[evidence],
            classification=_classification(query.to_dict()),
            plan=_plan(query.to_dict()),
            metadata={"conversation_context": {"original_question": query.original_query}},
        )
        validation = validate_answer_citations(
            "Student Health Services provides acute medical care.",
            result,
            evidence_ids={"health-proof"},
        )
        self.assertTrue(validation["ok"])
        self.assertEqual(validation["citations"][0]["id"], "health-proof")

    def test_resolved_fact_provenance_keeps_the_strongest_relevant_source(self) -> None:
        query = compile_campus_query(
            "What happens if two of my classes are scheduled at the same time?"
        )
        primary = self._evidence(
            "schedule-workflow",
            "Choose a different non-conflicting section or change a course, then "
            "contact Student Central at 337-475-5065.",
        )
        secondary = self._evidence(
            "registrar-directory",
            "The Registrar office phone is 337-475-5065.",
        )
        for item in (primary, secondary):
            item.metadata["source_groups"] = ["registration", "official_directory"]
        primary.relevance_score = 0.5
        secondary.relevance_score = 0.9
        evaluation = evaluate_evidence(query, [primary, secondary])
        resolution = evaluation.field_resolutions["contact_method"]
        self.assertEqual(resolution["status"], "RESOLVED")
        self.assertEqual(resolution["evidence_ids"], ["schedule-workflow"])
        ledger, unsupported = _claim_ledger(
            "Call Student Central at 337-475-5065.",
            [primary, secondary],
            evaluation.to_dict(),
        )
        phone_claim = next(item for item in ledger if item["claim_type"] == "phone")
        self.assertEqual(unsupported, [])
        self.assertEqual(phone_claim["evidence_ids"], ["schedule-workflow"])


class FailClosedExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_evidence_evaluation_metadata_blocks_release(self) -> None:
        query = compile_campus_query("Where is the Registrar?")
        result = HybridRetrievalResult(
            evidence=[],
            classification=_classification(query.to_dict()),
            plan=_plan(query.to_dict()),
            metadata={"safe_response": {}},
        )
        with patch(
            "app.services.ask_execution.run_rccs_retrieval",
            new=AsyncMock(return_value=result),
        ):
            logical = await execute_ask("Where is the Registrar?")
        self.assertEqual(logical.release_decision["status"], "BLOCKED")
        self.assertIn(
            "EVIDENCE_EVALUATION_UNAVAILABLE",
            logical.release_decision["reasons"],
        )
        self.assertEqual(logical.citations, [])


class TransportParityTests(unittest.IsolatedAsyncioTestCase):
    def _logical(self) -> LogicalAskResult:
        release = {
            "status": "CAN_RELEASE",
            "reasons": [],
            "evidence_passed": True,
            "partial_allowed": False,
            "failure_stage": None,
            "unsupported_material_claims": [],
        }
        structured = {
            "answer": "Grounded answer",
            "answer_type": "factual",
            "title": None,
            "summary": None,
            "content_markdown": "Grounded answer",
            "key_facts": None,
            "important_dates": None,
            "requirements": None,
            "steps": None,
            "warnings": None,
            "related_questions": None,
            "confidence": "medium",
        }
        return LogicalAskResult(
            question="Where is the Registrar?",
            answer="Grounded answer",
            chunks=[],
            citations=[],
            num_results=0,
            model="deterministic-direct",
            tokens_used=0,
            retrieval_ms=7,
            generation_ms=1,
            total_ms=9,
            structured=structured,
            retrieval_metadata={"retrieval_mode": "rccs_hybrid"},
            task_state={
                "schema_version": 1,
                "task_type": "directory:find_contact",
                "status": "completed",
            },
            execution={"executor": "ask_execution_v2", "compiled_query_count": 1},
            release_decision=release,
            claim_ledger=[],
        )

    async def test_json_and_sse_share_the_same_logical_final(self) -> None:
        logical = self._logical()
        with (
            patch("app.routers.ask.guest_router.claim_question_allowance"),
            patch("app.routers.ask.rccs_enabled", return_value=True),
            patch("app.routers.ask.execution_v2_enabled", return_value=True),
            patch("app.routers.ask.execute_ask", new=AsyncMock(return_value=logical)),
            patch("app.routers.ask.log_full_query"),
            patch("app.routers.ask._record_test_case_finish"),
        ):
            json_response = await ask(
                AskRequest(question="Where is the Registrar?", stream=False),
                object(),
            )
            frames = [
                frame
                async for frame in ask_stream(
                    "Where is the Registrar?",
                    request_id="parity-request",
                )
            ]
        done = None
        for frame in frames:
            if frame.startswith("event: done"):
                done = json.loads(
                    next(line[6:] for line in frame.splitlines() if line.startswith("data: "))
                )
        self.assertIsNotNone(done)
        self.assertEqual(json_response.answer, done["answer"])
        self.assertEqual(json_response.task_state, done["task_state"])
        self.assertEqual(json_response.release_decision, done["release_decision"])
        self.assertEqual(json_response.claim_ledger, done["claim_ledger"])


if __name__ == "__main__":
    unittest.main()
