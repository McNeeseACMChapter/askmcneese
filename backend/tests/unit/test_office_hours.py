from datetime import datetime
import unittest
from zoneinfo import ZoneInfo

from app.services.office_hours import calculate_office_status, parse_weekly_hours
from app.services.office_hours_answer import direct_office_hours_answer
from app.services.verified_service_answer import direct_verified_service_answer


OFFICE_PAGE = """
Office of the Registrar
4435 Ryan Street
337-475-5065
registrar@mcneese.edu
Hours of Operation
Monday - Thursday: 7:30 a.m. - 5 p.m.
Friday: 7:30 a.m. - 11:30 a.m.
"""


class OfficeHoursTests(unittest.TestCase):
    def test_regular_hours_calculate_live_closing_countdown(self) -> None:
        windows = parse_weekly_hours(OFFICE_PAGE)
        status = calculate_office_status(
            windows,
            now=datetime(2026, 8, 14, 11, 24, tzinfo=ZoneInfo("America/Chicago")),
        )
        self.assertTrue(status.is_open)
        self.assertEqual(status.minutes_until_transition, 6)
        self.assertEqual(status.next_transition.hour, 11)
        self.assertEqual(status.next_transition.minute, 30)

    def test_closed_office_reports_next_regular_opening(self) -> None:
        windows = parse_weekly_hours(OFFICE_PAGE)
        status = calculate_office_status(
            windows,
            now=datetime(2026, 8, 14, 12, 0, tzinfo=ZoneInfo("America/Chicago")),
        )
        self.assertFalse(status.is_open)
        self.assertEqual(status.next_transition.strftime("%A %H:%M"), "Monday 07:30")

    def test_direct_answer_combines_location_contact_and_status(self) -> None:
        answer = direct_office_hours_answer(
            "Where is the Registrar's Office and what time does it close today?",
            [{
                "title": "Office of the Registrar",
                "source_url": "https://www.mcneese.edu/registrar/",
                "text": OFFICE_PAGE,
                "metadata": {"page_fetched": True},
            }],
            {"request_context": {"current_datetime": "2026-08-14T11:24:00-05:00"}},
        )
        self.assertIsNotNone(answer)
        self.assertIn("4435 Ryan Street", answer)
        self.assertIn("closes at 11:30 a.m. (in 6 minutes)", answer)
        self.assertIn("America/Chicago", answer)

    def test_direct_answer_accepts_verified_office_snapshot(self) -> None:
        answer = direct_office_hours_answer(
            "Where is the Registrar and when does it close today?",
            [{
                "title": "Office of the Registrar",
                "source_url": "https://www.mcneese.edu/registrar/",
                "text": OFFICE_PAGE,
                "metadata": {"curated_snapshot": True, "last_verified": "2026-08-14"},
            }],
            {"request_context": {"current_datetime": "2026-08-14T11:24:00-05:00"}},
        )
        self.assertIsNotNone(answer)
        self.assertIn("Open now", answer)
        self.assertIn("closes at 11:30 a.m. (in 6 minutes)", answer)

    def test_verified_service_direct_answer_uses_only_snapshot(self) -> None:
        answer = direct_verified_service_answer(
            "Where can I get medical help?",
            [{
                "title": "Student Health Services",
                "source_url": "https://www.mcneese.edu/health-services/",
                "text": "Student Health Services provides acute medical care at 4100 Ryan St. Call 337-475-5748.",
                "score": 0.9,
                "metadata": {"curated_snapshot": True},
            }],
        )
        self.assertIsNotNone(answer)
        self.assertIn("4100 Ryan St.", answer)
        self.assertIn("https://www.mcneese.edu/health-services/", answer)


if __name__ == "__main__":
    unittest.main()
