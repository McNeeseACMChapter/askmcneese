ASKMCNEESE SYSTEM TRUTH AUDIT
Snapshot date: 2026-08-15
Audience: owner, Cursor, developers, reviewers
Document type: evidence-based repository and runtime assessment

PURPOSE

This folder describes what AskMcNeese actually is today. It deliberately separates implemented architecture from demonstrated capability. It does not assume that a route, taxonomy entry, provider key, source URL, unit test, or successful HTTP response proves that the system can answer the corresponding question correctly.

The correct current description is:

AskMcNeese is a beta, source-governed campus information and class-planning system with several strong deterministic workflows and a broad but uneven retrieval layer. It is not yet a general campus-intelligence system that can reliably tackle every arbitrary, compound, ambiguous, current, or conversational problem.

This audit was produced without changing application code, configuration, databases, or running services. Only the TXT files in this folder were added during this documentation pass.

READING ORDER

1. 01_EXECUTIVE_SYSTEM_TRUTH.txt
2. 02_CODEBASE_AND_RUNTIME_MAP.txt
3. 03_ASK_EXECUTION_FLOW.txt
4. 04_PROVEN_STRENGTHS.txt
5. 05_STRUCTURAL_WEAKNESSES.txt
6. 06_CAPABILITY_REALITY_MATRIX.txt
7. 07_DATA_AND_RETRIEVAL_REALITY.txt
8. 08_FRONTEND_PLANNER_GUEST_AND_ACM.txt
9. 09_TESTING_AND_METRICS_REALITY.txt
10. 10_RECENT_HARDENING_AND_REGRESSION_RISK.txt
11. 11_CURSOR_SAFE_NEXT_STEPS.txt
12. 12_EXISTING_DOCUMENTATION_INDEX.txt
13. 13_CURRENT_RUNTIME_SNAPSHOT.txt

EVIDENCE USED

- Current repository source code and configuration registries
- Current documentation under docs/, crawler/, knowledge/, and acm/
- Current /health, /ask/stats, and Class Planner read-only API responses
- Current source and index manifests
- Current query log summaries and selected recent route traces
- Test suite results already executed in this workspace
- Current Git working-tree state

IMPORTANT INTERPRETATION RULES

- “Configured” means a switch or credential exists. It does not prove reachability or correct results.
- “Registered” means a URL is known and governed. It does not mean its content is indexed or current.
- “Indexed source” is only useful if it has positive chunk coverage.
- “CAN_RELEASE” means the release gate accepted the pipeline’s own evidence rules. It does not prove the route chose the right domain or that the evidence answers the user’s real intent.
- “Success” in current query statistics means final_status equals success. It is not an answer-quality grade.
- Unit tests prove selected contracts and fixtures. They do not prove universal question handling.
- A 50,000-query planning corpus expands routing vocabulary. It does not contain 50,000 verified answers.

NON-GOAL

This folder does not prescribe a quick patch. The next step should be a controlled evaluation and architecture decision, not another set of question-specific conditions.
