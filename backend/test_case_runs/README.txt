AskMcNeese test-case trail logs
================================

This directory is reserved for local, append-only Ask pipeline trail logs. Runtime logs are intentionally kept outside app/, knowledge/, and committed source data.

Primary local file:
  test_case_trail.txt

Recording is controlled by:
  TEST_CASE_RECORDING_ENABLED=1|0
  TEST_CASE_TRAIL_PATH=<optional path override>

Each recorded run can include:
  - question and request flags
  - intent, source plan, companion plan, and browse policy
  - activity events shown to the frontend
  - backend channels, opened pages, sources, and citations
  - activity-versus-backend consistency verdict
  - final answer text and timing metadata

Safety and release rules:
  - Do not commit raw trail logs unless they have been reviewed and sanitized.
  - Remove cookies, secrets, personal data, and provider payloads before sharing.
  - Treat logs as diagnostic evidence, not as the source of product truth.
  - Use backend/tests/eval/capability_questions.json for committed representative capability coverage.
  - Beta behavior is subject to change when production bugs or evidence gaps are found.
