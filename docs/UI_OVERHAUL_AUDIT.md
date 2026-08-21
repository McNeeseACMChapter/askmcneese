# AskMcNeese UI Overhaul — Repository Audit

**Date:** 2026-07-11  
**Scope:** Pre-implementation inventory of real frontend and backend surfaces. No invented paths.

---

## Frontend entry point

| Item | Path | Export / note |
|------|------|----------------|
| HTML shell | `frontend/index.html` | mounts `#root`, loads `/src/main.tsx` |
| Bootstrap | `frontend/src/main.tsx` | `ReactDOM.createRoot` → `<App />`, imports `./index.css` |
| Root app | `frontend/src/App.tsx` | `export default function App` |

## Framework and routing

| Item | Detail |
|------|--------|
| Framework | React 18 + Vite + TypeScript (`frontend/package.json`) |
| Routing | **None.** Single-page shell; no `react-router`. Navigation is local state in `App.tsx` |
| Styling | Tailwind CSS 3 (`frontend/tailwind.config.js`, `frontend/postcss.config.js`) |
| Motion | `framer-motion` (`frontend/src/lib/motion.ts`) |

## Global stylesheet

| Path | Role |
|------|------|
| `frontend/src/index.css` | Tailwind layers, root height, scrollbar, `.prose-answer` |
| `frontend/src/styles/variables.css` | CSS custom properties (layout, color, spacing, radius, shadow, z-index) |

## Existing theme / token system

| Path | Tokens |
|------|--------|
| `frontend/src/styles/variables.css` | `--color-primary`, `--color-accent`, surfaces, text, borders, shadows, radii, durations, z-index |
| `frontend/tailwind.config.js` | Maps tokens to Tailwind (`mcneese.*`, `surface`, `background`, `text-*`, etc.) |

**Gap vs target palette:** Current brand is `#00549F` / `#F2A900`. Target overhaul uses brand-950…50 and `--accent-gold: #f2b134`.

## Current font configuration

| Location | Configuration |
|----------|----------------|
| `frontend/src/index.css` `body` | `'Inter', ui-sans-serif, system-ui, ...` |
| `frontend/tailwind.config.js` `fontFamily.sans` | Same Inter stack |
| `frontend/index.html` | **No font `<link>` or `@font-face`.** Inter is referenced but not loaded. |
| Editorial / EB Garamond | **Not present.** |

## App shell components

| Role | Path | Export |
|------|------|--------|
| Shell / orchestration | `frontend/src/App.tsx` | `App` |
| Splash | `frontend/src/components/feedback/SplashScreen.tsx` | `SplashScreen` |
| Main chat viewport | `frontend/src/components/chat/ChatPage.tsx` | `ChatPage` |

## Header

| Path | Export |
|------|--------|
| `frontend/src/components/layout/Header.tsx` | `Header`, internal `StatusIndicator` |

Shows product name, menu button, health status/version.

## Sidebar / history

| Path | Export |
|------|--------|
| `frontend/src/components/layout/Sidebar.tsx` | `Sidebar`, internal `groupByDate` |

Supports: open/close (desktop hide / mobile drawer), new chat, select, delete, date grouping.  
**Missing vs target:** collapse preference persistence, rename, pin, overflow menu, history search, collapsed tooltips.

## Welcome-state

| Path | Export |
|------|--------|
| `frontend/src/components/chat/EmptyState.tsx` | `EmptyState` |
| `frontend/src/components/chat/SuggestionPill.tsx` | `SuggestionPill` |

Floating suggestion pills call `onSuggestionClick` → real `onSend` → `/ask`.

## Message list

| Path | Export |
|------|--------|
| `frontend/src/components/chat/ChatPage.tsx` | message map + scroll |
| `frontend/src/components/chat/ChatBubble.tsx` | `ChatBubble` (user bubble; delegates assistant) |

## Assistant response

