# Ask Flow Core Stability Report

**Date:** 2026-07-12  
**Scope:** Public Ask experience only  
**Method:** Static code inspection + limited runtime health check  
**Companion:** `docs/current-system-evidence-map.md`

---

## Critical Failures (P0)

*None confirmed as full Ask-flow blockers at static inspection time.*

Runtime health check succeeded (`GET /health` on `:8001` → ok). Composer is wired to real `POST /ask`.

| Candidate | Why not P0 yet | Required validation |
|-----------|----------------|---------------------|
| Wrong API port for new clones | Local `.env` uses `8001`; docs/example often `8000`; host may have other service on `8000` | Fresh clone smoke; document port |
| Empty ChromaDB | Would yield `no_source` / low confidence, not a crash | Ask with empty store |

---

## Trust-Damaging Issues (P1)

### P1-1 — Streaming parsed but answer not shown until complete

| Field | Detail |
|-------|--------|
| Priority | P1 |
| Finding | SSE `chunk` events are accumulated in `useAsk`, but `App.send` passes `undefined` for `onStreamUpdate`, so the message list never updates with partial text. |
| Evidence | `frontend/src/App.tsx` L65; `frontend/src/hooks/useAsk.ts` L149–151; `ChatMessage.isStreaming` unused (`types.ts` L32) |
| Observed | User sees activity bubble, then a sudden full answer |
| Expected | Either live partial rendering, or an honest product claim that answers appear when ready |
| Impact | Feels broken or “fake streaming”; long answers increase perceived latency |
| Root cause | Incomplete wiring after SSE client was added |
| Smallest safe correction | Wire `onStreamUpdate` to update a provisional assistant message with `isStreaming: true`, finalize on resolve; or remove stream UX claims and keep activity-only |
| Regression risk | Medium (message list flicker, duplicate bubbles) |
| Validation | Ask long question; confirm tokens appear progressively or docs match behavior |
| Confidence | Confirmed |

### P1-2 — `useAsk.error` discarded by App

| Field | Detail |
|-------|--------|
| Priority | P1 |
| Finding | Hook returns `error`, but `App` does not destructure or display it. Failed asks may leave only a user bubble with no assistant error card if return is null/throw path inconsistently handled. |
| Evidence | `useAsk.ts` returns `error`; `App.tsx` L29 omits it |
| Observed | Unverified without forced error |
| Expected | Visible, honest error in chat |
| Impact | Silent failure damages trust |
| Root cause | Incomplete error surfacing |
| Smallest safe correction | Destructure `error`; render error assistant message or toast; ensure catch path appends `isError` message |
| Regression risk | Low |
| Validation | Stop mid-flight; kill API; invalid key path |
| Confidence | Strong evidence |

### P1-3 — Documentation claims contradict runtime (trust / onboarding)

| Field | Detail |
|-------|--------|
| Priority | P1 (process / operator trust) |
| Finding | `frontend/README.md` still describes dummy Sprint-1 messages; `main.py` description says no LLM; `/ask/stats` and ask module docstring call web search “default” while `AskRequest.use_web_search` defaults to `False`. |
| Evidence | `frontend/README.md`; `backend/app/main.py` L7-ish; `ask.py` AskRequest + stats modes string |
| Impact | Developers misconfigure modes and ports; product claims unreliable |
| Smallest safe correction | Align README, FastAPI description, stats strings with code defaults |
| Regression risk | None (docs/strings only) |
| Confidence | Confirmed |

### P1-4 — Citation dedupe by title only

| Field | Detail |
|-------|--------|
| Priority | P1 |
| Finding | `CitationGroup` drops citations that share a lowercase title even if URLs differ. |
| Evidence | `CitationGroup.tsx` uniqueCitations by `c.title.toLowerCase()` |
| Impact | Distinct official pages may disappear from “Official sources” |
| Smallest safe correction | Dedupe by normalized URL (primary) + title secondary |
| Regression risk | Low |
| Validation | Fixture with same title, different URLs |
| Confidence | Confirmed |

---

## Responsive Failures (P1 / needs runtime)

### P1-5 — Header / zoom / first-message overlap (Unverified)

| Field | Detail |
|-------|--------|
| Priority | P1 if confirmed |
| Finding | Sticky header (`z-header`) + scrollable main; historical reports of first assistant response overlapping header at certain zooms. |
| Evidence | `Header.tsx` L14 sticky; `ChatPage` scroll main; no automated zoom test |
| Observed | **Unable to verify** in this pass without matrix |
| Expected | First message fully below header at 100–200% zoom |
| Smallest safe correction | Ensure scroll padding-top / first-item offset; avoid absolute message positioning |
| Validation | Matrix: 360, 390, 768, 1024, 1366, 1440 × 100%/125%/200% |
| Confidence | Unverified |

### P1-6 — Mobile keyboard / safe area (Unverified)

| Field | Detail |
|-------|--------|
| Priority | P1 if confirmed |
| Finding | Composer uses `pb-safe`; main column `pb-14` for bottom NavRail. Keyboard interaction not runtime-tested here. |
| Evidence | `ChatInput.tsx` `composerShell` + `pb-safe`; `App.tsx` L101 |
| Confidence | Probable risk |

---

## Accessibility Failures (P1)

### P1-7 — Live region / streaming announcement incomplete

