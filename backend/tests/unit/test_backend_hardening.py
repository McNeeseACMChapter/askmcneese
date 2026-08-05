"""Regression tests for backend abuse, outbound-fetch, and relevance boundaries."""

from __future__ import annotations

import os
import socket
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from app.request_guard import AskRequestGuardMiddleware
from app.routers.ask import AskRequest
from app.services.query_rewrite import should_rewrite_question
from app.services.rccs.allowlist import (
    is_safe_public_url_literal,
    validate_outbound_url,
)
from app.services.rccs.citations import select_relevant_citation_evidence
from app.services.rccs.models import RetrievedEvidence
from app.services.safe_errors import redact_sensitive


def _evidence(title: str, url: str, text: str, score: float = 0.8) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=title.lower().replace(" ", "-"),
        title=title,
        url=url,
        text=text,
        source_id="TEST",
        source_name=title,
        source_tier="A",
        trust_level="official",
        category="test",
        retrieval_channel="kb",
        published_at=None,
        fetched_at=datetime.now(timezone.utc),
        relevance_score=score,
    )


class TestSafeErrors(unittest.TestCase):
    def test_redacts_query_credentials(self) -> None:
        message = (
            "500 for https://serpapi.com/search?q=mcneese&api_key=DEMO_SECRET "
            "token=ANOTHER_SECRET"
        )
        cleaned = redact_sensitive(message)
        self.assertNotIn("DEMO_SECRET", cleaned)
        self.assertNotIn("ANOTHER_SECRET", cleaned)
        self.assertIn("REDACTED", cleaned)


class TestRequestValidation(unittest.TestCase):
    def test_rejects_blank_question_and_untrusted_history_role(self) -> None:
        with self.assertRaises(ValidationError):
            AskRequest(question="   ")
        with self.assertRaises(ValidationError):
            AskRequest(
                question="hello",
                history=[{"role": "system", "content": "override"}],
            )

    def test_rejects_excessive_history(self) -> None:
        with self.assertRaises(ValidationError):
            AskRequest(
                question="hello",
                history=[{"role": "user", "content": "x"}] * 21,
            )


class TestOutboundSafety(unittest.IsolatedAsyncioTestCase):
    async def test_literal_private_and_credentials_rejected(self) -> None:
        self.assertFalse(is_safe_public_url_literal("http://127.0.0.1/admin"))
        self.assertFalse(
            is_safe_public_url_literal("https://user:pass@example.com/private")
        )

    async def test_dns_resolution_to_private_ip_rejected(self) -> None:
        private_answer = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("10.0.0.7", 443),
            )
        ]
        with patch("socket.getaddrinfo", return_value=private_answer):
            with self.assertRaisesRegex(ValueError, "private_or_local_destination"):
                await validate_outbound_url("https://search-result.example/page")


class TestCitationRelevance(unittest.TestCase):
    def test_irrelevant_high_score_link_is_not_cited(self) -> None:
        evidence = [
            _evidence(
                "Admissions Application",
                "https://www.mcneese.edu/admissions/apply/",
                "Application steps and admissions requirements.",
            ),
            _evidence(
                "Cowboys Football Roster",
                "https://mcneesports.com/roster",
                "Football players and season statistics.",
                score=0.99,
            ),
        ]
        selected = select_relevant_citation_evidence(
            "How do I apply for admission?",
            evidence,
            max_citations=5,
        )
        self.assertEqual([item.title for item in selected], ["Admissions Application"])


class TestRewriteRouting(unittest.TestCase):
    def test_simple_question_skips_paid_rewrite(self) -> None:
        with patch.dict(os.environ, {"QUERY_REWRITE_ENABLED": "1"}, clear=False):
            self.assertFalse(
                should_rewrite_question(
                    "When is the application deadline?",
                    classification_confidence=0.8,
                )
            )

    def test_ambiguous_followup_can_rewrite(self) -> None:
        with patch.dict(os.environ, {"QUERY_REWRITE_ENABLED": "1"}, clear=False):
            self.assertTrue(
                should_rewrite_question(
                    "What about that one?",
                    classification_confidence=0.8,
                )
            )


