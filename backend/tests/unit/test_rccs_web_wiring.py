"""Tests for capability contract and web-mode routing intent."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.capabilities import (
    capability_answer_text,
    is_capability_question,
    retrieval_capabilities,
)
from app.services.rccs.classify import classify_retrieval, with_user_web_preference
from app.services.rccs.plan import build_retrieval_plan


class TestCapabilityContract(unittest.TestCase):
    def test_capability_question_detection(self):
        self.assertTrue(is_capability_question("Can you do web search?"))
        self.assertTrue(is_capability_question("Do you have internet access?"))
        self.assertFalse(is_capability_question("What is the tuition deadline?"))

    def test_capability_answer_affirmative(self):
        text = capability_answer_text(use_web_search=True)
        self.assertIn("Yes", text)
        self.assertIn("approved", text.lower())
        self.assertNotIn("I cannot", text)

    def test_capabilities_no_secrets(self):
        caps = retrieval_capabilities()
        blob = str(caps).lower()
        self.assertNotIn("api_key", blob)
        self.assertNotIn("sk-ant", blob)
        self.assertIn("official_web_search_available", caps)


class TestWebModeRouting(unittest.TestCase):
    def test_explicit_web_forces_official_live(self):
        c = classify_retrieval("Tell me about computer science.")
        # Programs default may not want official live
        c2 = with_user_web_preference(c, True)
        self.assertTrue(c2.use_official_live)
        plan = build_retrieval_plan(c2, use_web_search=True, question="Tell me about computer science.")
        self.assertTrue(plan.use_official_live)

    def test_classifier_cannot_cancel_web(self):
        c = classify_retrieval("What is the tuition deadline?")
        c = with_user_web_preference(c, True)
        plan = build_retrieval_plan(c, use_web_search=True, question="What is the tuition deadline?")
        self.assertTrue(plan.use_official_live)
        self.assertEqual(plan.companion_source_ids, [])

    def test_knowledge_mode_admissions_no_companions(self):
        c = classify_retrieval("What is the tuition deadline?")
        plan = build_retrieval_plan(c, use_web_search=False, question="What is the tuition deadline?")
        self.assertEqual(plan.companion_source_ids, [])
        self.assertEqual(plan.companion_categories, [])


class TestUseWebSearchSchema(unittest.TestCase):
    def test_ask_request_defaults_false(self):
        from app.routers.ask import AskRequest

        req = AskRequest(question="Hello campus?")
        self.assertFalse(req.use_web_search)

    def test_ask_request_true(self):
        from app.routers.ask import AskRequest

        req = AskRequest(question="News?", use_web_search=True)
        self.assertTrue(req.use_web_search)

    def test_ask_request_rejects_non_bool_coercion_strings_safely(self):
        from pydantic import ValidationError
        from app.routers.ask import AskRequest

        # Pydantic v2 coerces "true"/"false" strings for bool in some configs;
        # ensure explicit True works and invalid types fail.
        req = AskRequest(question="x", use_web_search=True)
        self.assertIs(req.use_web_search, True)
        with self.assertRaises(ValidationError):
            AskRequest(question="x", use_web_search=["nope"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
