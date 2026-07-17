# AskMcNeese Live Activity Events

AskMcNeese streams progress and answer data over Server-Sent Events (SSE) from `POST /ask` when `stream: true`. The frontend requests this mode by default.

## SSE framing

Each frame uses the standard form:

```text
event: activity
data: {"request_id":"...","event":"retrieval.started","message":"Searching official McNeese sources","elapsed_ms":12,"metadata":{"mode":"knowledge_base"}}

```

The frontend accepts CRLF or LF input, buffers partial frames, joins multiple `data:` lines, and JSON-parses complete frames.

## Event types

| SSE event | Role |
|---|---|
| `activity` | Canonical, sanitized user-facing pipeline progress. |
| `step` | Legacy pipeline progress retained for compatibility. |
| `chunk` | Incremental answer text in `data.text`. |
| `citations` | Citation array in `data.citations`. |
| `done` | Final query/result/timing metadata and structured-answer fields. |
| `error` | Sanitized user-facing failure message. |

The backend emits canonical `activity` events alongside legacy events. Existing consumers can continue using `step`/`chunk`/`citations`/`done`/`error`; new activity UI should prefer `activity`.

## Canonical activity payload

```json
{
  "request_id": "server-generated query id",
  "event": "retrieval.completed",
  "message": "Finished gathering sources",
  "elapsed_ms": 247,
  "metadata": {
    "sources_found": 4,
    "duration_ms": 231,
    "mode": "knowledge_base"
  }
}
```

- `request_id`: request correlation identifier. When the client sends a safe `request_id` on `POST /ask`, the stream reuses it so live activity can bind to that turn. Otherwise the server generates one.
- `run_id`: optional client run id echoed on activity payloads for turn-owned UI.
- `event`: canonical dot-separated event name.
- `message`: short user-facing status text.
- `elapsed_ms`: milliseconds since the stream request began.
- `metadata`: allowlisted, non-sensitive context only.

The frontend also accepts camelCase `requestId` and `elapsedMs` defensively, but the backend emits snake_case.

## Canonical event vocabulary

Defined in `backend/app/services/activity_events.py`:

| Name | Safe default message |
|---|---|
| `request.accepted` | Request received |
| `query.analyzing` | Understanding your question |
| `query.rewritten` | Refining search terms |
| `retrieval.started` | Searching official McNeese sources |
| `retrieval.source_found` | Found relevant sources |
| `retrieval.completed` | Finished gathering sources |
| `reranking.started` | Ranking the most useful sources |
| `reranking.completed` | Sources ranked |
| `answer.generating` | Writing your answer |
| `citations.validating` | Checking citations |
| `answer.completed` | Answer ready |
| `request.failed` | Something went wrong |

This is the canonical vocabulary, not a promise that every request emits every event. The current `/ask` stream emits the applicable accepted, analyzing, retrieval, citation, generation, completion, and failure events. `query.rewritten` and reranking events are defined for consistent future instrumentation but are not currently emitted by `ask_stream`.

## Legacy event mapping

`frontend/src/lib/activity.ts` converts a legacy `step` payload into an activity item:

- `{step: "generation", status: "started"}` → `answer.started`
- other steps retain their name, for example `retrieval.completed` or `search.started`
- `status` is copied to safe metadata
- `duration_ms` becomes `elapsedMs`

Because canonical and legacy progress are both emitted, the current timeline may show both forms. This is intentional transport compatibility; consumers should not infer that legacy step names are part of the canonical vocabulary.

## Sanitization

### Backend

`activity_payload` supplies a predefined message unless the caller explicitly supplies one. `safe_metadata` permits only:

- `sources_found`
- `num_results`
- `mode`
- `duration_ms`
- `status`

Values must be strings, numbers, booleans, or null. String values containing a backslash or beginning with `/` are removed to avoid exposing path-like internals. Exceptions, prompts, stack traces, API keys, database details, and raw internal diagnostics are not placed in SSE activity/error frames. The server logs the original exception separately while sending the safe `request.failed` message.

### Frontend

The frontend applies a second boundary:

- metadata is re-allowlisted to the same five keys;
- messages containing Windows/user/system paths, `api key`, `token`, `secret`, or `.env` patterns are replaced with a known safe message;
- missing/blank messages fall back to the canonical safe message or “Working on your answer”;
- accepted messages have whitespace collapsed and are limited to 180 characters;
- invalid citation objects are discarded.

Sanitization protects the presentation boundary; it is not a substitute for avoiding secrets in backend event construction.

## `ActivityTimeline` behavior

`TypingIndicator` displays `ActivityTimeline` while `useAsk` is loading and at least one activity item exists. Before the first activity item, it displays a status-based fallback message.

The timeline:

- shows the latest activity message as the primary live status;
- pulses blue while active and uses red for a disconnected/error state;
- offers “View activity”/“Hide activity” when more than one event exists;
- lists events in arrival order with elapsed milliseconds when available;
- marks prior entries with a check and the current entry with a dot;
- uses `role="status"` and is contained by an `aria-live="polite"` typing indicator.

`ActivityTimeline` supports a `complete` prop that collapses details and marks entries complete, although the current `TypingIndicator` does not pass it; once loading ends, the typing indicator is removed and the completed assistant message is rendered.
