"""Zero-network unit tests for the debug-trace logging flag (Sprint 4).

Verifies that ASKMCNEESE_DEBUG_TRACE controls whether the extra trace fields
(intent, persona, expanded_queries, rerank_scores, mode) are written to the
query log. No network or LLM calls are made; logging is redirected to a temp
file via a patched log path.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.services import query_logger

_DEBUG_FIELDS = ("intent", "persona", "expanded_queries", "rerank_scores", "mode")

_DEBUG_KWARGS = {
    "intent": "question",
    "persona": "transfer",
    "expanded_queries": ["how to apply", "transfer admission requirements"],
    "rerank_scores": [0.91, 0.42],
    "mode": "knowledge_base",
}


class TestDebugTraceLogging(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._log_path = Path(self._tmpdir.name) / "query_logs.jsonl"
        patcher = mock.patch.object(
            query_logger, "_get_log_path", return_value=self._log_path
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmpdir.cleanup)

    def _read_last_entry(self) -> dict:
        lines = [ln for ln in self._log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertTrue(lines, "expected at least one log line")
        return json.loads(lines[-1])

    def test_debug_fields_absent_when_flag_unset(self) -> None:
        with mock.patch.dict(os.environ, {"ASKMCNEESE_DEBUG_TRACE": "0"}, clear=False):
            query_logger.log_full_query(
                query_id="q1",
                question="How do I apply as a transfer student?",
                chunks=[],
                retrieval_ms=5,
                final_status="no_results",
                **_DEBUG_KWARGS,
            )

        entry = self._read_last_entry()
        for field in _DEBUG_FIELDS:
            self.assertNotIn(field, entry, f"{field} should be absent when debug flag is off")
        # Baseline fields are still present.
        self.assertEqual(entry["query_id"], "q1")
        self.assertEqual(entry["final_status"], "no_results")

    def test_debug_fields_present_when_flag_set(self) -> None:
        with mock.patch.dict(os.environ, {"ASKMCNEESE_DEBUG_TRACE": "1"}, clear=False):
            query_logger.log_full_query(
                query_id="q2",
                question="How do I apply as a transfer student?",
                chunks=[],
                retrieval_ms=5,
                final_status="no_results",
                **_DEBUG_KWARGS,
            )

        entry = self._read_last_entry()
        for field in _DEBUG_FIELDS:
            self.assertIn(field, entry, f"{field} should be present when debug flag is on")
        self.assertEqual(entry["intent"], _DEBUG_KWARGS["intent"])
        self.assertEqual(entry["persona"], _DEBUG_KWARGS["persona"])
        self.assertEqual(entry["expanded_queries"], _DEBUG_KWARGS["expanded_queries"])
        self.assertEqual(entry["rerank_scores"], _DEBUG_KWARGS["rerank_scores"])
        self.assertEqual(entry["mode"], _DEBUG_KWARGS["mode"])


if __name__ == "__main__":
    unittest.main()
