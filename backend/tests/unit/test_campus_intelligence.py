from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.services.capabilities import capability_answer_text, is_capability_question
from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.evidence import evaluate_evidence
from app.services.campus_intelligence.registry import (
    capability_snapshot,
    load_domain_pack_registry,
    load_route_policy_registry,
    load_source_group_registry,
)
from app.services.campus_intelligence.route_policy import resolve_route_policy
from app.services.rccs.models import RetrievedEvidence


def evidence(
    evidence_id: str,
    *,
    title: str,
    text: str,
    source_id: str,
    url: str,
    source_group: str | None = None,
    link_only: bool = False,
) -> RetrievedEvidence:
    metadata = {}
    if source_group:
        metadata["source_group"] = source_group
    return RetrievedEvidence(
        evidence_id=evidence_id,
        title=title,
        url=url,
        text=text,
        source_id=source_id,
        source_name=title,
        source_tier="A",
        trust_level="official",
        category="test",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=datetime.now(timezone.utc),
        relevance_score=0.9,
        is_link_only=link_only,
        metadata=metadata,
    )


class TestCampusQueryCompiler(unittest.TestCase):
    def assert_compiles(self, question: str, domain: str, intent: str, freshness: str):
        compiled = compile_campus_query(question)
        self.assertEqual(compiled.domain, domain, question)
        self.assertEqual(compiled.intent, intent, question)
        self.assertEqual(compiled.freshness, freshness, question)
        self.assertTrue(compiled.answer_shape)
        self.assertGreaterEqual(compiled.confidence, 0.5)
        return compiled

    def test_capability_paraphrases_share_deterministic_domain(self):
        for question in (
            "What can you answer?",
            "What kinds of McNeese questions can you help me with?",
            "Show me your capabilities.",
            "What can I ask you about?",
        ):
            self.assert_compiles(question, "capability_discovery", "capability_discovery", "static")
            self.assertTrue(is_capability_question(question))

    def test_employment_paraphrases_are_live(self):
        cases = (
            "What are the job available at McNeese State University?",
            "Are there any jobs?",
            "Is McNeese hiring?",
            "Show me open positions at McNeese.",
        )
        for question in cases:
            compiled = compile_campus_query(question)
            self.assertEqual(compiled.domain, "employment", question)
            self.assertEqual(compiled.freshness, "live", question)
            self.assertIn(compiled.intent, {"discover", "find_job", "check_availability"})

    def test_admissions_subdomains_and_actions(self):
        general = self.assert_compiles("How do I apply to McNeese?", "admissions", "apply", "live")
        self.assertIn("application_portal", general.required_source_groups)
        international = self.assert_compiles(
            "What documents do international students need?",
            "admissions",
            "find_requirements",
            "term_based",
        )
        self.assertEqual(international.subdomain, "international")
        self.assertEqual(international.audience, "prospective_international_student")
        self.assertEqual(international.required_source_groups[0], "international_admissions")

    def test_representative_domain_operations(self):
        cases = (
            ("When is summer semester 2026 ending?", "academic_calendar", "check_deadline", "term_based"),
            ("What is CSCI 180?", "catalog", "find_course", "term_based"),
            ("What classes are required for computer science?", "degree_requirements", "check_requirements", "term_based"),
            ("Where is the academic suspension appeal form?", "forms", "find_form", "live"),
            ("What is McNeese's academic suspension policy?", "policy", "find_policy", "term_based"),
            ("Who should I contact about financial aid?", "financial_aid", "find_contact", "live"),
            ("How do I reset my password?", "technology", "resolve_problem", "live"),
            ("What clubs are active?", "organizations", "check_availability", "live"),
            ("What is happening on campus?", "events", "find_event", "live"),
            ("When is the next football game?", "athletics", "find_current_information", "live"),
        )
        for args in cases:
            self.assert_compiles(*args)

    def test_people_identity_uses_directory_contract(self):
        compiled = compile_campus_query("Who is Dr Vipin Menon?")
        self.assertEqual(compiled.domain, "directory")
        self.assertEqual(compiled.intent, "identify_person")
        self.assertEqual(compiled.entities["person"], "vipin menon")
        self.assertEqual(compiled.required_fields, ["person", "role", "department"])
        self.assertFalse(compiled.clarification_required)

    def test_single_name_identity_asks_human_clarification(self):
        compiled = compile_campus_query("Who is Dr Nikolas?")
        self.assertTrue(compiled.clarification_required)
        self.assertIn("last name, department, or course", compiled.ambiguities[0])
        from app.services.persona import clarification_question, needs_clarification

        self.assertTrue(needs_clarification("Who is Dr Nikolas?"))
        self.assertEqual(clarification_question("Who is Dr Nikolas?"), compiled.ambiguities[0])

        article_query = "Who is the Dr Nikolas?"
        article_compiled = compile_campus_query(article_query)
        self.assertTrue(article_compiled.clarification_required)
        self.assertTrue(needs_clarification(article_query))
        self.assertIn("Which Dr. Nikolas", clarification_question(article_query))

    def test_historical_leadership_query_uses_directory(self):
        compiled = compile_campus_query("Who was the dean of ENSC department at McNeese?")
        self.assertEqual(compiled.domain, "directory")
        self.assertEqual(compiled.intent, "identify_person")
        self.assertEqual(compiled.entities["office"], "ensc department at mcneese")
        self.assertFalse(compiled.clarification_required)
    def test_personal_status_never_uses_public_freshness(self):
        compiled = compile_campus_query("What is my transcript status?")
        self.assertEqual(compiled.freshness, "personal")
        self.assertEqual(compiled.risk, "high")
        policy = resolve_route_policy(compiled)
        self.assertEqual(policy.channels["authenticated_connector"].state, "REQUIRED")
        self.assertEqual(policy.channels["agentic_web"].state, "FORBIDDEN")


