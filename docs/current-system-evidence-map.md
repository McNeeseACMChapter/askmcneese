# Current System Evidence Map

**Date:** 2026-07-12  
**Mode:** Stage Zero — repository truth extraction (read-only)  
**Authority:** Actual code and runtime behavior over aspirational docs  
**Runtime spot-check:** `GET http://127.0.0.1:8001/health` → `{"status":"ok","service":"askmcneese-api","version":"0.1.0"}`; frontend HTTP 200 on local Vite port

---

## Current Stack

| Area | Verified implementation | Evidence | Confidence |
|------|-------------------------|----------|------------|
| Frontend framework | React 18.3.1 + react-dom 18.3.1 | `frontend/package.json` | Confirmed |
| Build | Vite 5.3.4, `@vitejs/plugin-react` 4.3.1 | `frontend/package.json`, `frontend/vite.config.ts` | Confirmed |
| Language | TypeScript 5.5.3, strict | `frontend/tsconfig.json` | Confirmed |
| Router model | **No react-router.** View state `AppView` in `App.tsx` | `frontend/src/App.tsx` L33, L105–108; `types.ts` L51 | Confirmed |
| Styling | Tailwind CSS 3.4.4 + PostCSS; CSS variables in `variables.css` | `package.json`, `tailwind.config.js`, `src/styles/variables.css` | Confirmed |
| Component libraries | None (no MUI/Chakra/Radix). Custom components + framer-motion | `package.json` dependencies | Confirmed |
| State management | Local React state + hooks (`useAsk`, `useConversations`, `useHealth`, `useSidebarPrefs`); `localStorage` persistence | `App.tsx`, `hooks/*` | Confirmed |
| Data fetching | Native `fetch` | `hooks/useAsk.ts`, `lib/api.ts` | Confirmed |
| Backend communication | `VITE_API_BASE_URL` (local `.env` = `http://127.0.0.1:8001`; example docs often cite `:8000`) | `frontend/.env`, `frontend/.env.example`, `lib/api.ts` | Confirmed |
| Streaming | HTTP POST `/ask` with `stream: true`; `Accept: text/event-stream`; manual SSE frame parser | `useAsk.ts` `askWithStream` | Confirmed |
| Markdown | `react-markdown` 10.1.0 + `remark-gfm` 4.0.1; `skipHtml: true` | `lib/markdown.tsx` | Confirmed |
| Fonts | Google Fonts: EB Garamond + Source Sans 3, `display=swap` | `frontend/index.html` L8–13 | Confirmed |
| Authentication | **Absent** (no login, JWT, session, or auth boundary) | Full `frontend/src` + `backend/app/main.py` | Confirmed |
| Testing (frontend) | Vitest 4.1.10 + Testing Library + jsdom | `package.json`; tests in `activity.test.ts`, `SemanticAnswer.test.tsx` | Confirmed |
| Backend | FastAPI ≥0.115, uvicorn, chromadb, anthropic, httpx, bs4, playwright, duckduckgo-search | `backend/requirements.txt` | Confirmed |
| Backend testing | Python `unittest` under `backend/tests/unit/`; eval harness under `backend/tests/eval/` | Directory listing | Confirmed |
| Build process (FE) | `npm run build` → `tsc --noEmit && vite build` | `package.json` scripts | Confirmed |

---

## Exact Current Route Tree

Derived from `App.tsx`. These are **not** URL routes; they are in-app views.

```text
App (single SPA mount #root)
├── NavRail (always)
├── Sidebar (history; open/collapsed by breakpoint + prefs)
└── Main column
    ├── Header (always)
    ├── Offline banner (conditional)
    └── View switch:
        ├── view === "chat"     → ChatPage
        ├── view === "status"   → SystemStatusPanel
        ├── view === "settings" → SettingsPanel
        └── view === "feedback" → FeedbackPanel
```

| View id | Entry | Component | Purpose |
|---------|-------|-----------|---------|
| `chat` (default) | Default state; new chat; select conversation | `ChatPage` | Public Ask experience |
| `status` | NavRail Status | `SystemStatusPanel` | Health / KB / LLM stats via `/ask/stats` + `/health` |
| `settings` | NavRail Settings | `SettingsPanel` | Sidebar prefs + clear history |
| `feedback` | NavRail Feedback | `FeedbackPanel` | Mailto ACM feedback |

**Backend HTTP routes (actual):**

| Method | Path | File |
|--------|------|------|
| GET | `/` | `backend/app/main.py` |
| GET | `/health` | `backend/app/routers/health.py` |
| POST | `/ask` | `backend/app/routers/ask.py` |
| GET | `/ask/stats` | `backend/app/routers/ask.py` |

No student/ACM/workspace/auth routes exist in code.

---

## Layout Ownership

