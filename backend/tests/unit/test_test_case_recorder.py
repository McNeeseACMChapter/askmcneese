"""Unit tests for the test-case trail recorder."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.activity_events import activity_payload, REQUEST_ACCEPTED
from app.services import test_case_recorder as rec


class TestCaseRecorder(unittest.TestCase):
    def test_records_activity_and_match_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            trail = Path(tmp) / "trail.txt"
            with patch.dict(
                os.environ,
                {
                    "TEST_CASE_RECORDING_ENABLED": "1",
                    "TEST_CASE_TRAIL_PATH": str(trail),
                },
                clear=False,
            ):
                # Reset counter file side effects by pointing index beside trail
                run = rec.begin_run(
                    query_id="q-test-1",
                    question="What is going on with ACM organization events?",
                    use_web_search=True,
                    stream=True,
                )
                self.assertIsNotNone(run)
                activity_payload("q-test-1", REQUEST_ACCEPTED, 0.0)
                activity_payload(
                    "q-test-1",
                    "retrieval.started",
                    0.0,
                    message="Searching public profiles and related web sources…",
                    metadata={"mode": "rccs_hybrid"},
                )
                path = rec.finalize_run(
                    answer="No events found.",
                    answer_type="factual",
                    model="test",
                    num_results=1,
                    retrieval_mode="rccs_hybrid",
                    retrieval_channels=["agentic_web", "companion"],
                    used_companion_sources=["SRC-C-INSTAGRAM-001"],
                    sources=[
                        {
                            "title": "ACM Instagram",
                            "url": "https://www.instagram.com/mcneeseacm/",
                            "retrieval_channel": "companion",
                            "source_tier": "C",
                            "trust_level": "social",
                        }
                    ],
                    citations=[
                        {
                            "title": "ACM Instagram",
                            "url": "https://www.instagram.com/mcneeseacm/",
                            "retrieval_channel": "companion",
                            "source_tier": "C",
                            "trust_level": "social",
                        }
                    ],
                    total_ms=12,
                )
                self.assertIsNotNone(path)
                body = trail.read_text(encoding="utf-8")
                self.assertIn("TEST CASE #", body)
                self.assertIn("request.accepted", body)
                self.assertIn("TRAIL vs DATA MATCH", body)
                self.assertIn("instagram.com", body)


if __name__ == "__main__":
    unittest.main()
