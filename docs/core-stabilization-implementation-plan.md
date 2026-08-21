# Core Stabilization Implementation Plan

**Date:** 2026-07-12  
**Gate:** Evidence docs complete — application code changes may begin **only** within this scoped plan  
**Scope lock:** Verified P0/P1 Ask-flow issues only. No dashboards, auth shells, or route-group restructure.  
**Sources:** `docs/current-system-evidence-map.md`, `docs/ask-flow-core-stability-report.md`, `docs/current-vs-target-architecture-comparison.md`

---

## Goals for Pass 1

1. Make Ask response lifecycle truthful (stream or honest batch).  
2. Surface failures in the conversation UI.  
3. Stop dropping distinct sources that share a title.  
4. Align operator-facing docs/default-mode strings with code.  
5. Align frontend activity fallbacks with backend SAFE_MESSAGES.  
6. Runtime-validate layout/a11y unknowns; fix only confirmed defects.

**Out of scope:** student/ACM portals, auth, token redesign, `common/` extraction, ask.py split, inventing `related_questions`.

---

## Implementation Work Items

### W1 — Wire live streaming into message state (P1-1, P1-7)

| Field | Detail |
|-------|--------|
| File path | `frontend/src/App.tsx` |
| Current responsibility | Orchestrates send; ignores stream callback |
| Verified problem | `ask(..., undefined, history)` drops partial text |
| Proposed change | Pass `onStreamUpdate` that upserts a provisional assistant `ChatMessage` with `isStreaming: true`; on resolve replace with final message; on abort/error clear or mark error |
| Why smallest safe change | Reuses existing `useAsk` callback; no protocol change |
| Dependencies | `useAsk.ts`, `ChatMessage` type, `AssistantMessage`/`SemanticAnswer` tolerance for partial markdown |
| Regression risk | Medium — duplicate assistants, flicker |
| Test | Unit: mock stream updates message; manual: long answer shows progressive text; reduced-motion still ok |

| Field | Detail |
|-------|--------|
| File path | `frontend/src/hooks/useAsk.ts` |
| Current responsibility | SSE parse + accumulate |
| Verified problem | Complete; may need small helpers for cleaner App integration |
| Proposed change | Only if App wiring needs clearer status/`isStreaming` signaling — prefer App-only first |
| Why smallest | Avoid hook rewrite |
| Dependencies | — |
| Regression risk | Low if untouched |
| Test | Existing activity tests still pass |

| Field | Detail |
|-------|--------|
| File path | `frontend/src/components/chat/SemanticAnswer.tsx` / `markdown.tsx` |
| Current responsibility | Render final structured answer |
| Verified problem | Partial markdown during stream may be unstable |
| Proposed change | While `isStreaming`, render markdown body only (skip fragile structured sections until done) **or** show plain accumulating text |
| Why smallest | Prevents half-parsed structured chrome during stream |
| Dependencies | W1 App flag |
| Regression risk | Medium |
| Test | Stream fixture with incomplete heading |

---

### W2 — Surface Ask errors in chat (P1-2)

| Field | Detail |
|-------|--------|
| File path | `frontend/src/App.tsx` |
| Current responsibility | Ignores `useAsk().error` |
| Verified problem | Failures may leave orphan user messages |
| Proposed change | Destructure `error`; on failure append assistant message with `isError: true` and safe text; clear on next send |
| Why smallest | Uses existing `SemanticAnswer` error branch |
| Dependencies | `useAsk` error string / throw behavior |
| Regression risk | Low |
| Test | Mock fetch reject; abort → no false error; API 500 → error card |

| Field | Detail |
|-------|--------|
| File path | `frontend/src/hooks/useAsk.ts` |
| Current responsibility | Sets `error` / returns null on abort |
| Verified problem | App does not consume |
| Proposed change | Ensure non-abort failures set `error` and return null consistently; abort remains silent cancel |
| Why smallest | Clarify contract only |
| Dependencies | W2 App |
| Regression risk | Low |
| Test | Unit around catch paths |

---

### W3 — Citation dedupe by URL (P1-4)

| Field | Detail |
|-------|--------|
| File path | `frontend/src/components/chat/CitationGroup.tsx` |
| Current responsibility | Expandable sources; dedupe by title |
| Verified problem | Distinct URLs with same title collapsed |
| Proposed change | Dedupe key = normalized URL (strip trailing slash / lowercase host); fallback to title+url |
| Why smallest | Local function change |
| Dependencies | None |
| Regression risk | Low |
| Test | Vitest: same title different URLs both render; exact duplicate URL once |

---

### W4 — Align activity fallback maps (P1-9)

| Field | Detail |
|-------|--------|
| File path | `frontend/src/lib/activity.ts` |
| Current responsibility | Sanitize + fallback SAFE_MESSAGES |
| Verified problem | Wording diverges from backend `activity_events.py` |
| Proposed change | Match backend default strings for shared event keys; keep sanitize rules |
| Why smallest | Copy alignment only |
| Dependencies | Update `activity.test.ts` expectations |
| Regression risk | Low |
| Test | Existing sanitize tests + message equality samples |

