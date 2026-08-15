import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.academic_calendar import (
    academic_schedule_url_candidates,
    resolve_academic_term,
)
from app.services.academic_calendar_answer import direct_academic_calendar_answer
from app.services.rccs.academic_calendar_retrieval import retrieve_academic_calendar
from app.services.rccs.classify import classify_retrieval
from app.services.rccs.plan import build_retrieval_plan
from app.services.search_providers import _site_scoped_query
from app.services.web_search import FetchedPage


FALL_PAGE = """
| AUGUST 2026 |  |  |
| --- | --- | --- |
| 23 | Sunday | Freshman Convocation |
| 24 | Monday | Classes begin |
| 25 | Tuesday | Last date to register, add/drop courses |
| DECEMBER 2026 |  |  |
| --- | --- | --- |
| 1 | Tuesday | Last date to withdraw from courses |
| 7 | Monday | Classes end |
| 12 | Saturday | Final examinations end / Semester ends |
| AUGUST 2026 |  |  |
| --- | --- | --- |
| 24 | Monday | Session 7A classes begin |
| OCTOBER 2026 |  |  |
| --- | --- | --- |
| 14 | Wednesday | Session 7A classes end |
"""

SUMMER_PAGE = """
| Regular Summer Session |  |
| --- | --- |
| Classes begin | June 10 |
| Classes end | July 21 |
| Final examinations begin | July 23 |
| Final examinations end | July 24 |
| Summer Session 13S |  |
| --- | --- |
| Classes begin | May 18 |
| Classes end | August 7 |
"""


def _live_chunk(title: str, url: str, text: str) -> dict:
    return {
        "title": title,
        "source_url": url,
        "category": "academic_calendar",
        "text": text,
        "metadata": {"page_fetched": True},
    }


class AcademicCalendarLiveRetrievalTests(unittest.IsolatedAsyncioTestCase):
    def test_unqualified_fall_resolves_by_campus_date(self):
        reference = resolve_academic_term(
            "When is our fall semester starting?",
            today=date(2026, 8, 11),
        )
        self.assertIsNotNone(reference)
        self.assertEqual(reference.label, "Fall 2026")
        self.assertFalse(reference.explicit_year)

    def test_candidates_are_bounded_to_requested_term_and_registrar(self):
        urls = academic_schedule_url_candidates(
            "When is our fall semester starting?",
            today=date(2026, 8, 11),
        )
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("/registrar/schedule" in url for url in urls))
        self.assertTrue(all("fall-2026" in url for url in urls))
        self.assertFalse(any("honor" in url or "alumni" in url for url in urls))

    def test_calendar_provider_scope_does_not_default_to_affiliate(self):
        query = _site_scoped_query(
            "McNeese Fall 2026 Registrar academic schedule classes begin",
            ["mcneese.edu", "mcneesealumni.com"],
        )
        self.assertTrue(query.startswith("site:mcneese.edu "))

    def test_affiliate_scope_requires_an_explicit_affiliate_question(self):
        query = _site_scoped_query(
            "McNeese alumni association events",
            ["mcneese.edu", "mcneesealumni.com"],
        )
        self.assertTrue(query.startswith("site:mcneesealumni.com "))

    def test_calendar_plan_excludes_historical_registry_noise(self):
        question = "When is our fall semester starting?"
        plan = build_retrieval_plan(classify_retrieval(question), question=question)
        self.assertEqual(plan.official_source_ids, ["SRC-012"])
        self.assertNotIn("mcneesealumni.com", plan.browse_domains)

    async def test_canonical_page_read_precedes_provider_search(self):
        question = "When is our fall semester starting?"
        plan = build_retrieval_plan(
            classify_retrieval(question),
            use_web_search=False,
            question=question,
        )

        async def fake_fetch(url: str):
            success = "/schedule/schedule/fall-2026/" in url
            return FetchedPage(
                url=url,
                title="Fall 2026" if success else "Not Found",
                content=FALL_PAGE if success else "",
                success=success,
                error=None if success else "404",
            )

        audit = {}
        with (
            patch("app.services.web_search.fetch_page_content", side_effect=fake_fetch),
            patch("app.services.search_providers.search_web", new=AsyncMock()) as search,
        ):
            evidence, error = await retrieve_academic_calendar(
                question,
                plan,
                4,
                audit=audit,
            )

        self.assertIsNone(error)
        self.assertEqual(len(evidence), 1)
        self.assertIn("Classes begin", evidence[0].text)
        self.assertFalse(audit["provider_search_executed"])
        self.assertEqual(audit["provider_queries"], [])
        search.assert_not_awaited()

    def test_direct_answer_extracts_date_from_live_evidence(self):
        answer = direct_academic_calendar_answer(
            "When is our fall semester starting?",
            [
                _live_chunk(
                    "Fall 2026",
                    "https://www.mcneese.edu/registrar/schedule/fall-2026/",
                    FALL_PAGE,
                )
            ],
        )
        self.assertIsNotNone(answer)
        self.assertIn("Monday, August 24, 2026", answer)
        self.assertNotIn("provided sources", answer)

    def test_term_course_section_query_is_not_answered_as_calendar_event(self):
        self.assertIsNone(
            direct_academic_calendar_answer(
                "Show me Calculus II sections for Fall 2026.",
                [
                    _live_chunk(
                        "Fall 2026",
                        "https://www.mcneese.edu/registrar/schedule/fall-2026/",
                        FALL_PAGE,
                    )
                ],
            )
        )

    def test_generic_fall_classes_end_ignores_short_session_rows(self):
        answer = direct_academic_calendar_answer(
            "When do Fall 2026 classes end?",
            [
                _live_chunk(
                    "Fall 2026",
                    "https://www.mcneese.edu/registrar/schedule/fall-2026/",
                    FALL_PAGE,
                )
            ],
        )
        self.assertIsNotNone(answer)
        self.assertIn("Monday, December 7, 2026", answer)
        self.assertNotIn("Session 7A", answer)

    def test_drop_without_f_uses_withdrawal_not_add_drop_deadline(self):
        answer = direct_academic_calendar_answer(
            "What is the deadline to drop a Fall 2026 class without receiving an F?",
            [
                _live_chunk(
                    "Fall 2026",
                    "https://www.mcneese.edu/registrar/schedule/fall-2026/",
                    FALL_PAGE,
                )
            ],
        )
        self.assertIsNotNone(answer)
        self.assertIn("Tuesday, December 1, 2026", answer)
        self.assertNotIn("August 25", answer)

    def test_summer_two_column_calendar_reports_classes_and_finals_end(self):
        answer = direct_academic_calendar_answer(
            "When is summer semester 2026 ending?",
            [
                _live_chunk(
                    "Summer 2026",
                    "https://www.mcneese.edu/registrar/schedule/summer-2026/",
                    SUMMER_PAGE,
                )
            ],
        )
        self.assertIsNotNone(answer)
        self.assertIn("Tuesday, July 21, 2026", answer)
        self.assertIn("Friday, July 24, 2026", answer)
        self.assertNotIn("August 7", answer)

    def test_direct_answer_refuses_unverified_or_unrelated_content(self):
        chunk = {
            "title": "Fall 2026",
            "source_url": "https://example.com/",
            "category": "academic_calendar",
            "text": FALL_PAGE,
            "metadata": {"page_fetched": False},
        }
        self.assertIsNone(
            direct_academic_calendar_answer(
                "When is our fall semester starting?",
                [chunk],
            )
        )


if __name__ == "__main__":
    unittest.main()