| Path | Export |
|------|--------|
| `frontend/src/components/chat/AssistantMessage.tsx` | `AssistantMessage` |
| `frontend/src/components/chat/AnswerCard.tsx` | `AnswerCard`, `parseAnswerContent` |
| `frontend/src/components/chat/BentoFactGrid.tsx` | `BentoFactGrid`, `BentoFact` |
| `frontend/src/components/chat/MessageActions.tsx` | `MessageActions` (copy) |

## Markdown renderer

| Path | Library | Export / usage |
|------|---------|----------------|
| `frontend/src/components/chat/AnswerCard.tsx` | `react-markdown` + `remark-gfm` | `ReactMarkdown` with local `markdownComponents` |
| Dependencies | `frontend/package.json` | `react-markdown@^10.1.0`, `remark-gfm@^4.0.1` |

## Citation / source components

| Path | Export | Status |
|------|--------|--------|
| `frontend/src/components/chat/CitationGroup.tsx` | `CitationGroup` | **Used** by `AssistantMessage` |
| `frontend/src/components/chat/CitationCard.tsx` | `CitationCard` | **Orphan** — not imported elsewhere |

## Composer

| Path | Export |
|------|--------|
| `frontend/src/components/chat/ChatInput.tsx` | `ChatInput` |

States today: idle / disabled-while-loading. Enter to send, Shift+Enter newline. No stop, no source scope, no attachments.

## API client

| Path | Export / functions |
|------|---------------------|
| `frontend/src/hooks/useAsk.ts` | `useAsk`, `askWithoutStream`, `askWithStream`, `transformResponse` |
| `frontend/src/hooks/useHealth.ts` | `useHealth` → `GET /health` |
| Base URL | `import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"` |

**Note:** `App.tsx` calls `ask(text, undefined, history)` — streaming path is unused because `onStreamUpdate` is omitted.

## Streaming implementation

| Layer | Path | Detail |
|-------|------|--------|
| Backend SSE | `backend/app/routers/ask.py` → `ask_stream` | Events: `step`, `chunk`, `citations`, `done`, `error` |
| Frontend consumer | `frontend/src/hooks/useAsk.ts` → `askWithStream` | Parses `data:` JSON lines; AbortController present |
| WebSockets | — | **None** |

## Backend health endpoint

| Path | Handler | Response |
|------|---------|----------|
| `backend/app/routers/health.py` | `health` → `GET /health` | `{ status, service, version }` |
| Mounted in | `backend/app/main.py` | `app.include_router(health.router)` |

## Backend query endpoint

| Path | Handler | Contract |
|------|---------|----------|
| `backend/app/routers/ask.py` | `ask` → `POST /ask` | Body: `AskRequest` (`question`, `stream`, `use_web_search`, `history`) |
| Response model | `AskResponse` in same file | `question`, `answer`, `chunks[]`, `num_results`, `query_id`, `model`, `tokens_used`, `retrieval_ms`, `generation_ms`, `total_ms` |
| Stats | `ask_stats` → `GET /ask/stats` | KB / pipeline / LLM / web_search metadata |

## Existing WebSocket or SSE support

| Technology | Present? |
|------------|----------|
| SSE (`text/event-stream`) | **Yes** — `StreamingResponse` when `stream=true` |
| WebSocket | **No** |

## Current response schema (frontend types)

| Path | Types |
|------|-------|
| `frontend/src/types.ts` | `AskResponse`, `BackendChunk`, `ChatMessage`, `Citation`, `AnswerFact`, `Conversation`, `PipelineStep`, `StreamEvent`, `HealthStatus` |

Backend and frontend `AskResponse` fields align. No structured `answer_type` / `title` / `key_facts` yet — answer is a single markdown `answer` string.

## Current loading / status implementation

| Path | Export |
|------|--------|
| `frontend/src/hooks/useAsk.ts` | `AskStatus`: idle \| connecting \| searching \| generating \| complete \| error; `PipelineInfo` |
| `frontend/src/components/chat/TypingIndicator.tsx` | `TypingIndicator` — shows pipeline message + completed steps |
| `frontend/src/App.tsx` | Offline banner (currently exposes `uvicorn app.main:app` startup command — **must remove from public UI**) |

