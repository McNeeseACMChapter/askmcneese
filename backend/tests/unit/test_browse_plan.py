"""Tests for classification-driven browse targets and URL selection."""

from __future__ import annotations

import unittest

from app.services.rccs.browse_plan import build_browse_target, wants_open_web
from app.services.rccs.classify import classify_retrieval
from app.services.rccs.page_open_agent import select_urls_to_open
from app.services.rccs.plan import build_retrieval_plan


class TestBrowsePlan(unittest.TestCase):
    def test_linkedin_prompt_unlocks_social_domains(self) -> None:
        c = classify_retrieval(
            "Can you search linkedin and find who is Prince Pudasaini at McNeese?"
        )
        target = build_browse_target(
            "Can you search linkedin and find who is Prince Pudasaini at McNeese?",
            c,
            use_web_search=True,
        )
        self.assertTrue(target.social)
        self.assertTrue(target.allow_open_web)
        self.assertTrue(any("linkedin.com" in d for d in target.domains))
        self.assertGreater(target.max_pages_to_open, 0)

    def test_scholarship_stays_mcneese_scoped(self) -> None:
        q = "What is the scholarship deadline for freshmen?"
        c = classify_retrieval(q)
        target = build_browse_target(q, c, use_web_search=False)
        self.assertFalse(target.social)
        self.assertTrue(any("mcneese.edu" in d for d in target.domains))
        self.assertFalse(any("linkedin.com" in d for d in target.domains))

    def test_open_web_cues_detected(self) -> None:
        self.assertTrue(wants_open_web("search the web for McNeese ACM officers"))
        self.assertFalse(wants_open_web("What is the library phone number?"))

    def test_plan_carries_browse_fields(self) -> None:
        q = "search google for Prince Pudasaini McNeese"
        c = classify_retrieval(q)
        plan = build_retrieval_plan(c, use_web_search=True, question=q)
        self.assertTrue(plan.allow_open_web)
        self.assertTrue(len(plan.browse_domains) > 0)

    def test_select_urls_respects_cap(self) -> None:
        c = classify_retrieval("search linkedin for someone at McNeese")
        target = build_browse_target(
            "search linkedin for someone at McNeese",
            c,
            use_web_search=True,
        )
        urls = [
            "https://www.linkedin.com/in/a",
            "https://www.linkedin.com/in/b",
            "https://www.mcneese.edu/x",
            "https://example.com/y",
        ]
        selected = select_urls_to_open(urls, target, limit=2)
        self.assertEqual(len(selected), 2)


if __name__ == "__main__":
    unittest.main()
