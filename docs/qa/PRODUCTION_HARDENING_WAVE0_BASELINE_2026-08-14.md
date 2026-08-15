# AskMcNeese production hardening Wave 0 baseline

Frozen at: 2026-08-14, America/Chicago

Backend: `http://127.0.0.1:8003`

Reported runtime flags:

- RCCS enabled: true
- hybrid retrieval available: true
- supervisor enabled: false
- official web search available: true
- backend version: 0.1.0

This artifact records the pre-Wave-1 behavior of the exact working tree used for the controlled hardening rollout. Each probe used a separate conversation and a non-streaming `/ask` request. The current response contract did not expose the internal route trace, evidence sufficiency decision, or release decision. Those fields are recorded as `UNAVAILABLE_PRE_WAVE_1`; they must not be reconstructed from output text.

## Summary

| Set | Correct task outcome | Safe clarification/no-source | Mean wall latency | Maximum wall latency |
| --- | ---: | ---: | ---: | ---: |
| Exact TC1-TC9 | 8/9 | 0/9 | 4,263 ms | 4,827 ms |
| Unseen paraphrases | 2/9 | 2/9 | 13,198 ms | 42,797 ms |

The exact-set defect was TC7: retrieval ranked the schedule-conflict service record first, but deterministic presentation answered with the lower-ranked Registrar record. The paraphrase set frequently bypassed structured specialists, entered slow live research, and cited unrelated sources.

## Exact probes

| TC | Question | Observed output | Result | Model | Evidence/source IDs | Wall / backend total |
| --- | --- | --- | --- | --- | --- | ---: |
| 1 | Where is the Office of the Registrar located, and what time does it close today? | Registrar at 4435 Ryan Street; Friday hours 7:30-11:30; closed now; opens Monday with countdown; regular-hours exception warning. | PASS | deterministic-direct | `ev-service-SERVICE-REGISTRAR-20260814`, `CUR-REGISTRAR-OFFICE`; an unused schedule-conflict evidence item was also returned. | 4,827 / 2,938 ms |
| 2 | I lost my McNeese ID card. Where do I get a replacement and how much does it cost? | University Police pickup, official form, $10 replacement charge, location and contact. | PASS | deterministic-direct | `ev-service-SERVICE-ID-CARDS-20260814`, `CUR-ID-CARDS` | 4,173 / 2,529 ms |
| 3 | I feel sick. Where can I get medical help on campus? | Student Health Services scope, location, contact, hours, cost caveat, and emergency guidance. | PASS | deterministic-direct | `ev-service-SERVICE-HEALTH-20260814`, `CUR-HEALTH-SERVICES` | 4,030 / 2,472 ms |
| 4 | What is the deadline to drop a Fall 2026 class without receiving an F? | Last withdrawal/resignation date: Tuesday, December 1, 2026, with official Fall 2026 schedule. | PASS | deterministic-direct | `CALENDAR-SNAPSHOT-FALL-2026`, `CUR-ACADEMIC-CALENDAR` | 4,101 / 2,473 ms |
| 5 | I am an international student. How do I get an I-20? | International Student Services guide and contacts; instructs student to obtain a case-specific decision. | PASS | deterministic-direct | `ev-service-SERVICE-INTERNATIONAL-CURRENT-20260814`, `CUR-INTERNATIONAL-CURRENT` | 4,107 / 2,508 ms |
| 6 | I do not know who my academic advisor is. What should I do? | Banner 9 -> Students -> Student Profile workflow and access contact. | PASS | deterministic-direct | `ev-service-SERVICE-ADVISOR-20260814`, `CUR-ADVISOR-WORKFLOW` | 4,028 / 2,424 ms |
| 7 | What happens if two of my classes are scheduled at the same time? | Answered with Registrar location/hours instead of the retrieved schedule-conflict workflow. | FAIL | deterministic-direct | Higher-scored `SERVICE-SCHEDULE-CONFLICT` plus lower-scored `SERVICE-REGISTRAR`; presenter chose Registrar. | 4,071 / 2,429 ms |
| 8 | Can you find all CSCI courses offered in Fall 2026 that do not conflict with Calculus II? | Listed four MATH 291 sections with details and asked which constraint CRN to use. | PASS/EXPECTED CLARIFICATION | deterministic-direct | `CLASS_PLANNER_CONFLICT_RESULT`, `CLASS_PLANNER` | 4,536 / 2,752 ms |
| 9 | How do I appeal a parking citation? | Online Traffic e-Appeal within seven calendar days, required fields, final decision, and Police contact. | PASS | deterministic-direct | `ev-service-SERVICE-PARKING-APPEAL-20260814`, `CUR-PARKING-APPEALS` | 4,494 / 2,736 ms |

