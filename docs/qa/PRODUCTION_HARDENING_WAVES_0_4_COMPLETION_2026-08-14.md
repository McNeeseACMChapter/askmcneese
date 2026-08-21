# AskMcNeese production hardening — Waves 0–4 completion report

Date: 2026-08-14 (America/Chicago)

Authorization boundary: Waves 0–4 only. Wave 5 and later work was not started.

## Outcome

The approved execution invariant is now implemented:

`one resolved task -> one authoritative CampusQuery -> one execution contract -> typed facts -> traceable claims -> deterministic release decision`

Final local runtime:

- Frontend: `http://127.0.0.1:5173/` — HTTP 200
- Hardened backend: `http://127.0.0.1:8004/health` — HTTP 200
- RCCS enabled; supervisor disabled, matching the frozen baseline configuration
- Rollback: `ASK_EXECUTION_V2=0` restores the legacy execution path

The exact TC1–TC9 set improved from 8/9 to 9/9. The unseen paraphrase set improved from 2/9 correct plus two safe failures to 8/9 correct plus one correct missing-year clarification. No final probe cited an unrelated source.

## Wave completion

### Wave 0 — frozen baseline

Complete. The fixed pre-change build, exact probes, paraphrases, outputs, source/evidence IDs, and wall/backend latency are preserved in `docs/qa/PRODUCTION_HARDENING_WAVE0_BASELINE_2026-08-14.md`.

The old API did not expose route traces, field resolutions, contradictions, claim ledgers, or release decisions. Those baseline values are recorded as unavailable rather than reconstructed.

### Wave 1 — canonical executor

Complete.

- Added the one authorized production file: `backend/app/services/ask_execution.py`.
- JSON and SSE call the same HTTP-neutral executor.
- Transport code remains in the FastAPI router.
- The old path remains available behind `ASK_EXECUTION_V2=0`.
- No SSE replay, reconnection, `Last-Event-ID`, or replay persistence was added.

### Wave 2 — compile once and typed task state

Complete.

- Every final exact and paraphrase probe reports `compiled_query_count = 1`.
- Classifier, planner, hybrid retrieval, supervisor compatibility path, evidence evaluation, and answer generation receive the same `CampusQuery` object.
- Query rewriting changes search text only; it does not replace the authoritative compiled task.
- Client task state is sanitized to selection/context fields only.
- Client-supplied fees, hours, deadlines, compatibility claims, and evidence are discarded.
- CRN-only and term-only replies are resolved through server task state.
- CRN 61066 is rehydrated against the backend Class Planner dataset before conflict computation.

### Wave 3 — structured specialists

Complete for the approved scope.

- Service-record and Class Planner specialists return structured result metadata.
- The Class Planner control path no longer stores or consumes a `direct_answer` prose field.
- The prior unreachable Class Planner prose/regex block was removed.
- Answer rendering consumes structured specialist data.
- Completed, fully released one-source tasks are presented as factual; genuinely incomplete planner-selection tasks remain partial.

### Wave 4 — typed evidence and fail-closed release

Complete.

- Required fields resolve as `MISSING`, `MENTIONED_UNRESOLVED`, `RESOLVED`, or `CONFLICTED`.
- Single-valued institutional conflicts block release.
- Material money, phone, email, date, URL, and CRN claims are checked against evidence.
- Citations are restricted to evidence IDs supporting released claims.
- When pages repeat the same value, provenance favors the source covering the most required task fields, then retrieval relevance.
- Evaluation failure, missing material evidence, unsupported material claims, citation failure, and unresolved contradictions fail closed.
- Query logs receive task type, release decision, field statuses, contradiction count, claim count, and targeted-recovery status without enabling raw-query debug logging.

## TC1–TC9 exact before/after

| TC | Mode | Baseline | Wave 4 result | Final source | Wall latency before -> after |
| --- | --- | --- | --- | --- | ---: |
| TC1 | Live office/directory | PASS | PASS; location, published hours, current open/closed state, next opening and countdown | Office of the Registrar | 4,827 -> 2,589 ms |
| TC2 | Governed student service | PASS | PASS; replacement workflow, form, office, fee and contact | University ID Cards | 4,173 -> 2,233 ms |
| TC3 | Health service | PASS | PASS; care scope, location, hours, contact and emergency guidance | Student Health Services | 4,030 -> 1,916 ms |
| TC4 | Academic calendar | PASS | PASS; December 1, 2026 withdrawal/resignation date | Fall 2026 | 4,101 -> 1,954 ms |
| TC5 | International service | PASS | PASS; current-student I-20 guidance and contacts | Current International Students | 4,107 -> 1,940 ms |
| TC6 | Advisor workflow | PASS | PASS; Banner 9 / Student Profile workflow and access contact | Find Your Academic Advisor | 4,028 -> 1,975 ms |
| TC7 | Administrative schedule conflict | FAIL; presenter selected Registrar | PASS; conflict-resolution options and correct contact | Class Listings Information | 4,071 -> 2,138 ms |
| TC8 | Structured Class Planner | PASS/clarification | PASS; detailed Calculus II choices and CRN request | McNeese Class Planner | 4,536 -> 2,253 ms |
| TC9 | Parking appeal | PASS | PASS; appeal form, seven-day rule and Police contact | Parking Citation Appeals | 4,494 -> 3,059 ms |

