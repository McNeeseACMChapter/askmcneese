from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.routers import class_planner as class_planner_router
from app.services.class_planner.models import TermOption
from app.services.class_planner.pipeline import (
    compare_datasets,
    enforce_anomaly_rules,
    McNeeseClassSearchAdapter,
    parse_sections,
    parse_subjects,
    SourceContractError,
    ValidationFailure,
    validate_sections,
)
from app.services.class_planner.store import ClassPlannerStore


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "mcneese_class_search"
    / "fall_2026_representative.html"
)


class ClassPlannerParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = parse_sections(FIXTURE.read_text(encoding="utf-8"), "202660")

    def test_parses_real_fixed_multiple_and_online_shapes(self) -> None:
        self.assertEqual(len(self.records), 3)
        csci = self.records[0]
        self.assertEqual((csci.subject, csci.course_number, csci.crn), ("CSCI", "180", "61166"))
        self.assertEqual(len(csci.meetings), 2)
        self.assertEqual(csci.meetings[0].days, ("T", "R"))
        self.assertEqual((csci.meetings[0].start_time, csci.meetings[0].end_time), ("08:00", "09:20"))
        self.assertEqual(csci.meetings[1].days, ("M",))
        self.assertEqual(csci.instructors, ("Lavergne, Jennifer",))

        night = self.records[1]
        self.assertEqual((night.meetings[0].start_time, night.meetings[0].end_time), ("17:30", "19:30"))
        self.assertEqual(night.available, 24)

        online = self.records[2]
        self.assertTrue(online.meetings[0].is_online)
        self.assertTrue(online.meetings[0].is_tba)
        self.assertIsNone(online.meetings[0].start_time)
        self.assertEqual(online.status, "open")

    def test_validator_distinguishes_invalid_from_optional_missing(self) -> None:
        optional_missing = replace(self.records[0], instructors=())
        invalid = replace(self.records[1], crn="bad")
        over_enrolled = replace(self.records[1], capacity=23, enrolled=24, available=None, crn="61234").with_hash()
        report = validate_sections([optional_missing, invalid, over_enrolled])
        self.assertEqual([item.id for item in report.valid], [optional_missing.id, over_enrolled.id])
        self.assertEqual(report.rejected[0]["reason"], "CRN does not match verified five-digit source format")

    def test_diff_detects_add_change_and_remove(self) -> None:
        previous = {
            self.records[0].id: self.records[0].normalized_hash,
            "202660:99999": "removed",
        }
        changed = replace(self.records[0], title="CHANGED").with_hash()
        diff = compare_datasets(previous, [changed, self.records[1]])
        self.assertEqual((diff.added, diff.changed, diff.removed), (1, 1, 1))

    def test_detects_error_pages_and_suspiciously_small_imports(self) -> None:
        with self.assertRaises(SourceContractError):
            parse_sections("<html><body>Login unavailable</body></html>", "202660")
        report = validate_sections(self.records)
        diff = compare_datasets({}, report.valid)
        with self.assertRaises(ValidationFailure):
            enforce_anomaly_rules(report.valid, report, {}, diff)

    def test_availability_change_changes_normalized_hash(self) -> None:
        updated = replace(self.records[1], available=23).with_hash()
        diff = compare_datasets(
            {self.records[1].id: self.records[1].normalized_hash},
            [updated],
        )
        self.assertEqual(diff.changed, 1)

    def test_parse_subjects_reads_verified_subject_select(self) -> None:
        html = """
        <form method="post" action="index.php">
          <select name="subject">
            <option value=""></option>
            <option value="CSCI">CSCI</option>
            <option value="MATH">MATH</option>
            <option value="ENGL">ENGL</option>
          </select>
        </form>
        """
        self.assertEqual(parse_subjects(html), ["CSCI", "MATH", "ENGL"])

    def test_parse_sections_can_allow_empty_subject_results(self) -> None:
        self.assertEqual(
            parse_sections("<html><body><p>No classes found</p></body></html>", "202660", allow_empty=True),
            [],
        )

    def test_adapter_uses_verified_form_contract_and_bounds_http_failures(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(500, headers={"Content-Type": "text/html"}, text="error")

        client = httpx.Client(
            base_url="https://schedule.mcneese.edu/",
            transport=httpx.MockTransport(handler),
        )
        adapter = McNeeseClassSearchAdapter(client=client, max_attempts=2)
        with patch("app.services.class_planner.pipeline.time.sleep"):
            with self.assertRaises(SourceContractError):
                adapter.fetch_sections_html("202660", subject="CSCI")
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].method, "POST")
        body = requests[0].content.decode()
        self.assertIn("term_code=202660", body)
        self.assertIn("subject=CSCI", body)
        self.assertIn("fps=0", body)
        client.close()


class ClassPlannerStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = ClassPlannerStore(Path(self.temp.name) / "planner.sqlite3")
        self.records = parse_sections(FIXTURE.read_text(encoding="utf-8"), "202660")
        self.term = TermOption("202660", "Fall 2026")
        self.store.publish(
            term=self.term,
            records=self.records,
            fetched_at="2026-08-08T14:00:00+00:00",
            source_url="https://schedule.mcneese.edu/",
            parser_version="test",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_queries_normalized_courses_and_sections(self) -> None:
        courses = self.store.search_courses("202660", query="Lavergne")
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]["id"], "202660:CSCI:180")
        self.assertEqual(len(courses[0]["sections"][0]["meetings"]), 2)
        online = self.store.search_courses("202660", online_only=True)
        self.assertEqual(online[0]["subject"], "ENGL")
        section = self.store.get_section("202660:61154")
        self.assertEqual(section["seatsRemaining"], 24)

    def test_failed_publish_does_not_replace_last_known_good(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.publish(
                term=self.term,
                records=[self.records[0], self.records[0]],
                fetched_at="2026-08-08T15:00:00+00:00",
                source_url="https://schedule.mcneese.edu/",
                parser_version="test",
            )
        self.assertEqual(len(self.store.search_courses("202660")), 3)
        self.assertEqual(
            self.store.freshness("202660")["fetchedAt"],
            "2026-08-08T14:00:00+00:00",
        )

    def test_term_lock_prevents_overlap(self) -> None:
        first = self.store.acquire_sync_lock("202660")
        self.assertIsNotNone(first)
        self.assertIsNone(self.store.acquire_sync_lock("202660"))
        # A stale/forced release from another abandoned job must not drop an owned lock.
        self.store.release_sync_lock("202660", "not-the-owner")
        self.assertIsNone(self.store.acquire_sync_lock("202660"))
        self.store.release_sync_lock("202660", first)
        self.assertIsNotNone(self.store.acquire_sync_lock("202660"))


class ClassPlannerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        store = ClassPlannerStore(Path(self.temp.name) / "planner.sqlite3")
        records = parse_sections(FIXTURE.read_text(encoding="utf-8"), "202660")
        store.publish(
            term=TermOption("202660", "Fall 2026"),
            records=records,
            fetched_at="2026-08-08T14:00:00+00:00",
            source_url="https://schedule.mcneese.edu/",
            parser_version="test",
        )
        class_planner_router._store.cache_clear()
        self.store_patcher = patch.object(class_planner_router, "_store", return_value=store)
        self.store_patcher.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.store_patcher.stop()
        self.temp.cleanup()

    def test_terms_search_and_section_details(self) -> None:
        terms = self.client.get("/class-planner/terms")
        self.assertEqual(terms.status_code, 200)
        self.assertEqual(terms.json()["data"][0]["id"], "202660")
        courses = self.client.get(
            "/class-planner/courses",
            params={"term": "202660", "q": "CSCI 308", "open": "true"},
        )
        self.assertEqual(courses.status_code, 200)
        self.assertEqual(courses.json()["data"][0]["sections"][0]["crn"], "61154")
        section = self.client.get("/class-planner/sections/202660:61154")
        self.assertEqual(section.status_code, 200)
        self.assertEqual(section.json()["source"]["name"], "McNeese Class Search")


if __name__ == "__main__":
    unittest.main()
