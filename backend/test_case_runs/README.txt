AskMcNeese test-case trail logs live in this folder (outside app/, logs/, and knowledge/).

Primary file:
  test_case_trail.txt   — append-only record of every /ask run while
                          TEST_CASE_RECORDING_ENABLED=1

Each block includes:
  - question + flags
  - classification / plan (intent, companions, browse_social)
  - ACTIVITY TRAIL (same SSE activity events the UI sees)
  - BACKEND DATA (channels, companions, sources, citations)
  - TRAIL vs DATA MATCH verdict
  - answer text

Toggle:
  backend/.env → TEST_CASE_RECORDING_ENABLED=1|0
  optional path override → TEST_CASE_TRAIL_PATH
