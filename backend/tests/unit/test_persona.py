"""Zero-network unit tests for persona detection."""

import unittest

from app.services.persona import detect_persona


class TestDetectPersona(unittest.TestCase):
    def test_international_student_wording(self) -> None:
        persona = detect_persona("How do I apply for an international scholarship?")
        self.assertEqual(persona, "international student")

    def test_transfer_applicant_wording(self) -> None:
        persona = detect_persona("What are the transfer admission requirements?")
        self.assertEqual(persona, "transfer")

    def test_neutral_no_persona_inferred(self) -> None:
        persona = detect_persona("Where is the library on campus?")
        self.assertIsNone(persona)


if __name__ == "__main__":
    unittest.main()
