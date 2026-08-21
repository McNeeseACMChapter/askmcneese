# Core Stabilization Runtime Validation

**Date:** 2026-07-12  
**Pass:** Core Stabilization Pass 1  
**Environment:** Windows 10, local Vite + uvicorn on `127.0.0.1:8001` (frontend `.env`), Chrome/automation via HTTP probes

---

## Results table

| Check | Environment | Viewport | Zoom or preference | Result | Evidence | Confirmed defect | Change made | Retest result |
|-------|-------------|----------|--------------------|--------|----------|------------------|-------------|---------------|
| API health | Local | n/a | n/a | Pass | `GET :8001/health` → ok | No | — | Pass |
| Frontend serves | Local | n/a | n/a | Pass | HTTP 200 on Vite | No | — | Pass |
| Unit tests FE | Vitest | n/a | n/a | Pass | 35/35 | No | — | Pass |
| Unit tests BE | unittest | n/a | n/a | Pass | 18/18 | No | — | Pass |
| Typecheck + build | Vite | n/a | n/a | Pass | `npm run build` ok | No | — | Pass |
| Header overlap vs scroll | Code | all | n/a | Mitigated (code) | Added `scroll-pt-[var(--header-height)]` on chat main | Unverified at real zoom | ChatPage scroll padding | Code-level only |
| Sticky header at 100% zoom | Manual browser | 1366 | 100% | **Not verified — requires manual browser validation** | — | — | — | — |
| Sticky header at 125% zoom | Manual browser | 1366 | 125% | **Not verified — requires manual browser validation** | — | — | — | — |
| Sticky header at 200% zoom | Manual browser | 1366 | 200% | **Not verified — requires manual browser validation** | — | — | — | — |
| Layout 360px | Code review | 360 | n/a | Probable ok | `pb-14` for mobile NavRail; max-w-chat; chat glass max widths | No confirmed defect | None speculative | — |
| Layout 390px | Code review | 390 | n/a | Probable ok | Same | No | None | — |
| Layout 768px | Code review | 768 | n/a | Probable ok | Sidebar overlay vs desktop rail | No | None | — |
| Layout 1024px+ | Code review | 1024–1440 | n/a | Probable ok | Desktop sidebar + rail | No | None | — |
| Mobile virtual keyboard | Device | mobile | n/a | **Not verified — requires manual device validation** | `pb-safe` present on composer | — | — | — |
| Reduced motion | CSS present | n/a | prefers-reduced-motion | Pass (static) | `chat-glass.css` disables typing-dot animation; variables zero durations | No | Existing | — |
| Reduced transparency | CSS present | n/a | prefers-reduced-transparency | Pass (static) | Solid fallbacks in `chat-glass.css` | Contrast not instrumented | None (no measured failure) | — |
| Keyboard flow | Manual | desktop | n/a | **Not verified — requires manual browser validation** | Focus-visible styles exist | — | — | — |
| Live streaming progressive text | Unit helpers + code path | n/a | n/a | Pass (unit) | `askSession` tests; App wires `onStreamUpdate` | Manual long-answer stream not run end-to-end | W1 implemented | Unit pass |
| Error card on failure | Unit | n/a | n/a | Pass | `useAsk.test.ts` | No | W2 | Pass |
| Abort no false error | Unit | n/a | n/a | Pass | `useAsk.test.ts` | No | W2 | Pass |
| Citation URL dedupe | Unit | n/a | n/a | Pass | `CitationGroup.test.tsx` | No | W3 | Pass |
| Mid-stream network drop | Manual | n/a | n/a | **Not verified** | — | — | — | — |
| Empty Chroma collection | Manual | n/a | n/a | **Not verified** | — | — | — | — |
| Very large citation sets | Manual | n/a | n/a | **Not verified** | — | — | — | — |

---

## Conditional code change from W6

| Defect | Action |
|--------|--------|
| Risk of first message heading sitting under sticky header when scrolling | Added `scroll-pt-[var(--header-height)]` on `ChatPage` main scroller |

No glass blur/radius token changes (no measured contrast failure).

---

## Accessibility notes (streaming)

- Chat log retains `aria-live="polite"` (additions).
- Streaming answer uses `aria-busy="true"` on the assistant article / answer shell.
- Token-level announcements are not forced via assertive live regions.
- Typing indicator is suppressed once a streaming answer bubble has text, to avoid competing status chrome.
