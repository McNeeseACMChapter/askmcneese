# AskMcNeese Premium Live Research Trail

## Product decision

The trail is a **trust-calibrated observability surface**, not a terminal mirror and not a fake stepper.

It has three levels:

1. **Glance** — current phase, current truthful action, and elapsed time.
2. **Evidence** — the newest one or two sources actually read by the backend.
3. **Inspect** — an expandable, sanitized trace grouped into Understand, Search, Verify, and Write.

## Canonical phases

| Phase | Meaning |
|---|---|
| Understand | Intent and route planning |
| Search | Retrieve and read material |
| Verify | Rank evidence and validate citations |
| Write | Organize and stream the answer |

Never display a fake step number or percentage unless the backend has a genuinely fixed plan.

## Key files

| File | Role |
|---|---|
| `backend/app/services/activity_events.py` | Structured emitters (`activity_payload`, `operation_activity`, `source_activity`) |
| `frontend/src/lib/activity.ts` | Frontend sanitation / normalization |
| `frontend/src/lib/askRun.ts` | Parallel-aware reducer + `buildLiveTrail` |
| `frontend/src/hooks/useAsk.ts` | Immediate `onActivity` delivery; completion ownership |
| `frontend/src/App.tsx` | Run ownership; persist completed/cancelled trails |
| `frontend/src/components/chat/LiveAnswerProgress.tsx` | Trail UI |
| `frontend/src/styles/live-trail.css` | Visual + motion system |

## Public vs private

Never emit shell commands, prompts, paths, stack traces, credentials, SQL, or model chain-of-thought. Map private work to safe student-facing narration and validated public source URLs only.

## Removed legacy path

`TypingIndicator.tsx` and `ActivityTimeline.tsx` were deleted so `LiveAnswerProgress` + `AskRun` remain the single canonical trail.
