"""Unit tests for sanitized Ask stream activity payloads."""

import unittest
from unittest import mock

from app.services.activity_events import (
    REQUEST_ACCEPTED,
    activity_payload,
    safe_metadata,
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

        self.assertEqual(
            payload,
            {
                "request_id": "request-123",
                "event": "request.accepted",
                "message": "Got your question — starting now",
                "elapsed_ms": 250,
                "metadata": {"mode": "knowledge_base"},
            },
        )

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


if __name__ == "__main__":
    unittest.main()
