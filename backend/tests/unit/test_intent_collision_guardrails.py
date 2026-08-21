import unittest

from app.services.capabilities import is_capability_question
from app.services.campus_intelligence.compiler import compile_campus_query
from app.services.campus_intelligence.route_policy import resolve_route_policy
from app.services.intent import Intent, classify_intent
from app.services.rccs.classify import classify_retrieval
from app.services.rccs.hybrid import _planned_search_phrases
from app.services.rccs.plan import build_retrieval_plan


class IntentCollisionGuardrailTests(unittest.TestCase):
    def test_operational_can_i_prompts_never_become_product_capabilities(self):
        questions = (
            "Where can I buy the Hero of Island book?",
            "Can I buy a parking pass?",
            "Can I find tutoring on campus?",
            "Where can I find the transcript form?",
            "Can I submit an academic suspension appeal?",
            "Can I contact Dr. Vipin Menon?",
            "How can I apply for admission?",
            "What can I purchase at the bookstore?",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(is_capability_question(question))
                self.assertNotEqual(
                    compile_campus_query(question).domain,
                    "capability_discovery",
                )

    def test_genuine_product_self_knowledge_stays_deterministic(self):
        questions = (
            "What can you answer?",
            "What kinds of McNeese questions can you help me with?",
            "Show me your capabilities.",
            "What can I ask you about?",
            "Can you do web search?",
            "Do you have internet access?",
            "What sources do you use?",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(is_capability_question(question))
                self.assertEqual(
                    compile_campus_query(question).domain,
                    "capability_discovery",
                )

    def test_book_purchase_is_a_live_bookstore_operation(self):
        compiled = compile_campus_query(
            "Where can I buy the Hero of Island book?"
        )
        self.assertEqual(compiled.domain, "student_services")
        self.assertEqual(compiled.subdomain, "bookstore")
        self.assertEqual(compiled.intent, "check_availability")
        self.assertEqual(compiled.action, "navigate")
        self.assertEqual(compiled.freshness, "live")
        self.assertTrue(compiled.requires_live_discovery)
        self.assertEqual(compiled.required_source_groups, ["bookstore"])
        self.assertEqual(compiled.entities["item"], "hero of island")
        policy = resolve_route_policy(compiled)
        self.assertEqual(policy.template, "live_fact")
        self.assertNotEqual(policy.channels["agentic_web"].state, "FORBIDDEN")
        question = "Where can I buy the Hero of Island book?"
        plan = build_retrieval_plan(
            classify_retrieval(question),
            question=question,
        )
        self.assertFalse(plan.use_kb)
        self.assertTrue(plan.use_official_live)
        self.assertEqual(plan.official_source_ids, ["SRC-027", "SRC-035"])
        phrases = _planned_search_phrases(question, plan)
        self.assertEqual(phrases[0][1], ["mcneesecowboystore.com"])
        self.assertEqual(phrases[0][2], "official_first")
        self.assertIsNone(phrases[1][1])
        self.assertEqual(phrases[1][2], "external_discovery")

    def test_resolved_subdomains_do_not_fan_out_to_sibling_connectors(self):
        cases = (
            ("Where can I apply for campus housing?", ["housing"]),
            ("Where is the dining hall?", ["dining"]),
            ("What student jobs are available?", ["student_employment", "official_employment"]),
            ("How do I contact counseling?", ["counseling"]),
        )
        for question, expected in cases:
            with self.subTest(question=question):
                self.assertEqual(
                    compile_campus_query(question).required_source_groups,
                    expected,
                )

    def test_identity_shortcut_requires_a_complete_identity_utterance(self):
        genuine = ("Who are you?", "What do you do?", "Help me")
        factual = (
            "What is this book about?",
            "Help me find the registrar form.",
            "What are you doing to find current jobs?",
            "Tell me your name and office location at McNeese.",
        )
        for question in genuine:
            with self.subTest(question=question):
                self.assertEqual(classify_intent(question).intent, Intent.IDENTITY)
        for question in factual:
            with self.subTest(question=question):
                self.assertEqual(classify_intent(question).intent, Intent.QUESTION)


if __name__ == "__main__":
    unittest.main()
