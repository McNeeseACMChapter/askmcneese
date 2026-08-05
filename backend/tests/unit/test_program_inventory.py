from __future__ import annotations

import unittest
from unittest.mock import patch


class TestProgramInventory(unittest.IsolatedAsyncioTestCase):
    def test_inventory_question_detection(self) -> None:
        from app.services.program_inventory import is_program_inventory_question

        self.assertTrue(
            is_program_inventory_question(
                "How many majors are there for undergraduate at mcneese?"
            )
        )
        self.assertTrue(
            is_program_inventory_question("What undergraduate majors does McNeese offer?")
        )
        self.assertFalse(
            is_program_inventory_question(
                "What courses do I need for the computer science degree plan?"
            )
        )

    def test_classify_routes_majors_count_to_academic_programs(self) -> None:
        from app.services.rccs.classify import INTENT_ACADEMIC_PROGRAMS, classify_retrieval

        result = classify_retrieval(
            "How many majors are there for undergraduate at mcneese?"
        )
        self.assertEqual(result.primary_intent, INTENT_ACADEMIC_PROGRAMS)

    async def test_direct_answer_uses_inventory_count(self) -> None:
        from app.services.llm import _direct_program_inventory_answer
        from app.services.program_inventory import retrieve_undergraduate_program_inventory

        fake_titles = [
            "Accounting",
            "Biology",
            "Computer Science",
            "Nursing (Undergraduate)",
            "Psychology",
            "Early Childhood Education Grades PK-3, PBC",
        ]
        with patch(
            "app.services.program_inventory._fetch_undergraduate_titles_sync",
            return_value=(fake_titles, 6),
        ):
            evidence, err = await retrieve_undergraduate_program_inventory(
                "How many majors are there for undergraduate at mcneese?"
            )
        self.assertIsNone(err)
        self.assertEqual(len(evidence), 1)
        chunk = evidence[0].to_chunk_dict()
        answer = _direct_program_inventory_answer(
            "How many majors are there for undergraduate at mcneese?",
            [chunk],
        )
        self.assertIsNotNone(answer)
        self.assertIn("**5 undergraduate majors**", answer or "")
        self.assertIn("Would you like help finding the best major", answer or "")
        self.assertIn("undergraduate-programs", answer or "")


if __name__ == "__main__":
    unittest.main()
