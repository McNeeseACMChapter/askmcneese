from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.routers import class_planner as class_planner_router
from app.services.class_planner.availability import refresh_course_availability
from app.services.class_planner.db import database_url_from_environment, sync_subjects
from app.services.class_planner.models import SubjectOption, TermOption
from app.services.class_planner.pipeline import (
    compare_datasets,
    enforce_anomaly_rules,
    McNeeseClassSearchAdapter,
    parse_sections,
    parse_subjects,
    SourceContractError,
    ValidationFailure,
    sync_mcneese_term,
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
        self.dataset_id = self.store.publish(
            term=self.term,
            records=self.records,
            fetched_at="2026-08-08T14:00:00+00:00",
            source_url="https://schedule.mcneese.edu/",
            parser_version="test",
            subject_options=(
                SubjectOption("CSCI", "Computer Science"),
                SubjectOption("ENGL", "English"),
            ),
        )

    def tearDown(self) -> None:
        self.store.engine.dispose()
        self.temp.cleanup()

    def test_queries_normalized_courses_and_sections(self) -> None:
        courses = self.store.search_courses("202660", query="Lavergne")
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]["id"], "202660:CSCI:180")
        page = self.store.get_course_sections("202660", "202660:CSCI:180")
        self.assertEqual(len(page["sections"][0]["meetings"]), 2)
        online = self.store.search_courses("202660", online_only=True)
        self.assertEqual(online[0]["subject"], "ENGL")
        section = self.store.get_section("202660:61154")
        self.assertEqual(section["seatsRemaining"], 24)

    def test_failed_publish_does_not_replace_last_known_good(self) -> None:
        with self.assertRaises(IntegrityError):
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

    def test_source_alias_search_and_registration_notes_are_separate(self) -> None:
        self.assertEqual(self.store.search_courses("202660", query="cs 180")[0]["id"], "202660:CSCI:180")
        online = self.store.get_section("202660:61429")
        self.assertEqual(online["instructor"], "Mahone, Taylor M")
        self.assertIn("ONLINE MAJORS ONLY NOT SELF PACED", online["registrationNotes"])
        self.assertEqual(self.store.search_courses("202660", query="ONLINE MAJORS ONLY"), [])

    def test_section_expansion_is_bounded_and_pageable(self) -> None:
        base = self.records[0]
        records = [
            replace(
                base,
                id=f"202660:{62000 + index}",
                crn=str(62000 + index),
                section_code=f"A{index}",
            ).with_hash()
            for index in range(8)
        ]
        self.store.publish(
            term=self.term, records=records, fetched_at="2026-08-08T14:30:00+00:00",
            source_url="https://schedule.mcneese.edu/", parser_version="test",
        )
        first = self.store.get_course_sections("202660", base.course_id, limit=6)
        second = self.store.get_course_sections("202660", base.course_id, limit=6, offset=6)
        self.assertEqual((len(first["sections"]), first["total"], first["hasMore"]), (6, 8, True))
        self.assertEqual((len(second["sections"]), second["offset"], second["hasMore"]), (2, 6, False))

    def test_section_hydration_has_constant_query_count(self) -> None:
        statements: list[str] = []
        listener = lambda *args: statements.append(str(args[2]))
        event.listen(self.store.engine, "before_cursor_execute", listener)
        try:
            self.store.get_course_sections("202660", "202660:CSCI:180")
        finally:
            event.remove(self.store.engine, "before_cursor_execute", listener)
        self.assertLessEqual(len(statements), 5)

    def test_subject_telemetry_and_atomic_rollback(self) -> None:
        sync_id = self.store.start_sync("202660", "https://schedule.mcneese.edu/", "test")
        self.store.record_subject_sync(
            sync_id, "CSCI", started_at="2026-08-08T14:01:00+00:00",
            status="success", section_count=2, duration_ms=25, content_hash="abc",
        )
        with self.store.engine.connect() as db:
            row = db.execute(select(sync_subjects).where(sync_subjects.c.sync_id == sync_id)).mappings().one()
        self.assertEqual((row["subject"], row["section_count"], row["status"]), ("CSCI", 2, "success"))

        changed = [replace(item, title="Changed title").with_hash() for item in self.records]
        newer_id = self.store.publish(
            term=self.term, records=changed, fetched_at="2026-08-08T15:00:00+00:00",
            source_url="https://schedule.mcneese.edu/", parser_version="test",
        )
        self.assertNotEqual(newer_id, self.dataset_id)
        self.assertEqual(self.store.search_courses("202660", query="Changed")[0]["title"], "Changed title")
        self.store.rollback("202660", self.dataset_id)
        self.assertEqual(self.store.search_courses("202660", query="Changed"), [])
        self.assertEqual(self.store.freshness("202660")["fetchedAt"], "2026-08-08T14:00:00+00:00")

    def test_unchanged_sync_advances_clocks_without_dataset_churn(self) -> None:
        fixture_html = FIXTURE.read_text(encoding="utf-8")

        class FixtureAdapter:
            def fetch_terms(self):
                return [TermOption("202660", "Fall 2026")]

            def fetch_term_search_form(self, term_id):
                return '<form action="index.php"><select name="subject"><option value="CSCI">Computer Science</option></select></form>'

            def fetch_sections_html(self, *args, **kwargs):
                return fixture_html

        with patch.dict("os.environ", {
            "CLASS_SYNC_MIN_SECTIONS": "1",
            "CLASS_SOURCE_SUBJECT_DELAY_SECONDS": "0",
            "CLASS_SYNC_MAX_CONCURRENCY": "1",
        }):
            result = sync_mcneese_term("202660", store=self.store, adapter=FixtureAdapter())
        self.assertFalse(result["published"])
        self.assertEqual(result["datasetId"], self.dataset_id)
        self.assertEqual(self.store.active_dataset_id("202660"), self.dataset_id)
        self.assertEqual(self.store.freshness("202660")["metadataVerifiedAt"], result["fetchedAt"])

    def test_failed_targeted_refresh_preserves_last_known_good(self) -> None:
        before = self.store.get_section("202660:61154")

        class BrokenAdapter:
            def fetch_sections_html(self, *args, **kwargs):
                raise SourceContractError("upstream unavailable")

        result = refresh_course_availability(
            "202660", "202660:CSCI:308", store=self.store, adapter=BrokenAdapter()
        )
        after = self.store.get_section("202660:61154")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(after["seatsRemaining"], before["seatsRemaining"])

    def test_live_mode_requires_postgresql(self) -> None:
        with patch.dict("os.environ", {"CLASS_DATA_MODE": "live"}, clear=True):
            with self.assertRaises(RuntimeError):
                database_url_from_environment()
        with patch.dict("os.environ", {
            "CLASS_DATA_MODE": "live",
            "DATABASE_URL": "sqlite:///unsafe.sqlite3",
        }, clear=True):
            with self.assertRaises(RuntimeError):
                database_url_from_environment()
        with patch.dict("os.environ", {
            "CLASS_DATA_MODE": "staging",
            "CLASS_PLANNER_DB_PATH": "relative-planner.sqlite3",
        }, clear=True):
            self.assertTrue(database_url_from_environment().endswith("/backend/relative-planner.sqlite3"))


class ClassPlannerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        store = ClassPlannerStore(Path(self.temp.name) / "planner.sqlite3")
        self.store = store
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
        self.store.engine.dispose()
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
        self.assertEqual(courses.json()["data"][0]["sectionCount"], 1)
        sections_response = self.client.get("/class-planner/courses/202660:CSCI:308/sections", params={"term": "202660"})
        self.assertEqual(sections_response.status_code, 200)
        self.assertEqual(sections_response.json()["data"]["sections"][0]["crn"], "61154")
        section = self.client.get("/class-planner/sections/202660:61154")
        self.assertEqual(section.status_code, 200)
        self.assertEqual(section.json()["source"]["name"], "McNeese Class Search")

    def test_internal_sync_requires_admin_token(self) -> None:
        with patch.dict("os.environ", {"CLASS_SYNC_ADMIN_TOKEN": "expected"}):
            missing = self.client.post("/class-planner/internal/sync", params={"term": "202660"})
            wrong = self.client.post(
                "/class-planner/internal/sync", params={"term": "202660"},
                headers={"X-Class-Sync-Token": "wrong"},
            )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)


if __name__ == "__main__":
    unittest.main()
