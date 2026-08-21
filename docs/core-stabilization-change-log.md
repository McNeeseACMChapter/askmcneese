# Core Stabilization Change Log — Pass 1

**Date:** 2026-07-12  
**Branch context:** `dev` (uncommitted working tree includes prior UI overhaul + this pass)

---

## Summary

Pass 1 made the public Ask flow truthful and more reliable: citation identity uses normalized URLs, Ask failures appear as one safe error card, activity fallbacks match backend wording, operator docs/default-mode strings were corrected, and SSE answer chunks render into one provisional assistant bubble that is replaced by a single final structured answer (without per-token localStorage writes).

---

## Work Items Completed

### W3 — Citation deduplication

| Field | Detail |
|-------|--------|
| Status | Complete |
| Files changed | `frontend/src/components/chat/CitationGroup.tsx`, `CitationGroup.test.tsx` (new) |
| Behavior before | Dedupe by lowercase title dropped distinct URLs |
| Behavior after | Primary key = normalized URL; same title + different URLs both keep; trailing-slash duplicates collapse; malformed URLs do not crash |
| Tests | 7/7 in `CitationGroup.test.tsx` |
| Limitations | Query-param canonicalization not applied beyond `URL` parsing |

### W2 — Error surfacing

| Field | Detail |
|-------|--------|
| Status | Complete |
| Files changed | `frontend/src/hooks/useAsk.ts`, `useAsk.test.ts` (new), `frontend/src/lib/askSession.ts`, `askSession.test.ts`, `App.tsx` |
| Behavior before | Failures could leave user message without a clear assistant error; abort error clearing incomplete |
| Behavior after | Non-abort failure → one `isError` assistant message; abort → `null` + `error=null`, provisional stream cleared; loading ends |
| Tests | `useAsk.test.ts` (fetch reject, HTTP 500, abort, stale error clear); `askSession` merge tests |
| Limitations | End-to-end App mount test not added (heavy); contract covered via hook + helpers |

### W4 — Activity-message alignment

| Field | Detail |
|-------|--------|
| Status | Complete |
| Files changed | `frontend/src/lib/activity.ts`, `activity.test.ts`, `TypingIndicator.tsx` |
| Behavior before | FE fallbacks drifted (e.g. “Preparing your answer”) |
| Behavior after | FE `SAFE_MESSAGES` match backend `activity_events.py`; backend message preferred when safe; TypingIndicator early copy aligned |
| Tests | Updated activity tests |
| Limitations | Backend still does not emit every defined event key |

### W5 — Documentation / default-mode truth

| Field | Detail |
|-------|--------|
| Status | Complete |
| Files changed | `frontend/README.md`, `frontend/.env.example`, `backend/app/main.py`, `backend/app/routers/ask.py` (strings + `ask_stream` default `False`), `README.md`, `backend/README.md` |
| Behavior before | Docs claimed Sprint-1 dummy UI / no LLM / web search default |
| Behavior after | Docs describe RAG+SSE, KB default, optional web search, port 8000/8001 sync with `VITE_API_BASE_URL` |
| Tests | n/a (docs); HTTP AskRequest default unchanged (`use_web_search=False`) |
| Limitations | Historical sprint docs under `docs/` left as historical records |

### W1 — Streaming answer rendering

| Field | Detail |
|-------|--------|
| Status | Complete |
| Files changed | `App.tsx`, `askSession.ts`, `SemanticAnswer.tsx`, `AssistantMessage.tsx`, `ChatPage.tsx`, tests |
| Behavior before | `onStreamUpdate` unused; full answer appeared at once |
| Behavior after | Transient provisional message per request/conversation; progressive markdown body only; final structured answer persisted once; stale callbacks ignored; abort clears provisional |
| Tests | `askSession.test.ts`; SemanticAnswer streaming-mode test |
| Limitations | Manual long-stream E2E against live Claude not executed in this pass |

### W6 — Runtime validation

| Field | Detail |
|-------|--------|
| Status | Partial — automated + static; manual zoom/keyboard/device deferred |
| Files changed | `ChatPage.tsx` (`scroll-pt` for sticky header); `docs/core-stabilization-runtime-validation.md` |
| Behavior before | Unverified header overlap risk |
| Behavior after | Scroll padding added; validation doc records what was / was not verified |
| Tests | Health probes; full unit suites |
| Limitations | Real browser zoom, mobile keyboard, mid-stream drop, empty Chroma, large citation sets |

---

## Exact File List (this pass)

### Modified

```text
README.md
backend/README.md
backend/app/main.py
backend/app/routers/ask.py
frontend/.env.example
frontend/README.md
frontend/src/App.tsx
frontend/src/components/chat/AssistantMessage.tsx
frontend/src/components/chat/ChatPage.tsx
frontend/src/components/chat/CitationGroup.tsx
frontend/src/components/chat/SemanticAnswer.tsx
frontend/src/components/chat/SemanticAnswer.test.tsx
frontend/src/components/chat/TypingIndicator.tsx
frontend/src/hooks/useAsk.ts
frontend/src/lib/activity.ts
frontend/src/lib/activity.test.ts
```

### Created

```text
frontend/src/components/chat/CitationGroup.test.tsx
frontend/src/hooks/useAsk.test.ts
frontend/src/lib/askSession.ts
frontend/src/lib/askSession.test.ts
docs/core-stabilization-change-log.md
docs/core-stabilization-runtime-validation.md
```

(Evidence docs from Stage Zero remain as previously created.)

---

## Test Results

| Command | Result | Notes |
|---------|--------|-------|
| `npm run test -- --run` (frontend) | Pass | 35 tests, 5 files |
| `npm run typecheck` | Pass | |
| `npm run build` | Pass | |
| `python -m unittest discover -s tests/unit -p "test_*.py"` | Pass | 18 tests |
| `git diff --check` | Pass | No whitespace errors reported |
| `GET http://127.0.0.1:8001/health` | Pass | ok |
| Frontend HTTP | Pass | 200 |

---

## Runtime Validation

See `docs/core-stabilization-runtime-validation.md`.

---

## Deferred Work

```text
Authentication
Student dashboard
ACM workspace
Route restructuring
Claim-level citation mapping
Server conversation history
related_questions generation
ask.py split
common/ extraction
Broad design-token revision
```

---

## Remaining Risks

- Real browser zoom (100/125/200%) not manually verified
- Mobile virtual keyboard vs composer not device-tested
- Reduced-transparency contrast not measured with tools
- Mid-stream network interruption UX not exercised live
- Empty Chroma collection UX not exercised live
- Very large citation lists not load-tested
- Working tree still contains prior uncommitted UI overhaul files alongside this pass