Exact-set summary:

- Correct task outcomes: 8/9 -> 9/9
- Mean wall latency: 4,263 -> 2,229 ms (47.7% lower)
- Maximum wall latency: 4,827 -> 3,059 ms
- Mean backend latency after: 1,329 ms
- Single authoritative compilation: 9/9
- Blocked: 0/9

## Unseen paraphrases before/after

| TC | Baseline | Wave 4 result | Final source | Wall latency before -> after |
| --- | --- | --- | --- | ---: |
| TC1 | PASS, with unused conflict evidence | PASS; only Registrar evidence released | Office of the Registrar | 4,182 -> 2,279 ms |
| TC2 | PASS | PASS | University ID Cards | 3,964 -> 2,030 ms |
| TC3 | FAIL; unrelated sources | PASS | Student Health Services | 14,039 -> 2,016 ms |
| TC4 | Safe but vague clarification | PASS; immediate explicit term-and-year clarification | No source released | 17 -> 844 ms |
| TC5 | FAIL; Registrar answer | PASS | Current International Students | 4,377 -> 2,238 ms |
| TC6 | FAIL; unrelated sources | PASS | Find Your Academic Advisor | 14,547 -> 1,953 ms |
| TC7 | PARTIAL/FAIL; unrelated sources | PASS | Class Listings Information | 17,047 -> 2,072 ms |
| TC8 | Safe no-source task failure | PASS; detailed MATH 291 choices and CRN request | McNeese Class Planner | 42,797 -> 1,971 ms |
| TC9 | FAIL; unrelated sports sources | PASS | Parking Citation Appeals | 17,808 -> 2,346 ms |

Paraphrase summary:

- Correct answers: 2/9 -> 8/9
- Correct bounded clarification: 1/9
- Mean wall latency: 13,198 -> 1,972 ms (85.1% lower)
- Maximum wall latency: 42,797 -> 2,346 ms
- Mean backend latency after: 1,117 ms
- Single authoritative compilation: 9/9
- Blocked: 0/9; one clarification released without institutional claims

## TC8 follow-up behavior

Browser and API verification passed:

1. The initial question listed all four Fall 2026 Calculus II sections with course, section, CRN, meeting pattern, room, modality, instructor, and remaining seats.
2. The system asked which Calculus II CRN should be used as the schedule constraint.
3. Replying only `61066` used the typed `awaiting_input` task state.
4. The backend rehydrated MATH 291 CRN 61066 and computed 21 non-conflicting CSCI sections.
5. The response included course/section/CRN, meetings, room, modality, instructor and seats.
6. It asked which CSCI CRNs to keep and offered a Class Planner review after the list is final.

No Class Planner mutation/action was emitted. That action semantics work belongs to Wave 5 and remains behind the review checkpoint.

The calendar clarification also passed: answering only `Fall 2026` after the missing-year prompt returned the correct December 1, 2026 date. `Why did you stop?` retained the typed task context and repeated the exact missing term/year requirement rather than starting unrelated research.

## Evidence, claim and release results

- Material and required-field claims across the final 18 isolated probes: 102
- Supported claims: 102
- Unsupported released claims: 0
- Released contradictory institutional fields: 0
- Final unrelated citations in TC1–TC9/paraphrases: 0
- Institutional-answer blocked rate in the final 18 probes: 0/18
- Clarification rate: 1/18
- Synthetic fail-closed checks passed for conflicting ID-card fees, an unsupported money claim, and unavailable evidence evaluation.
- `UNCERTAIN` is not represented as conflict-free; unresolved states remain missing/mentioned-unresolved or conflicted.

The regression blocked rate is zero because all answerable cases had governed evidence. This is not a permissive release result: adversarial unit probes confirm that conflicts and unsupported facts are blocked.

## JSON/SSE parity and rollback

Final normalized parity probe, using TC7:

- Answer: equal
- Answer type: equal
- Typed task state: equal
- Release decision: equal
- Claim ledger: equal
- Citation/source IDs: equal
- Source: `ev-service-SERVICE-SCHEDULE-CONFLICT-20260814` only
- Compiled-query count: JSON 1, SSE 1
- Local backend latency: JSON 1,207 ms; SSE 1,180 ms

TC1 contains a live countdown, so sequential requests can differ in derived clock text at a minute boundary. Transport parity is exact when normalized for request-time-derived countdown values; the time-independent TC7 probe was byte-equal for the logical fields above.

Live rollback probe:

- Server launched with `ASK_EXECUTION_V2=0`
- Legacy answer path returned a correct TC7 answer
- Legacy response omitted V2 `execution` and `release_decision`, confirming the old path was selected
- Probe latency: 1,647 ms

## Browser, frontend and backend verification

