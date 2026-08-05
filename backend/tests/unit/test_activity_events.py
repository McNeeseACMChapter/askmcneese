"""Unit tests for sanitized Ask stream activity payloads."""

import unittest
from unittest import mock

from app.services.activity_events import (
    REQUEST_ACCEPTED,
    activity_payload,
    safe_metadata,
    source_activity,
    source_activities_from_citations,
    source_preview_from_citations,
)


class TestActivityEvents(unittest.TestCase):
    def test_payload_shape_uses_safe_default_message(self) -> None:
        with mock.patch(
            "app.services.activity_events.time.perf_counter",
            return_value=10.25,
        ):
            payload = activity_payload(
                "request-123",
                REQUEST_ACCEPTED,
                10.0,
                metadata={"mode": "knowledge_base", "ignored": "secret"},
            )

        self.assertEqual(payload["request_id"], "request-123")
        self.assertEqual(payload["event"], "request.accepted")
        self.assertEqual(payload["message"], "Starting your request")
        self.assertEqual(payload["elapsed_ms"], 250)
        self.assertEqual(payload["phase"], "understand")
        self.assertEqual(payload["kind"], "milestone")
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["metadata"]["mode"], "knowledge_base")
        self.assertNotIn("ignored", payload["metadata"])
        self.assertIn("event_id", payload["metadata"])

    def test_payload_includes_optional_run_id(self) -> None:
        with mock.patch(
            "app.services.activity_events.time.perf_counter",
            return_value=10.25,
        ):
            payload = activity_payload(
                "request-123",
                REQUEST_ACCEPTED,
                10.0,
                run_id="run-abc",
            )

        self.assertEqual(payload["run_id"], "run-abc")
        self.assertEqual(payload["request_id"], "request-123")
        metadata = safe_metadata(
            {
                "mode": r"C:\Users\student\secret.txt",
                "status": "/var/private/data",
                "duration_ms": 42,
                "sources_found": 3,
                "prompt": "not allowlisted",
            }
        )

        self.assertEqual(metadata, {"duration_ms": 42, "sources_found": 3})

    def test_source_preview_joins_titles(self) -> None:
        preview = source_preview_from_citations(
            [
                {"title": "Admissions", "url": "https://www.mcneese.edu/admissions"},
                {"title": "Aid", "url": "https://www.mcneese.edu/finaid"},
                {"title": "Admissions", "url": "https://www.mcneese.edu/admissions/2"},
            ]
        )
        self.assertEqual(preview, "Admissions · Aid")
        self.assertIn(
            "source_preview",
            safe_metadata({"source_preview": preview, "prompt": "nope"}),
        )

    def test_source_activity_emits_one_title(self) -> None:
        with mock.patch(
            "app.services.activity_events.time.perf_counter",
            return_value=10.5,
        ):
            payload = source_activity(
                "request-123",
                10.0,
                source_title="Academic Calendar 2026–27",
                source_host="mcneese.edu",
                source_url="https://www.mcneese.edu/academics/calendar/",
                source_type="official",
                operation_id="official-web",
                sources_found=8,
                sources_read=1,
                run_id="run-abc",
            )
        self.assertEqual(payload["kind"], "evidence")
        self.assertEqual(payload["phase"], "search")
        self.assertEqual(payload["metadata"]["source_title"], "Academic Calendar 2026–27")
        self.assertEqual(payload["metadata"]["operation_id"], "official-web")
        self.assertEqual(payload["run_id"], "run-abc")

    def test_source_activities_from_citations(self) -> None:
        events = source_activities_from_citations(
            "request-123",
            10.0,
            [
                {"title": "Admissions", "url": "https://www.mcneese.edu/admissions"},
                {"title": "Aid", "url": "https://www.mcneese.edu/finaid"},
            ],
            operation_id="kb",
            sources_found=2,
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["metadata"]["source_title"], "Admissions")
        self.assertEqual(events[1]["metadata"]["source_title"], "Aid")

    def test_rejects_private_source_url(self) -> None:
        with mock.patch(
            "app.services.activity_events.time.perf_counter",
            return_value=10.5,
        ):
            payload = source_activity(
                "request-123",
                10.0,
                source_title="Internal",
                source_url="http://localhost:8000/secret",
            )
        self.assertNotIn("source_url", payload["metadata"])


if __name__ == "__main__":
    unittest.main()
