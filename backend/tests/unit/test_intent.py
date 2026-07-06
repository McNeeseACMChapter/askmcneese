"""Zero-network unit tests for intent classification."""

import unittest

from app.services.intent import Intent, classify_intent


class TestClassifyIntent(unittest.TestCase):
    def test_greeting_hello(self) -> None:
        result = classify_intent("hello")
        self.assertEqual(result.intent, Intent.GREETING)
        self.assertTrue(result.reply)

    def test_campus_question(self) -> None:
        result = classify_intent("What scholarships are available at McNeese?")
        self.assertEqual(result.intent, Intent.QUESTION)
        self.assertEqual(result.reply, "")

    def test_thanks(self) -> None:
        result = classify_intent("thank you")
        self.assertEqual(result.intent, Intent.THANKS)
        self.assertTrue(result.reply)


if __name__ == "__main__":
    unittest.main()
