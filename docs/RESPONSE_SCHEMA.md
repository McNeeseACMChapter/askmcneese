# AskMcNeese Response Schema

**Current implementation:** `backend/app/routers/ask.py`, `backend/app/services/structured_answer.py`, and `frontend/src/lib/answerModel.ts`

## HTTP `AskResponse`

`POST /ask` with `stream: false` returns the Pydantic `AskResponse` below.

### Legacy fields

| Field | Type | Purpose |
|---|---|---|
| `question` | `string` | Original question. |
| `answer` | `string` | Complete answer markdown; retained as the compatibility source of truth. |
| `chunks` | `ChunkResponse[]` | Retrieved source chunks. |
| `num_results` | `integer` | Number of source results used/found. |
| `query_id` | `string` | Server-generated request identifier. |
| `model` | `string \| null` | Generation/fallback mode or model. |
| `tokens_used` | `integer \| null` | Token count when available. |
| `retrieval_ms` | `integer` | Retrieval duration. |
| `generation_ms` | `integer \| null` | Generation duration when generation ran. |
| `total_ms` | `integer` | End-to-end duration. |

Each `ChunkResponse` contains `chunk_id`, `text`, `source_url`, `title`, `category`, and `score`.

### Additive structured fields

All structured fields are optional/nullable so older consumers can ignore them and incomplete structure can be represented honestly.

| Field | Type | Purpose |
|---|---|---|
| `answer_type` | `string \| null` | Presentation category such as `factual`, `deadline`, `process`, `comparison`, `location`, `no_source`, `partial`, `backend_failure`, `clarification`, or `conversational`. |
| `title` | `string \| null` | Heading lifted from the answer when present. |
| `summary` | `string \| null` | First prose summary lifted from the answer. |
| `content_markdown` | `string \| null` | Full markdown body; currently mirrors `answer`. |
| `key_facts` | `{label, value}[] \| null` | Labeled facts recognized in existing answer text. |
| `important_dates` | `{label, value}[] \| null` | Date-related labeled facts. |
| `requirements` | `string[] \| null` | Requirement statements extracted from existing content. |
| `steps` | `string[] \| null` | Existing ordered-list steps. |
| `warnings` | `string[] \| null` | Existing `Note:`, `Important:`, `Warning:`, or `Tip:` lines. |
| `related_questions` | `string[] \| null` | Reserved additive field; the current service returns `null`. |
| `confidence` | `string \| null` | Current values are `high`, `medium`, or `low`, inferred from source count unless supplied. |

The backend HTTP model does not define a top-level `sources` field. Non-streaming citations are represented by `chunks`. In SSE, citations arrive in a separate `citations` event. The frontend’s broader TypeScript `AskResponse` accepts optional `sources` because it normalizes both transport forms.

## Streaming equivalent

For `stream: true`, answer text arrives through one or more `chunk` events and citations arrive through `citations`. The final `done` event contains `query_id`, result/timing metadata, `mode`, and the additive structured fields. It does not repeat legacy `chunks`; the frontend assembles a normalization input from the stream.

## `structure_answer` service

`backend/app/services/structured_answer.py` is a best-effort adapter between the legacy markdown answer and the additive schema. It:

- infers an answer type from the model, source count, question, and existing answer text;
- lifts the first markdown/bold heading and first prose paragraph;
- recognizes labeled bullet facts, date/requirement facts, ordered steps, and explicit warning prefixes;
- sets `content_markdown` to the original answer;
- estimates confidence from source count when confidence is not supplied.

It does not call a model, retrieve data, replace `answer`, or create new McNeese facts. Extraction can be incomplete; nullable/empty structured fields are expected.

## Frontend normalization

`normalizeAskResponse` in `frontend/src/lib/answerModel.ts` converts the transport shape to the camelCase `StructuredAnswer` used by `SemanticAnswer`.

Normalization rules:

1. Content preference is `content_markdown`, then legacy `answer`, then legacy frontend-compatible `text`, then an empty string.
2. A recognized `answer_type` is used; otherwise empty content becomes `backend_failure`, zero results become `no_source`, and other responses become `factual`.
3. Missing structured arrays become empty arrays.
4. `sources` are preferred when supplied by the SSE adapter; otherwise citations are derived from legacy `chunks`.
5. Nullable `title` and `summary` become optional frontend values.

`normalizeChatMessage` separately protects locally persisted/older conversations: if a message has no `structured` object, its original `text` and `citations` are wrapped in a valid `StructuredAnswer`.

## Compatibility and migration plan

1. **Current phase — additive dual shape:** Producers keep returning `answer` and all legacy metadata while also returning structured fields. Consumers must tolerate missing/null structured values.
2. **Consumer migration:** New UI code reads only through `normalizeAskResponse`/`normalizeChatMessage`. Other clients may continue reading `answer` and `chunks`.
3. **Producer improvement:** Structured fields may later be generated more directly, but `content_markdown` and `answer` must remain semantically equivalent during the compatibility window.
4. **Contract verification:** Test both a legacy-only fixture and a structured fixture before changing requiredness or field names.
5. **Future deprecation, if approved:** Deprecate legacy fields only in a versioned API with measured consumer adoption. No legacy field is deprecated by the current overhaul.

This plan lets backend and frontend deploy independently without requiring a flag day.
