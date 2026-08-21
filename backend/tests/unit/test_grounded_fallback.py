import unittest

from app.services.grounded_fallback import direct_navigation_answer, render_grounded_fallback


class GroundedFallbackTests(unittest.TestCase):
    def test_named_book_uses_official_store_without_claiming_stock(self):
        answer = render_grounded_fallback(
            "Where can I buy the Hero of Island book?",
            [
                {
                    "title": "McNeese Cowboy Store",
                    "source_url": "https://mcneesecowboystore.com/HOME",
                    "retrieval_channel": "structured_specialist",
                }
            ],
            {
                "campus_query": {
                    "domain": "student_services",
                    "subdomain": "bookstore",
                    "entities": {"item": "hero of island"},
                }
            },
        )
        self.assertIn("could not confirm a current listing", answer)
        self.assertIn("McNeese Cowboy Store", answer)
        self.assertIn("author or ISBN", answer)
        self.assertNotIn("capabilities", answer.lower())

    def test_live_product_matches_are_labeled_as_possible(self):
        answer = render_grounded_fallback(
            "Where can I buy this book?",
            [
                {
                    "title": "Hero Island by Example Author",
                    "source_url": "https://books.example/hero-island",
                    "retrieval_channel": "web_live",
                }
            ],
            {
                "campus_query": {
                    "domain": "student_services",
                    "subdomain": "bookstore",
                    "entities": {"item": "hero island"},
                }
            },
        )
        self.assertIn("possible current matches", answer)
        self.assertIn("author or ISBN", answer)

    def test_link_only_navigation_finishes_without_llm(self):
        safe = {
            "campus_query": {
                "domain": "student_services",
                "subdomain": "bookstore",
                "action": "navigate",
                "entities": {"item": "hero of island"},
            }
        }
        answer = direct_navigation_answer(
            "Where can I buy the Hero of Island book?",
            [
                {
                    "title": "McNeese Cowboy Store",
                    "source_url": "https://mcneesecowboystore.com/HOME",
                    "retrieval_channel": "structured_specialist",
                    "is_link_only": True,
                }
            ],
            safe,
        )
        self.assertIsNotNone(answer)
        self.assertIn("McNeese Cowboy Store", answer or "")
        self.assertIsNone(
            direct_navigation_answer(
                "Where can I buy it?",
                [{"source_url": "https://example.com", "is_link_only": False}],
                safe,
            )
        )

    def test_employment_partial_lists_verified_portals_without_inventing_jobs(self):
        answer = render_grounded_fallback(
            "What jobs are available right now?",
            [
                {
                    "title": "McNeese Employment",
                    "source_url": "https://www.mcneese.edu/hr/employment/",
                },
                {
                    "title": "Student Employment",
                    "source_url": "https://www.mcneese.edu/student-employment/",
                },
            ],
            {"campus_query": {"domain": "employment"}},
        )
        self.assertIn("will not invent vacancies", answer)
        self.assertIn("McNeese Employment", answer)
        self.assertIn("Student Employment", answer)

    def test_page_read_fallback_quotes_extracted_section(self) -> None:
        answer = render_grounded_fallback(
            "exact steps to apply as an international student",
            [
                {
                    "title": "Apply",
                    "source_url": "https://www.mcneese.edu/admissions/apply/",
                    "retrieval_channel": "official_live",
                    "is_link_only": False,
                    "metadata": {"page_read": True},
                    "text": (
                        "I'm An International Student\n"
                        "Pay a nonrefundable application fee of $30. "
                        "Submit official transcripts and a signed affidavit."
                    ),
                }
            ],
            {"campus_query": {"domain": "admissions", "intent": "apply"}},
        )
        self.assertIn("I'm An International Student", answer)
        self.assertIn("application fee of $30", answer)
        self.assertIn("https://www.mcneese.edu/admissions/apply/", answer)
        self.assertNotIn("could not complete a full synthesis", answer)

    def test_kb_text_without_page_read_flag_is_still_quoted(self) -> None:
        answer = render_grounded_fallback(
            "Where is Student Central?",
            [
                {
                    "title": "Student Central",
                    "source_url": "https://www.mcneese.edu/student-central/",
                    "retrieval_channel": "kb",
                    "is_link_only": False,
                    "text": (
                        "Student Central is located at 4435 Ryan St, Lake Charles, LA 70605. "
                        "Call +1-337-475-5065 or email studentcentral@mcneese.edu."
                    ),
                },
                {
                    "title": "Apply",
                    "source_url": "https://www.mcneese.edu/admissions/apply/",
                    "retrieval_channel": "structured_specialist",
                    "is_link_only": True,
                    "text": "Governed campus source record. Official owner/destination: apply.",
                },
            ],
            {"campus_query": {"domain": "admissions", "intent": "find_contact"}},
        )
        self.assertIn("4435 Ryan St", answer)
        self.assertIn("337-475-5065", answer)
        self.assertNotIn("could not complete a full synthesis", answer)
        self.assertNotIn("Governed campus source record", answer)

    def test_calendar_fallback_returns_the_requested_dates_not_the_table(self) -> None:
        answer = render_grounded_fallback(
            "When does the Summer 2026 semester end?",
            [
                {
                    "title": "Summer 2026",
                    "source_url": "https://www.mcneese.edu/registrar/schedule/summer-2026/",
                    "category": "academic_calendar",
                    "retrieval_channel": "official_live",
                    "is_link_only": False,
                    "metadata": {"page_fetched": True},
                    "text": (
                        "- 337-475-5065\n\n"
                        "| Regular Summer Session | |\n"
                        "| --- | --- |\n"
                        "| Classes begin | June 10 |\n"
                        "| Classes end | July 21 |\n"
                        "| Final examinations begin | July 23 |\n"
                        "| Final examinations end | July 24 |\n"
                        "| Summer Session 13S | |\n"
                        "| --- | --- |\n"
                        "| Session 13S classes end | August 7 |"
                    ),
                }
            ],
            {"campus_query": {"domain": "academic_calendar", "intent": "check_deadline"}},
        )
        self.assertIn("Tuesday, July 21, 2026", answer)
        self.assertIn("Friday, July 24, 2026", answer)
        self.assertNotIn("| Classes begin |", answer)
        self.assertNotIn("337-475-5065", answer)


if __name__ == "__main__":
    unittest.main()