| Region | Owning file | Notes |
|--------|-------------|-------|
| Root shell | `frontend/src/App.tsx` | Flex shell; no router outlet |
| Header | `frontend/src/components/layout/Header.tsx` | Sticky `z-header`, glass blur |
| Sidebar | `frontend/src/components/layout/Sidebar.tsx` | History; mobile overlay; desktop collapse |
| Mobile / desktop primary nav | `frontend/src/components/layout/NavRail.tsx` | Bottom bar on small screens (`pb-14` on main column) |
| Chat area | `frontend/src/components/chat/ChatPage.tsx` | Scrollable `main role="log"` + composer |
| Message list | `ChatPage.tsx` → `ChatBubble` | `chatMessageStack` gap |
| User prompt | `ChatBubble.tsx` | `.userMessage` glass |
| Assistant response | `AssistantMessage.tsx` → `SemanticAnswer.tsx` | `.assistantMessage` glass |
| Markdown body | `frontend/src/lib/markdown.tsx` | `.prose-answer` |
| Source / citation UI (live) | `CitationGroup.tsx` | Expandable list |
| Source card (unused) | `CitationCard.tsx` | **Not imported anywhere** |
| Composer | `ChatInput.tsx` | `.composerGlass` |
| Live status | `TypingIndicator.tsx` + `ActivityTimeline.tsx` | `.activityBubble` |
| Context panel | — | **Does not exist** |
| Authentication boundary | — | **Does not exist** |

---

## Data Flow — One Real Ask Request

```text
ChatInput.submit
  → App.send (guards: isLoading || health offline)
    → createConversation if needed (localStorage)
    → optimistic user ChatMessage
    → useAsk.ask(question, sourceScope, undefined, history)
         ↑ onStreamUpdate intentionally undefined
      → POST {API}/ask
         body: { question, stream: true, use_web_search, history }
      → SSE frames parsed (activity | step | chunk | citations | done | error)
      → accumulate fullText + citations + donePayload
      → normalizeAskResponse → ChatMessage with structured
    → append assistant message; persist conversation
  → ChatPage re-render
    → AssistantMessage → SemanticAnswer
      → MarkdownRenderer(content_markdown)
      → FactCardSection / ListSection (dates, requirements, steps, warnings)
      → CitationGroup(sources)
```

### Points where real data is / is not replaced

| Concern | Status | Evidence | Confidence |
|---------|--------|----------|------------|
| Request path | Real `fetch` to backend | `useAsk.ts` | Confirmed |
| Mock API client | **None** in production src | Grep `mock` in `frontend/src` | Confirmed |
| Streaming chunks to UI | **Parsed but not rendered live** — `App.send` passes `undefined` for `onStreamUpdate` | `App.tsx` L65 | Confirmed |
| `isStreaming` flag | Declared; never set/read | `types.ts` L32; no writers | Confirmed |
| Activity narration | Backend `activity` events + frontend `SAFE_MESSAGES` fallbacks + TypingIndicator defaults | `activity_events.py`, `lib/activity.ts`, `TypingIndicator.tsx` | Confirmed |
| Elapsed time | Real `perf_counter`-based `elapsed_ms` from backend when present | `activity_events.py`; unit test | Confirmed |
| Citations | From SSE `citations` event (retrieval URLs) or chunks fallback | `useAsk.ts`, `answerModel.ts`, `ask.py` | Confirmed |
| Hardcoded production citations | **None** | Grep; only test fixtures | Confirmed |
| EmptyState suggestions | Hardcoded starter questions; they call live `onSend` | `EmptyState.tsx` | Confirmed |
| `related_questions` | Backend always returns `null`; UI section stays empty | `structured_answer.py`; `RESPONSE_SCHEMA.md` | Confirmed |
| `isDemo` | UI badge exists; production always `isDemo: false` | `useAsk.ts`; `AssistantMessage.tsx` | Confirmed |

### SSE event types (backend → frontend)

| Event | Origin | Frontend handling |
|-------|--------|-------------------|
| `activity` | `activity_events.activity_payload` | Append to `activity[]` |
| `step` | Legacy | Mapped via `mapLegacyStep` |
| `chunk` | LLM token stream | Appended to `fullText`; callback unused by App |
| `citations` | Built from retrieval chunks/pages | `validCitations` |
| `done` | Final structured fields + metrics | Builds `AskResponse` |
| `error` | Sanitized message | Throws |

**Defined but not emitted by backend stream:** `query.rewritten`, `reranking.started`, `reranking.completed` (`docs/LIVE_ACTIVITY_EVENTS.md` + grep of `ask.py`).

---

## Current Design System (as implemented)

**Sources of truth (code):**

1. `frontend/src/styles/variables.css` — master tokens  
2. `frontend/src/styles/answer-typography.css` — answer primitives  
3. `frontend/src/styles/chat-glass.css` — chat glass family  
4. `frontend/tailwind.config.js` — maps vars to utilities  
5. `frontend/docs` narrative: `docs/DESIGN_SYSTEM.md` (largely aligned with variables; may lag glass chat tokens)

### Inventory (selected actual tokens)