## Unseen paraphrase probes

| TC | Question | Observed output | Result | Model | Evidence/source observation | Wall latency |
| --- | --- | --- | --- | --- | --- | ---: |
| 1 | Where can I find the registrar and are they still open right now? | Correct Registrar location and live status/countdown. | PASS | deterministic-direct | Correct Registrar evidence, but unused conflict evidence also returned. | 4,182 ms |
| 2 | My Cowboy Card vanished. What do I do and what is the replacement charge? | Correct ID workflow and $10 replacement charge. | PASS | deterministic-direct | Correct ID-card evidence. | 3,964 ms |
| 3 | I feel ill and need someone on campus to check me out. | Claimed no campus health source and recommended Police/local care. | FAIL | claude-sonnet-5 | Unrelated financial-aid appeal, probation, forms, parking, housing and admissions evidence. | 14,039 ms |
| 4 | During the autumn term, what is the last day I can leave one class and avoid an F? | `The requested academic term is not explicit.` | SAFE CLARIFICATION, SEMANTIC FAIL | clarification | No evidence released. | 17 ms |
| 5 | Who handles the paperwork that lets an international student study in the United States? | Incorrectly returned Registrar location/hours. | FAIL | deterministic-direct | Registrar evidence instead of International Student Services. | 4,377 ms |
| 6 | Banner does not show me who advises me. How can I locate that person? | Claimed no specific workflow; suggested Student Central. | FAIL | claude-sonnet-5 | Unrelated news/home/appeal/payment evidence. | 14,547 ms |
| 7 | My lectures overlap on the timetable. What are my options? | Generic advisor/Student Central/Class Search advice with a bad Registrar home-page link. | PARTIAL/FAIL | claude-sonnet-5 | Unrelated COVID webinar, reporting, home and news evidence. | 17,047 ms |
| 8 | Which fall 2026 computer science sections will not overlap MATH 291? | `I found related information, but not enough to answer accurately yet.` | SAFE NO-SOURCE, TASK FAIL | no_source | No citations released; only `SRC-011` matched. | 42,797 ms |
| 9 | A ticket was left on my windshield. How can I challenge it? | Claimed no parking appeal information; suggested Police/Parking Services. | FAIL | claude-sonnet-5 | Unrelated sports-ticket and campus-news evidence. | 17,808 ms |

## Pre-change contract gaps

- Route trace: `UNAVAILABLE_PRE_WAVE_1`
- Field resolution state: `UNAVAILABLE_PRE_WAVE_1`
- Contradictions: `UNAVAILABLE_PRE_WAVE_1`
- Claim/evidence ledger: `UNAVAILABLE_PRE_WAVE_1`
- Release decision and reason: `UNAVAILABLE_PRE_WAVE_1`
- JSON/SSE normalized parity: `UNVERIFIED_PRE_WAVE_1`
- Institutional-answer blocked rate cannot be measured reliably because the old contract has no release-decision field. The paraphrase set produced two observable clarification/no-source responses out of nine, but this is not equivalent to a deterministic release gate.

## Invariants for comparison

The post-Wave-4 comparison must use these same 18 isolated questions and additionally test their natural follow-ups. A post-change pass requires correct task resolution or an evidence-accurate clarification; an answer with unrelated sources is a failure even if its prose sounds cautious.
