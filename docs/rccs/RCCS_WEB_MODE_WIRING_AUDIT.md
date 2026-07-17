# RCCS Web Mode Wiring Audit

**Date:** 2026-07-12  
**Status:** Diagnosed before repair; repairs follow in same task

| Stage | File | Function / component | Input | Output | Expected mode value | Actual behavior (pre-repair) | Pass/Fail |
|-------|------|----------------------|-------|--------|---------------------|------------------------------|-----------|
| UI mode control | `frontend/src/components/chat/ChatInput.tsx` | `<select>` Sources | user click | `onSourceScopeChange("knowledge"\|"web")` | `"web"` when Web selected | Controlled select; updates parent state | **Pass** |
| React state | `frontend/src/App.tsx` | `useState<SourceScope>("knowledge")` | scope change | `sourceScope` | `"knowledge"` / `"web"` | Single source of truth in AppRoutes | **Pass** |
| Submit handler | `frontend/src/App.tsx` | `send()` → `ask(text, sourceScope, …)` | question + scope | calls useAsk | current `sourceScope` | Passes live `sourceScope` (in deps) | **Pass** |
| API client | `frontend/src/hooks/useAsk.ts` | `askWithStream` | `sourceScope` | JSON body | `use_web_search: sourceScope==="web"` | Serializes correctly | **Pass** |
| HTTP request body | network | POST `/ask` | JSON | SSE stream | `use_web_search` bool | Contract correct when UI used | **Pass** |
| Backend request schema | `backend/app/routers/ask.py` | `AskRequest.use_web_search` | body | bool default False | true for web | Declared; not discarded | **Pass** |
| ask.py routing (legacy) | `ask.py` | `if body.use_web_search` | bool | `search_and_fetch` / KB | web → live | Works when RCCS off | **Pass** |
| ask.py routing (RCCS) | `ask.py` + `rccs/hybrid.py` | `run_rccs_retrieval` | `use_web_search` | hybrid plan | web forces official_live | Forces live when true; smoke showed `category=official_live` | **Pass** |
| RCCS classifier | `rccs/classify.py` | `with_user_web_preference` | bool | use_official_live | cannot cancel web | Does not cancel explicit web | **Pass** |
| Official web retrieval | `web_search.py` / `hybrid._retrieve_official` | DDG + fetch | query | pages | executed on web | Smoke: 10 chunks, official_live | **Pass** |
| Claude context | `llm.py` | `generate_answer` | chunks | answer | capability-aware | **No retrieval-status metadata**; capability Q answered from empty campus evidence | **Fail** |
| Capability meta-Q | `intent.py` / ask | “Can you do web search?” | text | truthful capability | runtime-grounded yes | Treated as campus RAG Q → “nothing in sources” / soft denial | **Fail** |
| Citation response | ask SSE / AskResponse | citations / chunks | evidence | URLs | real URLs | Works for web smoke | **Pass** |
| Frontend source rendering | SemanticAnswer / citations | citations | URLs | UI | show sources | Existing path OK when citations arrive | **Pass** |
| Activity narration | `activity.ts` / TypingIndicator | status copy | mode | “Searching…” | web-specific | Always generic “official McNeese sources”; not mode-aware | **Fail** (UX) |
| Runtime config | env / `rccs/config.py` | `RCCS_ENABLED` | env | flags | documented local=1 | Flags only in shell env; not in `.env`; module constants freeze at import | **Fail** |
| Capabilities contract | `/health` / `/ask/stats` | capabilities | — | booleans | expose web availability | Partial `rccs` on stats only; FE unused; health has none | **Fail** |
| Response metadata | AskResponse | requested/effective mode | — | additive fields | truthful | Only partial `retrieval_mode`; missing `web_search_executed` / status | **Fail** |

## Root causes (pre-repair)

1. **Capability answers are not runtime-grounded** — meta-questions hit RAG+Claude without a capability reply or retrieval-status block, so Claude reports it cannot confirm web search.
2. **Local RCCS flags were not persisted** in `.env` / `.env.example`; availability depended on accidental shell env.
3. **Frontend has no capabilities contract** — Web toggle always enabled with no backend truth.
4. **Status copy / response metadata incomplete** for distinguishing Knowledge vs Web.

## Note

Frontend → `use_web_search` → backend web retrieval **already works** when the flag is true (API smoke proved `official_live` citations). The product failure is capability UX + config + metadata, not a dead toggle serializer.