| Field | Detail |
|-------|--------|
| File path | `frontend/src/components/chat/TypingIndicator.tsx` |
| Current responsibility | Default status copy when no activity yet |
| Verified problem | Mild drift vs backend early events |
| Proposed change | Align default strings with backend early stages |
| Why smallest | String constants |
| Dependencies | — |
| Regression risk | None |
| Test | Smoke |

---

### W5 — Operator truth: docs and default-mode strings (P1-3)

| Field | Detail |
|-------|--------|
| File path | `frontend/README.md` |
| Current responsibility | Frontend setup narrative |
| Verified problem | Describes dummy Sprint-1 shell |
| Proposed change | Document real Ask SSE, views, `.env` port, no auth |
| Why smallest | Docs only |
| Dependencies | — |
| Regression risk | None |
| Test | Human review |

| Field | Detail |
|-------|--------|
| File path | `backend/app/main.py` |
| Current responsibility | App factory description |
| Verified problem | Says no LLM |
| Proposed change | Update description to current RAG+LLM reality; keep “no auth” |
| Why smallest | String |
| Dependencies | — |
| Regression risk | None |
| Test | OpenAPI title/description glance |

| Field | Detail |
|-------|--------|
| File path | `backend/app/routers/ask.py` |
| Current responsibility | Ask orchestration + `/ask/stats` |
| Verified problem | Module docstring + `modes.web_search` claim “default” while `AskRequest.use_web_search` defaults `False` |
| Proposed change | Change strings to “optional / when use_web_search=true”; leave default `False` |
| Why smallest | No behavior change |
| Dependencies | Frontend source scope already maps knowledge→false, web→true |
| Regression risk | None |
| Test | Stats payload string assert optional |

| Field | Detail |
|-------|--------|
| File path | Root `README.md` (if port section wrong) |
| Proposed change | Note Windows port conflict: prefer `8001` when `8000` occupied; match `frontend/.env` |
| Why smallest | Docs |
| Regression risk | None |

---

### W6 — Runtime validation matrix (P1-5, P1-6, P1-8) — no code until confirmed

| Check | Method | If fails → smallest fix |
|-------|--------|-------------------------|
| Header overlap 100/125/200% | Manual Ask with tall first answer | Add scroll-padding-top on chat main / ensure sticky offset |
| Widths 360–1440 | Resize + screenshot notes | Fix specific overflow (sidebar, composer, message max) |
| Mobile keyboard | Emulator | Adjust composer sticky/safe-area |
| Reduced transparency | OS/browser pref | Raise solid fallback opacity in `chat-glass.css` only if contrast fails |
| Reduced motion | Pref | Confirm dots static (already coded) |
| Keyboard Ask flow | Tab through composer, send, sources | Fix missing focus rings if found |

**Do not change glass blur tokens without measured failure.**

---

## Ordered Execution

```text
1. W3 Citation dedupe (lowest risk, high trust)
2. W2 Error surfacing
3. W4 Activity string alignment
4. W5 Docs / default-mode strings
5. W1 Streaming wire-up (highest regression risk — last among code fixes)
6. W6 Runtime matrix → conditional layout/contrast fixes only
```

After code changes, record:

```text
docs/core-stabilization-change-log.md
```

---

## Explicit Non-Goals (Stop Conditions)

Stop and document — do **not** implement workarounds that look production-ready — if:

- Auth or role APIs are required for a requested feature  
- A change needs inventing `related_questions` or fake citations  
- Token redesign is requested without contrast/perf evidence  
- Multi-role route groups are requested before Ask P1 closure  

---

## Success Criteria

| Criterion | Pass condition |
|-----------|----------------|
| Truthful response UX | Partial tokens visible **or** product copy no longer implies live typing of the answer |
| Errors visible | Failed Ask shows assistant error card |
| Citations | Same-title different-URL sources both listed |
| Docs | README + API description + stats mode strings match `use_web_search` default |
| Activity | FE fallbacks match backend SAFE_MESSAGES for shared keys |
| Regressions | `npm run test`, `npm run typecheck`, backend `unittest` discover still pass |
| No scope creep | No new routes, auth, or dashboards in the diff |

---

## File Touch List (expected)

```text
frontend/src/App.tsx
frontend/src/hooks/useAsk.ts                    # only if needed for W1/W2
frontend/src/components/chat/CitationGroup.tsx
frontend/src/components/chat/SemanticAnswer.tsx  # streaming-safe render if needed
frontend/src/components/chat/TypingIndicator.tsx
frontend/src/lib/activity.ts
frontend/src/lib/activity.test.ts
frontend/src/components/chat/SemanticAnswer.test.tsx  # citation cases if added
frontend/README.md
backend/app/main.py
backend/app/routers/ask.py                       # docstring + stats strings only
README.md                                        # port note if needed
docs/core-stabilization-change-log.md            # after implementation
```

Optional after W6 confirmation only:

```text
frontend/src/components/chat/ChatPage.tsx
frontend/src/styles/chat-glass.css
frontend/src/components/layout/Header.tsx
```
