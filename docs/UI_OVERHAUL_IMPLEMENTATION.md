# AskMcNeese UI Overhaul — Implementation

**Date:** 2026-07-11  
**Status:** Implemented; test results are tracked separately in `docs/UI_TEST_RESULTS.md`.

## Summary

The overhaul replaced the original chat-only presentation with a responsive application shell, made the existing Server-Sent Events (SSE) path the frontend default, added sanitized live pipeline activity, and introduced an additive structured-answer contract. The original `answer` markdown remains the compatibility source of truth.

## Frontend changes

- `frontend/src/App.tsx` now orchestrates a responsive `NavRail`, conversation `Sidebar`, `Header`, chat surface, and three real panels.
- `frontend/src/components/layout/NavRail.tsx` is a bottom navigation bar on small screens and a left rail from the `md` breakpoint upward.
- `frontend/src/components/layout/Sidebar.tsx` supports local conversation search, date grouping, pinning, renaming, deletion, compact mode, and a mobile overlay.
- `frontend/src/components/layout/Header.tsx` shows the current view/conversation title and live backend health/version.
- `frontend/src/components/chat/ChatPage.tsx` owns the scrollable message log, empty state, loading activity, and composer.
- `frontend/src/components/chat/ChatInput.tsx` supports an auto-growing textarea, stop control, offline state, and a real knowledge-base/web-search scope selector.
- Conversation history and the collapsed-sidebar preference remain browser-local through `useConversations` and `useSidebarPrefs`.
- `SystemStatusPanel` reads the real `/health` and `/ask/stats` endpoints. `SettingsPanel` changes browser-local preferences/history. `FeedbackPanel` opens a populated email to `acm@mcneese.edu`.

There is no client router. `App.tsx` uses the `AppView` state union (`chat`, `status`, `settings`, `feedback`) to switch real in-app panels.

## Application shell

The visual hierarchy is:

1. `App` owns health, request, conversation, view, sidebar, and source-scope state.
2. `NavRail` initiates a new chat, focuses history, or selects Status, Settings, or Feedback.
3. `Sidebar` displays and manages locally stored conversations. It is a fixed drawer on mobile and an inline full/compact column on desktop.
4. The main column contains the sticky `Header`, an offline banner when needed, and the selected panel.
5. `ChatPage` renders `ChatBubble` messages and delegates assistant responses to `AssistantMessage` → `SemanticAnswer`.
6. During a request, `TypingIndicator` presents `ActivityTimeline`; the composer maps request state to submitting, retrieving, generating, stopped, failed, or offline UI.

The shell uses a 64 px navigation rail, 280 px sidebar, 64 px collapsed sidebar, 56 px header, and a 760 px maximum chat column from `frontend/src/styles/variables.css`.

## Streaming is the frontend default

`useAsk` always posts to `/ask` with:

- `stream: true`
- `Accept: text/event-stream`
- `use_web_search` derived from the selected source scope
- prior conversation turns as `history`

The response is consumed incrementally by a `ReadableStream` reader. `chunk` frames accumulate answer markdown, `citations` frames collect sources, `activity` and legacy `step` frames update the timeline, and `done` supplies final metadata and structured fields. An `AbortController` powers the Stop action.

The backend still supports non-streaming requests when another client sends `stream: false`; this preserves the existing API contract. The overhaul changed the web client default, not the endpoint’s request-model default.

## Markdown and semantic-answer fix

The former `AnswerCard` and `BentoFactGrid` components were removed. They attempted to parse markdown into presentation-specific fragments and could expose or mishandle heading markers.

The current path is:

- `AssistantMessage` delegates to `SemanticAnswer`.
- `SemanticAnswer` normalizes both new and legacy response shapes and conditionally renders semantic sections.
- `MarkdownRenderer` passes the intact markdown body to `react-markdown` with `remark-gfm`.
- Raw HTML is skipped, images are suppressed, and links open with `noopener noreferrer`.
- If the structured title duplicates the first markdown heading, only that duplicate heading is removed; the remaining markdown is not regex-rewritten into cards.

This keeps markdown parsing in a markdown parser while still allowing structured dates, requirements, steps, warnings, citations, and confidence states.

## Backend changes

- `AskResponse` retains all legacy fields and adds nullable structured fields.
- `structure_answer` performs best-effort extraction from the already-generated answer; it does not replace `answer` or invent institutional facts.
- Both streaming and non-streaming paths call `structure_answer`.
- SSE now emits sanitized canonical `activity` frames alongside the legacy `step`, `chunk`, `citations`, `done`, and `error` frames.
- The streaming `done` frame carries structured-answer fields and timing/query metadata.
- Activity payload construction and metadata allowlisting live in `backend/app/services/activity_events.py`.

## Real navigation destinations

Only implemented behavior is exposed:

- **New chat** — clears the selected conversation and returns to Chat.
- **History** — opens/expands the real local conversation sidebar and focuses its search field.
- **Status** — displays real `/health` and `/ask/stats` data.
- **Settings** — controls the persisted sidebar preference and clears local conversation history.
- **Feedback** — opens the user’s mail client with a message addressed to the project team.

Chat itself is reached by starting a new chat or selecting a conversation. No route or panel is claimed for a feature that does not exist.

## Intentionally not added

- **Voice input:** no microphone capture, transcription service, or voice control was added.
- **Attachments:** no file picker, upload API, storage, or document-processing path was added.
- **Campus directory:** no directory destination was added because there is no implemented directory data/API screen.
- **Saved answers:** conversations remain local history; there is no separate saved-answer model, backend persistence, or navigation destination.

These omissions are deliberate scope boundaries, not hidden or disabled navigation items.