class TestCampusIntelligenceRegistry(unittest.TestCase):
    def test_configuration_is_complete_and_versioned(self):
        packs = load_domain_pack_registry()
        groups = load_source_group_registry()
        policies = load_route_policy_registry()
        self.assertGreaterEqual(len(packs["packs"]), 19)
        self.assertGreaterEqual(len(groups["groups"]), 30)
        self.assertGreaterEqual(len(policies["templates"]), 6)
        for template in policies["templates"].values():
            self.assertEqual(set(template["channels"]), set(policies["channels"]))
            for decision in template["channels"].values():
                self.assertTrue(decision["reason"])

    def test_capability_snapshot_only_uses_implemented_packs(self):
        snapshot = capability_snapshot(runtime={"official_web_search_available": True})
        supported = {
            item["domain_id"]
            for status in ("fully_supported", "live_official", "limited")
            for item in snapshot["domains_by_status"][status]
        }
        self.assertIn("admissions", supported)
        self.assertIn("employment", supported)
        self.assertIn("capability_discovery", supported)
        answer = capability_answer_text()
        self.assertIn("Fully supported", answer)
        self.assertIn("Supported with live official retrieval", answer)
        self.assertIn("Personal records require", answer)

    def test_high_risk_and_action_routes_forbid_agentic_web(self):
        for question in (
            "What is McNeese's academic suspension policy?",
            "Where is the academic suspension appeal form?",
            "Give me the McNeese application link.",
        ):
            policy = resolve_route_policy(compile_campus_query(question))
            self.assertEqual(policy.channels["agentic_web"].state, "FORBIDDEN", question)
            self.assertEqual(policy.channels["governed_official_fetch"].state, "REQUIRED", question)


class TestEvidenceRequirements(unittest.TestCase):
    def test_unrelated_admissions_chunk_is_rejected_for_employment(self):
        query = compile_campus_query("What are the job available at McNeese State University?")
        unrelated = evidence(
            "admissions-1",
            title="Admissions Overview",
            text="Learn about admission requirements and freshman applications.",
            source_id="SRC-002",
            url="https://www.mcneese.edu/admissions/",
            source_group="official_admissions",
        )
        result = evaluate_evidence(query, [unrelated], policy=resolve_route_policy(query))
        self.assertFalse(result.passed)
        self.assertEqual(result.accepted_evidence_ids, [])
        self.assertEqual(result.rejected_evidence[0]["evidence_id"], "admissions-1")
        self.assertIn("NO_MATCHING_RECORDS", result.failure_codes)

    def test_failure_copy_never_leaks_internal_evidence_fields(self):
        from app.services.campus_intelligence.failures import render_precise_failure

        query = compile_campus_query("Who is Dr Vipin Menon?")
        result = evaluate_evidence(query, [], policy=resolve_route_policy(query))
        message = render_precise_failure(query, result)
        lowered = message.lower()
        self.assertNotIn("required field", lowered)
        self.assertNotIn("source group", lowered)
        self.assertNotIn("route", lowered)
        self.assertIn("department", lowered)
    def test_verified_employment_portal_supports_precise_partial(self):
        query = compile_campus_query("What are the job available at McNeese State University?")
        portal = evidence(
            "employment-1",
            title="McNeese Employment",
            text=(
                "Employment categories and current application portal. "
                "Relevant official action links found on this page:\n"
                "- Apply for positions: https://example.invalid/careers"
            ),
            source_id="ECO-936B1481E4179D",
            url="https://www.mcneese.edu/hr/employment/",
            source_group="official_employment",
            link_only=True,
        )
        result = evaluate_evidence(query, [portal], policy=resolve_route_policy(query))
        self.assertTrue(result.partial_allowed)
        self.assertIn("employment-1", result.accepted_evidence_ids)
        self.assertTrue(result.field_coverage["category"])
        self.assertTrue(result.field_coverage["last_verified"])


if __name__ == "__main__":
    unittest.main()