## Responsive breakpoints

| Source | Breakpoints in use |
|--------|-------------------|
| `App.tsx` `useMediaQuery` | `min-width: 1024px` (desktop sidebar), `min-width: 768px` (mobile vs tablet) |
| Tailwind defaults (used in classes) | `sm` 640, `md` 768, `lg` 1024 (e.g. Header menu `lg:hidden`, BentoFactGrid `sm`/`lg`) |
| CSS vars | `--header-height`, `--sidebar-width`, `--chat-max-width`, `--composer-min-height` |

No explicit 320 / 375 / 1440 / 1920 tokens; layout is fluid.

## Test locations

| Area | Path | Runner |
|------|------|--------|
| Backend unit | `backend/tests/unit/test_intent.py` | `unittest` |
| Backend unit | `backend/tests/unit/test_persona.py` | `unittest` |
| Backend unit | `backend/tests/unit/test_query_logging.py` | `unittest` |
| Backend unit | `backend/tests/unit/test_html_extraction.py` | `unittest` |
| Backend eval | `backend/tests/eval/run_eval.py` | eval harness |
| Frontend | — | **No unit/component test suite** (`package.json` has only `dev` / `build` / `preview`) |
| Root tests dir | `tests/` | present at repo root (inspect before assuming UI coverage) |

## Dead or duplicate components

| Path | Note |
|------|------|
| `frontend/src/components/chat/CitationCard.tsx` | Orphan; `CitationGroup` uses `CitationRow` instead |
| `frontend/src/components/ui/Button.tsx` | Check usage — may be lightly used |
| `frontend/src/components/ui/Badge.tsx` | Check usage |
| `frontend/src/components/feedback/Skeleton.tsx` | Check usage |
| `AnswerFact` in `types.ts` | Parallel to `BentoFact`; limited use |
| Duplicate API base constant | Hardcoded fallback in both `useAsk.ts` and `useHealth.ts` |

## Exact files responsible for visible raw markdown symbols such as `#`

| Path | Mechanism |
|------|-----------|
| `frontend/src/components/chat/AnswerCard.tsx` → `parseAnswerContent` | Custom line parser **strips / rewrites** markdown before `ReactMarkdown`. It only treats `## ` / `### ` as titles; **`# ` (ATX h1) is not extracted as title**. When `facts.length > 0`, **body markdown is discarded** (`bodyContent = ""`), so remaining content may be summarized via `cleanMarkdown` which uses regex stripping — incomplete parsing. |
| Same file → `cleanMarkdown` | Regex removes `#{1,6}` from summary strings; not a full markdown parser. |
| `backend/app/services/answer_format.py` → `format_chunks_as_answer` | Fallback answers often include `##` section headers from source chunks. |
| LLM answers (`backend/app/services/llm.py`) | May emit `#` / `##` headings in `answer` string. |

**Root cause hypothesis:** Visible `#` characters appear when (1) heading lines are not passed intact to `ReactMarkdown`, (2) title extraction leaves a bare `#` or partial line in summary/body, or (3) fact-greedy parsing empties body and leaves poorly cleaned text. Fix: stop using regex as the complete markdown parser; render full `content_markdown` through `react-markdown` + `remark-gfm`, with structured fields only when the API provides them.

## Conversations / persistence

| Path | Export |
|------|--------|
| `frontend/src/hooks/useConversations.ts` | `useConversations` — localStorage key `askmcneese_conversations` |

## Project instruction files read

| Path | Purpose |
|------|---------|
| `docs/frontend_guidelines.md` | Stack, brand, component rules |

## Implementation constraints derived from audit

1. Prefer existing **SSE** over WebSockets for live activity.
2. Preserve `POST /ask` / `AskResponse` / SSE event names; extend additively.
3. Do not mock answers; wire welcome cards to real `onSend` → pipeline.
4. Remove public `uvicorn` command from offline banner.
5. Do not add nav destinations without real screens (system status via `/health` + `/ask/stats` is valid; campus directory / saved answers need implementations or stay out).