| Category | Examples |
|----------|----------|
| Layout | `--header-height: 56px`, `--nav-rail-width: 64px`, `--sidebar-width: 280px`, `--chat-max-width: 760px` |
| Brand | `--brand-700`, `--accent-gold` |
| Surfaces | `--canvas`, `--surface`, `--surface-subtle` |
| Text | `--text-primary`, `--text-secondary`, `--text-muted` |
| Typography fonts | `--font-sans` (Source Sans 3), `--font-serif` / `--font-editorial` (EB Garamond), `--chat-font` |
| Chat body | `--chat-body-size`, `--chat-body-line-height: 1.62`, `--chat-body-weight: 450` |
| Answer scale | `--answer-title-size`, `--answer-summary-size`, `--answer-h2-size`, `--answer-h3-size`, … |
| Glass | `--glass-background`, `--glass-border`, `--glass-blur: 18px`, `--chat-radius: 20px` |
| Spacing | `--space-1`…`--space-16` (4px base); chat gaps `--chat-message-gap`, etc. |
| Motion | `--duration-fast/normal/slow`; reduced-motion zeroes durations |
| Focus | `--focus-ring`; `:focus-visible` in `index.css` |
| Z-index | `--z-header: 300`, `--z-overlay: 400`, `--z-splash: 1000` |

---

## Documentation-to-Code Validation

| System-design claim | Documentation source | Implementation evidence | Actual status | Observed difference | Required action |
|---------------------|----------------------|-------------------------|---------------|---------------------|-----------------|
| Shared `common/` package | `docs/ARCHITECTURE.md` §1–2 | No `common/` directory | Documented only | Target not built | Do not assume shared package |
| `web_search/` folder modules | `ARCHITECTURE.md` | Single `services/web_search.py` | Partially implemented | Monolith file | Split only if LoC/maintainability requires |
| Integration tests dir | `ARCHITECTURE.md` | No `backend/tests/integration/` | Documented only | — | Add when E2E needed |
| Backend read-only Chroma | README / ARCHITECTURE | `retrieval.py` read path | Implemented and verified | — | Preserve |
| Live web search + KB | README | `use_web_search` flag; default `False` | Implemented but behaves differently | Docstrings/stats say web is “default” | Align docs/strings with `AskRequest` default |
| No LLM (Sprint 2 shell) | `main.py` description comment | Full Claude pipeline in `llm.py` + `ask.py` | Contradicted by code | Stale comment | Update description |
| Frontend “dummy messages” / Sprint 1 only | `frontend/README.md` | Live `useAsk` SSE | Contradicted by code | README stale | Rewrite README |
| Inter font | Older `UI_OVERHAUL_AUDIT.md` | EB Garamond + Source Sans 3 in `index.html` | Deprecated claim | Audit outdated | Prefer DESIGN_SYSTEM + code |
| Structured answer fields | `RESPONSE_SCHEMA.md` | `AskResponse` + `structured_answer.py` | Implemented and verified | — | Keep |
| Streaming used in UI | Mixed: audit said unused; log said default | SSE parsed; **live chunk UI not wired** | Partially implemented | Activity streams; answer text waits for completion | P1: wire or document as batch |
| Auth / roles / dashboards | Future prompts / backlog | Absent in code | Future / not available | — | Blocked — do not build fake routes |
| `related_questions` | Schema reserved | Always `null` | Partially implemented | UI section never fills from backend | Leave empty or generate later with contract |
| Citations from real URLs | Architecture / safety docs | Built from chunk/page URLs | Implemented and verified | — | Preserve |

---

## Auth / Roles / Dashboards

| Capability | Contract status | Evidence |
|------------|-----------------|----------|
| Public Ask | Ready and verified | `/ask`, ChatPage |
| Health / stats panels | Ready and verified | `/health`, `/ask/stats` |
| Conversation history | Ready (client-only) | `localStorage` via `useConversations` |
| User accounts | Not available | No auth code |
| Student dashboard | Not available | No routes/components |
| ACM workspace | Not available | Mailto only in FeedbackPanel |
| Publishing / automation | Not available | — |

---

## Verified Strengths (brief)

- Real RAG path with ChromaDB and optional web search  
- Structured answer normalization frontend ↔ backend  
- Markdown rendered via parser (not raw `#` as text when `MarkdownRenderer` used)  
- Activity messages sanitized; elapsed_ms real  
- Citations from retrieval, not fabricated  
- Design tokens centralized; glass + answer typography systems exist  
- Stop/abort via `AbortController`  
- Offline banner + composer disable when health offline  

---

## Unknowns Requiring Runtime Validation

| Unknown | Required test |
|---------|---------------|
| Header overlap with first assistant message at 125%/200% zoom | Manual viewport matrix |
| Mobile keyboard covering composer / safe-area | Device or emulator |
| Glass contrast over canvas with reduced transparency | Browser preference toggle |
| Stream mid-connection drop UX | Kill backend mid-request |
| KB empty / cold Chroma behavior in UI | Run ask against empty collection |
| Long answer + many citations overflow | Fixture or live long query |
| Port confusion 8000 (Apache/docs) vs 8001 (local `.env`) | Onboarding smoke |
