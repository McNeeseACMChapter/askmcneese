from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.rccs.hybrid import _question_matched_action_links
from app.services.rccs.models import RetrievedEvidence, utcnow
from app.services.web_search import (
    _is_cloudflare_blocked,
    _parse_fetched_html,
    fetch_page_content,
    select_relevant_page_sections,
)


def _evidence(*, url: str, text: str = "", **metadata) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id="ev-test",
        title="Official page",
        url=url,
        text=text,
        source_id="TEST",
        source_name="Official page",
        source_tier="A",
        trust_level="official",
        category="official_live",
        retrieval_channel="official_live",
        published_at=None,
        fetched_at=utcnow(),
        relevance_score=0.9,
        metadata=metadata,
    )


class CloudflareDetectorTests(unittest.TestCase):
    def test_noscript_enable_javascript_is_not_a_challenge(self) -> None:
        html = """
        <html><head><title>International Admissions</title></head>
        <body>
          <noscript>Please enable JavaScript to view this site.</noscript>
          <main><h1>How to apply</h1><p>Submit the application and transcripts.</p></main>
        </body></html>
        """
        self.assertFalse(_is_cloudflare_blocked(html))

    def test_real_cloudflare_challenge_is_blocked(self) -> None:
        html = "<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>"
        self.assertTrue(_is_cloudflare_blocked(html))


class SectionExtractionTests(unittest.TestCase):
    def test_keeps_question_matched_section_not_the_page_head(self) -> None:
        content = (
            "Campus news and welcome banner for visiting families.\n\n"
            "Dining hours this week are posted on a separate page.\n\n"
            "International application steps\n"
            "1. Complete the online application.\n"
            "2. Submit transcripts and English scores.\n"
            "3. Pay the application fee.\n\n"
            "Football tickets go on sale Friday."
        )
        excerpt = select_relevant_page_sections(
            content,
            "exact steps to apply as an international student",
            limit=220,
        )
        self.assertIn("International application steps", excerpt)
        self.assertIn("Complete the online application", excerpt)
        self.assertNotIn("Football tickets", excerpt)

    def test_start_date_beats_office_hours_even_when_page_fits_the_limit(self) -> None:
        content = (
            "337-475-5065\nChozen Hall\nMonday-Thursday: 7:30 a.m. to 5:00 p.m.\n\n"
            "Fall Regular Semester\n"
            "3 Monday Personal Touch Accounts (PTA) open\n"
            "6 Thursday Non-traditional/Transfer orientation\n\n"
            "24 Monday Classes begin for the Fall 2026 regular semester.\n"
        )
        excerpt = select_relevant_page_sections(
            content,
            "When does fall semester 2026 start?",
            limit=4000,
        )
        self.assertIn("Classes begin", excerpt)
        self.assertNotIn("337-475-5065", excerpt)

    def test_start_date_is_selected_from_a_calendar_table(self) -> None:
        table = (
            "337-475-5065\nChozen Hall\n\n"
            "| AUGUST 2026 | | |\n"
            "| 3 | Monday | Personal Touch Accounts (PTA) open |\n"
            "| 6 | Thursday | Non-traditional/Transfer Student Orientation |\n"
            "| 10 | Monday | Last date to apply for admission for regular session |\n"
            "| 17 | Monday | Faculty report to work |\n"
            "| 18 | Tuesday | General Faculty/Staff Meeting |\n"
            "| 24 | Monday | Classes begin for the Fall 2026 regular semester |\n"
            "| 25 | Tuesday | Late registration |\n"
        )
        excerpt = select_relevant_page_sections(
            table,
            "When does fall semester 2026 start?",
            limit=400,
        )
        self.assertIn("Classes begin", excerpt)
        self.assertNotIn("337-475-5065", excerpt)

    def test_later_matching_section_beats_page_head_within_limit(self) -> None:
        freshman = (
            "Application Steps - It's as easy as 1-2-3!\n"
            "Start your application by choosing a student type.\n"
            + ("Submit ACT scores and apply for freshman scholarships. " * 40)
        )
        international = (
            "I'm An International Student\n"
            "Pay a nonrefundable application fee of $30. "
            "Submit official transcripts and a signed affidavit before an I-20 is issued."
        )
        excerpt = select_relevant_page_sections(
            freshman + "\n\n" + international + "\n\nCampus news for visiting families.",
            "exact steps to apply as an international student",
            limit=500,
        )
        self.assertIn("I'm An International Student", excerpt)
        self.assertIn("application fee of $30", excerpt)
        self.assertNotIn("Campus news", excerpt)

    def test_campus_spelling_correction_still_selects_international_section(self) -> None:
        freshman = (
            "Application Steps - It's as easy as 1-2-3!\n"
            "Start your application by choosing a student type.\n"
            + ("Submit ACT scores and apply for freshman scholarships. " * 40)
        )
        international = (
            "I'm An International Student\n"
            "Pay a nonrefundable application fee of $30. "
            "Submit official transcripts and a signed affidavit before an I-20 is issued."
        )
        excerpt = select_relevant_page_sections(
            freshman + "\n\n" + international,
            "i am an interantional student tell me the exact steps to apply",
            limit=500,
        )
        self.assertIn("I'm An International Student", excerpt)
        self.assertIn("application fee of $30", excerpt)

    def test_audience_section_beats_register_for_classes_noise(self) -> None:
        freshman_register = (
            "We're thrilled you've decided to become a Cowboy.\n"
            "Through Banner, you will be able to register for classes and pay tuition."
        )
        international = (
            "I'm An International Student\n"
            "Pay a nonrefundable application fee of $30. "
            "Submit official transcripts and a signed affidavit before an I-20 is issued."
        )
        excerpt = select_relevant_page_sections(
            freshman_register + "\n\n" + international,
            "i am an interantional student tell me the exact steps to apply so I can register the class",
            limit=220,
        )
        self.assertIn("I'm An International Student", excerpt)
        self.assertIn("application fee of $30", excerpt)
        self.assertNotIn("We're thrilled", excerpt)

    def test_main_content_survives_header_nav_noise(self) -> None:
        html = """
        <html><head><title>Admissions | McNeese</title></head>
        <body>
          <header><nav><a href="/news/">News</a></nav></header>
          <main>
            <h1>How to apply</h1>
            <p>International students should submit an application, transcripts, and English test scores.</p>
            <a href="https://www.mcneese.edu/admissions/apply/">Application portal</a>
          </main>
          <footer>Privacy policy</footer>
        </body></html>
        """
        page = _parse_fetched_html(
            "https://www.mcneese.edu/admissions/",
            html,
            "How do I apply as an international student?",
        )
        self.assertTrue(page.success)
        self.assertIn("International students should submit", page.content)
        self.assertEqual(page.links[0]["url"], "https://www.mcneese.edu/admissions/apply/")

    def test_ignores_breakdance_token_main_and_reads_accordion_body(self) -> None:
        html = """
        <html><head><title>Apply - McNeese State University</title></head>
        <body>
          <div id="headspin-tokenWP" class="tokenWP-modal">
            <main id="tokenwp-main">
              <p>Headings color Text color Site main background Brand color Brand hover color Links color</p>
            </main>
          </div>
          <header>
            <nav>
              <a href="https://www.mcneese.edu/admissions/">Overview</a>
              <a href="https://www.mcneese.edu/admissions/#freshman">First Time Freshman</a>
            </nav>
          </header>
          <section>
            <h2>Application Steps - It's as easy as 1-2-3!</h2>
            <h3>I'm A Beginning Freshman</h3>
            <p>Submit your official ACT or SAT scores to McNeese.</p>
            <h3>I'm An International Student</h3>
            <p>Pay a nonrefundable application fee of $30. Submit official transcripts, a signed affidavit, and exam scores before an I-20 can be issued.</p>
            <a href="https://www.mcneese.edu/admissions/requirements/">admission requirements</a>
          </section>
        </body></html>
        """
        page = _parse_fetched_html(
            "https://www.mcneese.edu/admissions/apply/",
            html,
            "exact steps to apply as an international student",
        )
        self.assertTrue(page.success)
        self.assertIn("application fee of $30", page.content)
        self.assertIn("signed affidavit", page.content)
        self.assertNotIn("Headings color", page.content)
        self.assertNotIn("Brand hover color", page.content)
        self.assertEqual(
            page.links[0]["url"],
            "https://www.mcneese.edu/admissions/requirements/",
        )