| Field | Detail |
|-------|--------|
| Priority | P1 |
| Finding | Chat log has `aria-live="polite"`; typing indicator has `role="status"`. Partial answer text never enters the DOM during stream, so AT users get activity then a large dump. |
| Evidence | `ChatPage.tsx` main attrs; streaming gap P1-1 |
| Smallest safe correction | Same as P1-1 + ensure final answer is in the live region |
| Confidence | Strong evidence |

### P1-8 — Glass / reduced transparency fallbacks present; contrast not measured

| Field | Detail |
|-------|--------|
| Priority | P1 if contrast fails |
| Finding | `chat-glass.css` includes `@supports` solid fallbacks and `prefers-reduced-transparency`. WCAG contrast of glass-on-canvas not instrumented. |
| Evidence | `frontend/src/styles/chat-glass.css` |
| Validation | Contrast check tools + reduced transparency toggle |
| Confidence | Probable |

### Verified a11y strengths

- `:focus-visible` global outline (`index.css`)  
- Composer `aria-label` / `aria-describedby`  
- Citation expand `aria-expanded`  
- `prefers-reduced-motion` zeroes durations and disables typing-dot animation  
- Markdown `skipHtml: true`; links `rel="noopener noreferrer"`  

---

## Data-Integrity Failures

### P1-9 — Frontend activity SAFE_MESSAGES diverge from backend

| Field | Detail |
|-------|--------|
| Priority | P1 (trust / consistency) |
| Finding | Frontend remaps several events to fewer marketing strings; backend emits more specific SAFE_MESSAGES. If backend message is missing/sensitive, FE fallback may not match backend wording. |
| Evidence | `frontend/src/lib/activity.ts` vs `backend/app/services/activity_events.py` |
| Impact | Inconsistent narration across failure modes |
| Smallest safe correction | Prefer backend message when present; keep FE map as fallback only (already mostly true) — align maps |
| Confidence | Confirmed |

### P2 — `related_questions` always null

| Field | Detail |
|-------|--------|
| Priority | P2 / P3 |
| Finding | Structured field reserved; UI can render section but backend never fills it. |
| Evidence | `structured_answer.py` returns `None`; schema docs |
| Action | Do not invent questions client-side |
| Confidence | Confirmed |

### P2 — Non-stream HTTP response has no top-level `sources`

| Field | Detail |
|-------|--------|
| Priority | P2 |
| Finding | Streaming sends `citations` event; non-stream relies on `chunks`. Frontend `citationsFromResponse` handles both. |
| Evidence | `AskResponse` model; `answerModel.ts` |
| Impact | Low while FE always streams |
| Confidence | Confirmed |

---

## Maintainability Risks (P2)

| Issue | Evidence | Impact | Smallest action |
|-------|----------|--------|-----------------|
| `ask.py` very large (~1370 LoC) | File size | Hard to test/change safely | Extract only when touching area |
| Unused components | `CitationCard`, `SplashScreen`, `Skeleton`, `Button`, `Badge` unused | Confusion | Mark or delete in cleanup pass |
| ARCHITECTURE.md target ≠ tree | No `common/`, no split web_search | Wrong mental model | Label ARCHITECTURE as target vs current |
| Stale UI_OVERHAUL_AUDIT | Claims pre-structured fields / Inter | Misleads audits | Supersede with evidence map |
| Port 8000 vs 8001 | Apache may own 8000; FE `.env` → 8001 | Setup failures | Document in README |

---

## Verified Strengths

1. Real Ask pipeline: composer → `/ask` → retrieval → Claude → structured answer → UI  
2. Markdown headings/lists/emphasis rendered via `MarkdownRenderer` (not raw hashes when path used)  
3. Citations built from retrieval URLs, not LLM-invented citation objects  
4. Activity `elapsed_ms` is wall-clock based  
5. Stop control aborts fetch  
6. Offline detection disables send  
7. Centralized design tokens + answer typography + chat glass family  
8. Unit tests for structured answer, activity sanitize, markdown/SemanticAnswer  
9. Duplicate submission guarded by `isLoading` in App + ChatInput  

---

## Unknowns Requiring Runtime Validation

```text
- Header overlap at zoom levels
- Mobile keyboard vs composer
- Glass contrast / reduced transparency readability
- Mid-stream disconnect UX
- Empty knowledge base UX copy quality
- Many-citation overflow
- 360–1440 width matrix
- Keyboard-only full Ask flow
```

---

## Classification Summary

| ID | Title | Priority |
|----|-------|----------|
| P1-1 | Live chunk rendering not wired | P1 |
| P1-2 | Error state not surfaced in App | P1 |
| P1-3 | Stale docs / default-mode strings | P1 |
| P1-4 | Citation dedupe by title | P1 |
| P1-5 | Header/zoom overlap | P1 if confirmed |
| P1-6 | Mobile keyboard | P1 if confirmed |
| P1-7 | AT live answer updates | P1 (tied to P1-1) |
| P1-8 | Glass contrast measurement | P1 if fail |
| P1-9 | Activity message map drift | P1 |
| — | related_questions null | P2 |
| — | Monolithic ask.py / unused comps | P2 |
| — | Role dashboards / auth | P4 — blocked |

**First implementation pass must address P1-1 through P1-4 and P1-9, then runtime-validate P1-5/P1-6/P1-8. No P3/P4 route expansion.**
