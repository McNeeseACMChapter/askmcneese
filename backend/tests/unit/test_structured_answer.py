"""Unit tests for best-effort structured answer extraction."""

import unittest

from app.services.structured_answer import structure_answer


class TestStructuredAnswer(unittest.TestCase):
    def test_infers_deadline_and_preserves_markdown(self) -> None:
        answer = (
            "# Scholarship Dates\n\n"
            "Applications are available for incoming students.\n\n"
            "- **Deadline:** February 1\n"
        )
        result = structure_answer(
            question="What is the scholarship deadline?",
            answer=answer,
            num_results=2,
            model="test-model",
        )

        self.assertEqual(result["answer_type"], "deadline")
        self.assertEqual(result["content_markdown"], answer)
        self.assertEqual(
            result["important_dates"],
            [{"label": "Deadline", "value": "February 1"}],
        )

    def test_person_query_not_deadline_from_bio_dates(self) -> None:
        answer = (
            "Prince started in Fall 2024 and ends his term next semester. "
            "He is Project Manager at ACM."
        )
        result = structure_answer(
            question="Can you search LinkedIn and find who is Prince Pudasaini at McNeese?",
            answer=answer,
            num_results=3,
        )
        self.assertNotEqual(result["answer_type"], "deadline")
        self.assertIn(result["answer_type"], {"factual", "partial"})

    def test_infers_process_from_ordered_steps(self) -> None:
        answer = "Follow these instructions:\n\n1. Create an account.\n2. Submit the form."
        result = structure_answer(
            question="What should I do?",
            answer=answer,
            num_results=2,
        )

        self.assertEqual(result["answer_type"], "process")
        self.assertEqual(result["steps"], ["Create an account.", "Submit the form."])
        self.assertEqual(result["content_markdown"], answer)

    def test_infers_no_source(self) -> None:
        answer = "I couldn't find relevant information in the knowledge base."
        result = structure_answer(
            question="Is this available?",
            answer=answer,
            num_results=0,
        )

        self.assertEqual(result["answer_type"], "no_source")
        self.assertEqual(result["content_markdown"], answer)

    def test_does_not_invent_facts_absent_from_text(self) -> None:
        answer = "McNeese offers support for students."
        result = structure_answer(
            question="Tell me about student support.",
            answer=answer,
            num_results=1,
        )

        self.assertIsNone(result["key_facts"])
        self.assertIsNone(result["important_dates"])
        self.assertIsNone(result["requirements"])
        self.assertIsNone(result["steps"])
        self.assertIsNone(result["warnings"])
        self.assertIsNone(result["related_questions"])
        self.assertEqual(result["content_markdown"], answer)

    def test_simple_phone_question_skips_supporting_sections(self) -> None:
        answer = "The main McNeese phone number is **337-475-5000**."
        result = structure_answer(
            question="What is McNeese's main phone number?",
            answer=answer,
            num_results=1,
        )
        self.assertEqual(result["answer_type"], "location")
        self.assertIsNone(result["key_facts"])
        self.assertIsNone(result["requirements"])
        self.assertIsNone(result["steps"])

    def test_process_keeps_multi_steps(self) -> None:
        answer = (
            "Change your major as follows:\n\n"
            "1. Meet your advisor.\n"
            "2. Submit the change-of-major form.\n"
            "3. Confirm the update in Banner.\n"
        )
        result = structure_answer(
            question="How do I change my major?",
            answer=answer,
            num_results=2,
        )
        self.assertEqual(result["answer_type"], "process")
        self.assertEqual(len(result["steps"] or []), 3)


if __name__ == "__main__":
    unittest.main()