- In-app browser: TC1–TC9 passed through the actual SSE UI in isolated conversations.
- In-app browser: TC8 CRN-only follow-up passed as the tenth isolated guest question.
- The browser suite used an isolated temporary guest database; the real guest quota database was not reset or modified.
- Backend: 303 tests passed, 33 subtests passed.
- Backend warnings: two pre-existing collection/deprecation warnings; no failures.
- Backend compile check: `python -m compileall -q app` passed.
- Frontend: 34 test files passed, 226 tests passed.
- Frontend 100-turn ordering tests passed.
- Frontend production build passed; Vite reported the existing large-main-chunk warning.
- `git diff --check` passed; Git printed line-ending conversion warnings only.

## Exact files changed in this authorization

Production/backend:

- `backend/app/routers/ask.py`
- `backend/app/services/ask_execution.py` — new; the only production file created in this authorization
- `backend/app/services/campus_intelligence/compiler.py`
- `backend/app/services/campus_intelligence/evidence.py`
- `backend/app/services/campus_intelligence/models.py`
- `backend/app/services/campus_intelligence/specialists.py`
- `backend/app/services/conversation_context.py`
- `backend/app/services/llm.py`
- `backend/app/services/orchestrator/supervisor.py`
- `backend/app/services/persona.py`
- `backend/app/services/query_logger.py`
- `backend/app/services/rccs/ask_integration.py`
- `backend/app/services/rccs/citations.py`
- `backend/app/services/rccs/classify.py`
- `backend/app/services/rccs/hybrid.py`
- `backend/app/services/rccs/models.py`
- `backend/app/services/rccs/plan.py`
- `backend/app/services/verified_service_answer.py` — already present as an untracked user/worktree file before this authorization; modified, not created here

Frontend:

- `frontend/src/App.tsx`
- `frontend/src/hooks/useAsk.ts`
- `frontend/src/types.ts`

Tests and QA:

- `backend/tests/unit/test_ask_execution.py` — new, 11 invariant tests
- `frontend/src/hooks/useAsk.test.ts`
- `frontend/src/conversation-boundary.test.ts`
- `docs/qa/PRODUCTION_HARDENING_WAVE0_BASELINE_2026-08-14.md` — new
- `docs/qa/PRODUCTION_HARDENING_WAVES_0_4_COMPLETION_2026-08-14.md` — this report

No deployment dependency, auth/privacy boundary, middleware architecture, quota semantics, Chroma infrastructure, Class Planner publication/sync boundary, Banner registration boundary, unrelated CSS, or onboarding behavior was refactored for this work.

## LOC and git accounting

The worktree was already dirty before this authorization. Therefore, Git cannot produce a truthful implementation-only delta from the current index. No pre-existing user changes were reset or overwritten.

Reproducible current-worktree accounting:

- Authorization-touched tracked paths versus `HEAD`: +1,983 / -107 lines across 21 files.
- Authorization-created files before this report: 959 lines total:
  - `ask_execution.py`: 553
  - `test_ask_execution.py`: 340
  - Wave 0 baseline: 66
- Measurable scoped subtotal before this report: +2,942 / -107.
- `verified_service_answer.py` is excluded from implementation-only LOC attribution because it was already an untracked worktree file before this authorization.
- Whole dirty tracked worktree `git diff --stat`: 34 files changed, 2,359 insertions, 122 deletions. This includes unrelated/pre-existing changes and excludes all untracked files.

## New invariant coverage

The new backend tests cover:

- malicious/stale client institutional facts being discarded
- CRN-only typed follow-up
- term-only typed follow-up
- bounded constraint-course parsing
- explicit rollback flag behavior
- conflicting authoritative fees becoming `CONFLICTED`
- unsupported material claims
- claim-ledger citation allow-list behavior
- strongest task-relevant fact provenance
- missing evidence-evaluation metadata failing closed
- JSON/SSE shared logical final contract

Existing and updated suites additionally cover Class Planner data rehydration, 100-turn ordering, frontend task-state transport, and confirmed/compatible-only planner action application.

## Remaining UNVERIFIED or intentionally deferred

- Wave 5 Class Planner selection persistence, compatibility confirmation and planner write actions: intentionally not implemented.
- Waves 6–7 comprehensive department/office directory expansion and governance rollout: intentionally not implemented. Current live-hours behavior is only as complete as the governed office records currently present.
- SSE replay/reconnection/idempotency: intentionally not implemented.
- Targeted missing-field recovery is structurally limited to one branch/attempt and emits route metadata, but the final 18-probe set did not naturally trigger that upstream-recovery path. A controlled upstream-failure integration test remains UNVERIFIED.
- The supervisor runtime is disabled in the frozen configuration. Compatibility was preserved and unit-tested, but the supervisor-enabled production route remains UNVERIFIED in this checkpoint.
- Contradictory institutional evidence was tested deterministically with synthetic official records; a real live upstream contradiction did not occur during the final run.
- Latency results are sequential local measurements, not a concurrency/load benchmark.
- No production deployment or remote environment rollout was performed.

## Checkpoint decision

Waves 0–4 meet the approved local completion gates: deterministic single compilation, shared transport execution, server-authoritative task state, structured specialist control data, typed evidence, claim-level support, restricted citations, fail-closed release, rollback, full regressions, and browser verification.

STOP at this checkpoint. Wave 5 requires a new review and authorization.