class SecondHopLinkTests(unittest.TestCase):
    def test_action_links_in_metadata_are_followed(self) -> None:
        item = _evidence(
            url="https://www.mcneese.edu/admissions/",
            text="Admissions overview.",
            page_read=True,
            action_links=[
                {
                    "label": "International application steps",
                    "url": "https://www.mcneese.edu/admissions/international/",
                }
            ],
        )
        urls = _question_matched_action_links(
            "exact steps to apply as an international student",
            [item],
            {"https://www.mcneese.edu/admissions"},
        )
        self.assertEqual(
            urls,
            ["https://www.mcneese.edu/admissions/international/"],
        )


class FetchBeforeSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetcher_uses_question_when_reading_html(self) -> None:
        html = """
        <html><head><title>Admissions</title></head>
        <body><main>
          <p>Welcome to McNeese news and campus highlights for families visiting Lake Charles this weekend.</p>
          <h2>International application steps</h2>
          <ol><li>Complete the application</li><li>Submit transcripts</li></ol>
        </main></body></html>
        """
        with patch(
            "app.services.web_search._fetch_http_html",
            AsyncMock(return_value=("https://www.mcneese.edu/admissions/", html, "")),
        ):
            page = await fetch_page_content(
                "https://www.mcneese.edu/admissions/",
                question="What are the steps to apply as an international student?",
            )
        self.assertTrue(page.success)
        self.assertIn("International application steps", page.content)
        self.assertIn("Complete the application", page.content)


if __name__ == "__main__":
    unittest.main()
