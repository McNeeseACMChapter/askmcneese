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


if __name__ == "__main__":
    unittest.main()
