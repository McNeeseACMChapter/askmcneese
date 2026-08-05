from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.people_retrieval import _matching_directory_block
from app.services.rccs.classify import (
    INTENT_CAREER_SERVICES,
    INTENT_COURSE_CATALOG,
    INTENT_FACULTY_IDENTITY,
    INTENT_FORM_LOOKUP,
    INTENT_POLICY_PROCEDURE,
    classify_retrieval,
)
from app.services.rccs.evidence import has_sufficient_evidence
from app.services.rccs.models import RetrievedEvidence, utcnow
from app.services.web_search import fetch_page_content


def _evidence(text: str, title: str = "McNeese source") -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id="ev-test",
        title=title,
        url="https://www.mcneese.edu/test/",
        text=text,
        source_id="TEST",
        source_name=title,
        source_tier="A",
        trust_level="official",
        category="test",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.9,
    )


class TestCapabilityRouting(unittest.TestCase):
    def test_actionable_questions_route_to_authoritative_live_paths(self):
        cases = {
            "Where is the form to change my major?": INTENT_FORM_LOOKUP,
            "How do I sign into Handshake to apply for internships?": INTENT_CAREER_SERVICES,
            "Who is Mitchell Morgan at McNeese?": INTENT_FACULTY_IDENTITY,
            "What is MATH 190 and what are its prerequisites?": INTENT_COURSE_CATALOG,
            "How do I withdraw from all my courses?": INTENT_POLICY_PROCEDURE,
            "How do I report sexual misconduct?": INTENT_POLICY_PROCEDURE,
            "Where is the parking ticket appeal form?": INTENT_FORM_LOOKUP,
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                result = classify_retrieval(question)
                self.assertEqual(result.primary_intent, expected)
                self.assertTrue(result.use_official_live)

    def test_suspension_requires_academic_suspension_coverage(self):
        question = "What does academic suspension mean and where is the appeal form?"
        financial_only = _evidence(
            "Financial aid satisfactory academic progress requires a 2.0 GPA. "
            "Students may submit a financial aid appeal form."
        )
        self.assertFalse(has_sufficient_evidence(question, [financial_only]))
        complete = _evidence(
            "Academic suspension lasts one regular semester after the first suspension. "
            "Submit the academic suspension appeal in Banner Self-Service."
        )
        self.assertTrue(has_sufficient_evidence(question, [complete]))

    def test_course_code_and_person_name_are_hard_requirements(self):
        self.assertFalse(
            has_sufficient_evidence(
                "What are the prerequisites for MATH 190?",
                [_evidence("MATH 191 is Calculus II and requires MATH 190.")],
            )
        )
        self.assertFalse(
            has_sufficient_evidence(
                "Who is Mitchell Morgan?",
                [_evidence("McNeese faculty directory entry for another professor")],
                entity_names=["Mitchell Morgan"],
            )
        )

    def test_directory_parser_returns_exact_person_block(self):
        html = """
        <section><h3>Another Person</h3><p>other@mcneese.edu</p></section>
        <section><h3>Mitchell Morgan</h3><p>Assistant Professor</p>
        <p>mmorgan@mcneese.edu 337-475-5860 Drew Hall, Room 122</p></section>
        """
        block = _matching_directory_block(html, "Mitchell Morgan")
        self.assertIsNotNone(block)
        self.assertIn("mmorgan@mcneese.edu", block or "")
        self.assertNotIn("other@mcneese.edu", block or "")


class TestActionLinkExtraction(unittest.IsolatedAsyncioTestCase):
    async def test_fetcher_preserves_exact_action_links(self):
        html = """
        <html><head><title>Career | McNeese</title></head><body>
        <main><h1>Career Services</h1><p>Students can apply for jobs and internships, upload a resume, build a portfolio, attend events, and contact career advisors.</p>
        <a href="https://mcneese.joinhandshake.com/login">Login to Handshake</a>
        <a href="/news/">News</a></main></body></html>
        """
        with patch(
            "app.services.web_search._fetch_http_html",
            AsyncMock(return_value=("https://www.mcneese.edu/career/", html, "")),
        ):
            page = await fetch_page_content("https://www.mcneese.edu/career/")
        self.assertTrue(page.success)
        self.assertEqual(page.links[0]["url"], "https://mcneese.joinhandshake.com/login")
        self.assertIn("Relevant official action links", page.content)
        self.assertNotIn("https://www.mcneese.edu/news/", page.content)


if __name__ == "__main__":
    unittest.main()