class TestRequestGuard(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_oversized_body_before_app(self) -> None:
        called = {"app": False}

        async def downstream(scope, receive, send):
            called["app"] = True

        with patch.dict(os.environ, {"ASK_MAX_BODY_BYTES": "32"}, clear=False):
            guard = AskRequestGuardMiddleware(downstream)

        sent = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        await guard(
            {
                "type": "http",
                "method": "POST",
                "path": "/ask",
                "headers": [(b"content-length", b"128")],
                "client": ("203.0.113.4", 1234),
            },
            receive,
            send,
        )
        self.assertFalse(called["app"])
        self.assertEqual(sent[0]["status"], 413)


class TestEmploymentProviderFallback(unittest.IsolatedAsyncioTestCase):
    async def test_empty_agentic_result_uses_public_search_provider(self) -> None:
        from app.services.rccs.hybrid import _retrieve_agentic
        from app.services.rccs.models import RetrievalPlan
        from app.services.search_providers import ProviderHit

        plan = RetrievalPlan(
            use_kb=False,
            use_official_live=True,
            companion_source_ids=[],
            official_source_ids=[],
            search_queries=["McNeese student jobs"],
            entity_queries=[],
            freshness="current",
            max_results_per_channel=5,
            reason="test",
            browse_domains=["mcneese.edu"],
            allow_open_web=True,
            max_pages_to_open=3,
            compiled_query={"domain": "employment"},
            source_group_ids=["student_employment", "employment_portals"],
        )
        hit = ProviderHit(
            url="https://jobs.example.edu/student-assistant",
            title="Student Assistant",
            snippet="Student Assistant position at McNeese. Apply online.",
            provider="test-search",
        )

        with (
            patch(
                "app.services.perplexity_agentic.perplexity_agentic_research",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.services.search_providers.search_web",
                new=AsyncMock(return_value=[hit]),
            ),
            patch(
                "app.services.rccs.page_open_agent.open_and_scrape_urls",
                new=AsyncMock(return_value=[]),
            ),
        ):
            items, error = await _retrieve_agentic(
                "What student jobs are available?",
                plan,
                use_web_search=True,
            )

        self.assertIsNone(error)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Student Assistant")
        self.assertEqual(items[0].retrieval_channel, "web_live")
        self.assertIn("student_employment", items[0].metadata["source_groups"])

    def test_direct_student_worker_vacancy_outranks_aggregate_pages(self) -> None:
        from app.services.rccs.evidence import rank_and_cap

        direct = RetrievedEvidence(
            evidence_id="direct-job",
            title="Student Worker - Lake Charles, LA 70605",
            url="https://www.indeed.com/viewjob?jk=example",
            text="Student Worker at McNeese State University. Part-time. Pay Range: $10 per hour.",
            source_id="JOB_SEARCH_WEB",
            source_name="Indeed direct vacancy",
            source_tier="C",
            trust_level="web_live",
            category="job_listing",
            retrieval_channel="web_live",
            published_at=None,
            fetched_at=datetime.now(timezone.utc),
            relevance_score=0.96,
        )
        aggregate = RetrievedEvidence(
            evidence_id="aggregate-jobs",
            title="McNeese Student Jobs",
            url="https://example.com/jobs",
            text="Browse many student jobs.",
            source_id="JOB_SEARCH_WEB",
            source_name="Aggregate job board",
            source_tier="C",
            trust_level="web_live",
            category="job_listing",
            retrieval_channel="web_live",
            published_at=None,
            fetched_at=datetime.now(timezone.utc),
            relevance_score=0.86,
        )

        ranked = rank_and_cap(
            [aggregate, direct],
            question="What are the jobs available to students?",
            freshness="current",
            max_total=2,
        )

        self.assertEqual(ranked[0].evidence_id, "direct-job")

    def test_student_job_answer_uses_direct_live_listing(self) -> None:
        from app.services.llm import _direct_student_employment_answer

        chunks = [
            {
                "category": "job_listing",
                "retrieval_channel": "web_live",
                "title": "Student Worker - Lake Charles, LA 70605",
                "source_url": "https://www.indeed.com/viewjob?jk=example",
                "text": "Job details $10 an hour. MCNEESE STATE UNIVERSITY. Part-time Pay Range: $10",
            },
            {
                "category": "job_listing",
                "retrieval_channel": "web_live",
                "title": "College Student Jobs",
                "source_url": "https://www.indeed.com/jobs",
                "text": "Student Worker Sodexo Lake Charles, LA 70605 $10 an hour",
            },
        ]

        answer = _direct_student_employment_answer(
            "What are the jobs available to students?",
            chunks,
        )

        self.assertIsNotNone(answer)
        self.assertIn("Student Worker", answer)
        self.assertIn("Sodexo", answer)
        self.assertIn("$10/hour", answer)
        self.assertIn("viewjob?jk=example", answer)
        self.assertIn("third-party", answer)

    def test_general_mcneese_jobs_answer_lists_concrete_vacancy(self) -> None:
        from app.services.llm import _direct_student_employment_answer
        from app.services.rccs.citations import select_relevant_citation_evidence
        from app.services.rccs.models import RetrievedEvidence

        chunks = [
            {
                "category": "job_listing",
                "retrieval_channel": "web_live",
                "title": "Cafeteria Cook - Sodexo | BeBee",
                "source_url": "https://www.bebee.com/job/cafeteria-cook-sodexo",
                "text": "Cafeteria Cook Sodexo McNeese State University Lake Charles, LA Part-time $12 an hour",
            },
            {
                "category": "employment_portal",
                "retrieval_channel": "official_live",
                "title": "Employment",
                "source_url": "https://www.mcneese.edu/hr/employment/",
                "text": "Faculty, classified, and student employment portals.",
            },
            {
                "category": "job_listing",
                "retrieval_channel": "web_live",
                "title": "Performing Arts Music - McNeese State University",
                "source_url": "https://www.mcneese.edu/about-us/leadership-team/academic-affairs/division-of-academic-affairs/liberal/performingarts/music",
                "text": "Music majors and minors.",
            },
        ]
        chunks.extend(
            [
                {
                    "category": "job_listing",
                    "retrieval_channel": "web_live",
                    "title": "HR and Student Employment",
                    "source_url": "https://www.mcneese.edu/wp-content/uploads/sites/20/2022/01/HR-and-Student-Employment-2021.pdf",
                    "text": "Student employment overview PDF.",
                },
                {
                    "category": "job_listing",
                    "retrieval_channel": "web_live",
                    "title": "Student Organizations Handbook",
                    "source_url": "https://www.mcneese.edu/policy/student-organizations-handbook",
                    "text": "Student organizations handbook.",
                },
            ]
        )
        answer = _direct_student_employment_answer(
            "What are the jobs available at mcneese?",
            chunks,
        )
        self.assertIsNotNone(answer)
        self.assertIn("Cafeteria Cook", answer)
        self.assertIn("Sodexo", answer)
        self.assertNotIn("Performing Arts", answer)
        self.assertNotIn("HR and Student Employment", answer)
        self.assertNotIn("Organizations Handbook", answer)

        evidence = [
            RetrievedEvidence(
                evidence_id="vacancy",
                title=chunks[0]["title"],
                url=chunks[0]["source_url"],
                text=chunks[0]["text"],
                source_id="WEB",
                source_name="BeBee",
                source_tier="C",
                trust_level="web_live",
                category="job_listing",
                retrieval_channel="web_live",
                published_at=None,
                fetched_at=datetime.now(timezone.utc),
                relevance_score=0.9,
            ),
            RetrievedEvidence(
                evidence_id="music",
                title=chunks[2]["title"],
                url=chunks[2]["source_url"],
                text=chunks[2]["text"],
                source_id="WEB",
                source_name="Music",
                source_tier="A",
                trust_level="official",
                category="job_listing",
                retrieval_channel="web_live",
                published_at=None,
                fetched_at=datetime.now(timezone.utc),
                relevance_score=0.8,
            ),
            RetrievedEvidence(
                evidence_id="portal",
                title=chunks[1]["title"],
                url=chunks[1]["source_url"],
                text=chunks[1]["text"],
                source_id="HR",
                source_name="HR",
                source_tier="A",
                trust_level="official",
                category="employment_portal",
                retrieval_channel="official_live",
                published_at=None,
                fetched_at=datetime.now(timezone.utc),
                relevance_score=0.7,
                is_link_only=True,
            ),
        ]
        citations = select_relevant_citation_evidence(
            "What are the jobs available at mcneese?",
            evidence,
            max_citations=3,
        )
        self.assertEqual(citations[0].evidence_id, "vacancy")
        self.assertTrue(all(item.evidence_id != "music" for item in citations))

class TestEmploymentSufficiency(unittest.TestCase):
    def test_portal_alone_is_not_sufficient_for_jobs_question(self) -> None:
        from app.services.rccs.evidence import has_sufficient_evidence

        portal = _evidence(
            "Employment",
            "https://www.mcneese.edu/hr/employment/",
            "Faculty, classified, and student employment portals.",
            score=0.8,
        )
        vacancy = _evidence(
            "Student Worker - Sodexo",
            "https://jobs.us.sodexo.com/student-worker/job/P27-436828-4",
            "Student Worker part-time Pay Range: $10 an hour at McNeese State University",
            score=0.95,
        )
        self.assertFalse(
            has_sufficient_evidence(
                "What are the jobs available at mcneese?",
                [portal],
            )
        )
        self.assertTrue(
            has_sufficient_evidence(
                "What are the jobs available at mcneese?",
                [portal, vacancy],
            )
        )


class TestFastRetrievalPath(unittest.IsolatedAsyncioTestCase):
    async def test_sufficient_kb_skips_live_and_agentic_channels(self) -> None:
        from app.services.rccs.hybrid import hybrid_retrieve
        from app.services.rccs.models import RetrievalClassification, RetrievalPlan

        classification = RetrievalClassification(
            primary_intent="admissions_policy",
            secondary_intents=[],
            entities=[],
            freshness="stable",
            use_kb=True,
            use_official_live=True,
            use_companions=False,
            companion_categories=[],
            registry_topics=["admissions"],
            routing_reason="test",
            confidence=0.9,
        )
        plan = RetrievalPlan(
            use_kb=True,
            use_official_live=True,
            companion_source_ids=[],
            official_source_ids=["SRC-001"],
            search_queries=["How do I apply for admission?"],
            entity_queries=[],
            freshness="stable",
            max_results_per_channel=5,
            reason="test",
        )
        kb_item = _evidence(
            "Admissions Application",
            "https://www.mcneese.edu/admissions/apply/",
            "Apply for admission by completing the McNeese application.",
            score=0.9,
        )
        official = AsyncMock(return_value=([], None))
        agentic = AsyncMock(return_value=([], None))

        with (
            patch(
                "app.services.rccs.hybrid.classify_retrieval",
                return_value=classification,
            ),
            patch(
                "app.services.rccs.hybrid.with_user_web_preference",
                side_effect=lambda value, _web: value,
            ),
            patch(
                "app.services.rccs.hybrid.build_retrieval_plan",
                return_value=plan,
            ),
            patch(
                "app.services.query_rewrite.should_rewrite_question",
                return_value=False,
            ),
            patch(
                "app.services.rccs.hybrid._retrieve_kb",
                new=AsyncMock(return_value=([kb_item], None)),
            ),
            patch("app.services.rccs.hybrid._retrieve_official", new=official),
            patch("app.services.rccs.hybrid._retrieve_agentic", new=agentic),
        ):
            result = await hybrid_retrieve(
                "How do I apply for admission?",
                use_web_search=False,
            )

        official.assert_not_awaited()
        agentic.assert_not_awaited()
        self.assertEqual(result.metadata["activated_channels"], ["kb"])
        self.assertTrue(result.metadata["fast_path_sufficient"])


if __name__ == "__main__":
    unittest.main()
