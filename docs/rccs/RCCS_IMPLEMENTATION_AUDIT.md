# RCCS Implementation Audit

**Date:** 2026-07-12  
**Scope:** Registry-Constrained Hybrid Retrieval and Companion Search (RCCS)  
**Status:** Pre-modification audit — verified against repository before code changes

---

## 1. Current request flow (API → answer)

```
POST /ask (AskRequest)
  → ask() or ask_stream()                    [backend/app/routers/ask.py]
  → create_query_id()                        [query_logger.py]
  → classify_intent()                        [intent.py]  # greeting bypass
  → needs_clarification() / detect_persona() [persona.py]  # gate usually off
  → FORK on use_web_search:
       true  → search_and_fetch()            [web_search.py]
             → pages_to_context()
       false → search_chunks() / retrieve()  [retrieval.py]
  → generate_answer[_stream]()               [llm.py]
  → structure_answer()                       [structured_answer.py]
  → log_full_query()                         [query_logger.py]
  → AskResponse or SSE events
```

---

## 2. Exact files and functions

| Role | Path | Symbols |
|------|------|---------|
| App entry | `backend/app/main.py` | `app` |
| Orchestration | `backend/app/routers/ask.py` | `ask`, `ask_stream`, `AskRequest`, `AskResponse`, `ChunkResponse` |
| Conversational intent | `backend/app/services/intent.py` | `classify_intent`, `Intent`, `IntentResult` |
| Persona | `backend/app/services/persona.py` | `detect_persona`, `needs_clarification` |
| KB retrieval | `backend/app/services/retrieval.py` | `retrieve`, `search_chunks`, `RetrievedChunk` |
| Query expansion | `backend/app/services/query_expansion.py` | `expand_query` |
| Rerank | `backend/app/services/rerank.py` | `rerank_texts` |
| Official live web | `backend/app/services/web_search.py` | `search_and_fetch`, `search_duckduckgo`, `fetch_page_content`, `is_mcneese_url`, `MCNEESE_DOMAINS`, `FetchedPage` |
| Registry routing | `backend/app/services/source_registry.py` | `load_registry`, `match_sources`, `RegistrySource` |
| LLM | `backend/app/services/llm.py` | `generate_answer`, `generate_answer_stream`, `SYSTEM_PROMPT`, `_build_context` |
| Structure | `backend/app/services/structured_answer.py` | `structure_answer` |
| Activity SSE | `backend/app/services/activity_events.py` | `activity_payload` |
| Seed registry | `knowledge/source_registry_seed.csv` | SRC-001..033 |
| Merged registry | `knowledge/source_registry_merged.csv` | ingest only; backend does not read |

---

## 3. `use_web_search` behavior

- `AskRequest.use_web_search` defaults to `False`.
- Frontend maps `sourceScope === "web"` → `use_web_search: true`.
- When true: exclusive live path via `search_and_fetch` (no Chroma).
- When false: exclusive KB path via `search_chunks` (no live web).
- No hybrid merge exists.

---

## 4. ChromaDB retrieval behavior

- Read-only `retrieve()`: expand → multi-query → merge/dedup → rerank → top_k.
- Defaults: `RETRIEVAL_TOP_K=6`, `RETRIEVAL_PER_QUERY_K=12`.
- Empty/missing Chroma returns `[]` (no hard crash in search path when handled).

---

## 5. Source-registry matching

- Backend loads **seed only** (`source_registry_seed.csv`).
- Filters `Allowed for AI Retrieval` containing `"yes"`.
- Keyword score via `_TOPIC_KEYWORDS` + name/category tokens.
- Used only by live web `search_and_fetch`, not by KB path.
- No Tier C companions; no external domains.

---

## 6. URL allowlist

- Hardcoded `MCNEESE_DOMAINS` in `web_search.py`.
- `is_mcneese_url(url)` substring-matches netloc.
- DDG results post-filtered; non-McNeese dropped.
- No SSRF private-IP checks today.
- No companion-domain authorization.

---

## 7. Citation model

- Non-stream: `chunks: list[ChunkResponse]` (`chunk_id`, `text`, `source_url`, `title`, `category`, `score`).
- Stream: SSE `citations` event with `{id, title, url, snippet}`.
- No `source_tier` / `trust_level` today.
- No post-generation citation validation against evidence set.
- Frontend expects additive optional fields; required fields must remain.

---

## 8. Reranking

- Shared `rerank_texts()` used by KB and live web.
- Methods: cross-encoder / LLM / heuristic (env-gated).

---

## 9. Response schema

- Documented in `docs/RESPONSE_SCHEMA.md`.
- Additive structured fields via `structure_answer`.
- Must preserve `answer`, `chunks`, citation `id/title/url/snippet`.

---

## 10. Current tests

| File | Focus |
|------|--------|
| `backend/tests/unit/test_intent.py` | Conversational intent |
| `backend/tests/unit/test_persona.py` | Persona detection |
| `backend/tests/unit/test_structured_answer.py` | Structure lift |
| `backend/tests/unit/test_activity_events.py` | SSE activity allowlist |
| `backend/tests/unit/test_html_extraction.py` | HTML extract parity |
| `backend/tests/unit/test_query_logging.py` | Logging |
| `backend/tests/eval/run_eval.py` | Live eval harness |

No hybrid / companion / allowlist authorization tests exist.

---

## 11. Documentation conventions

- Keep implementation records under `docs/rccs/`.
- Keep architecture decisions under `docs/architecture/`.
- Do not commit local IDE config or internal PM notes.

---

## 12. Risks of changing each component

| Component | Risk | Mitigation |
|-----------|------|------------|
| `ask.py` fork | Break KB/web modes | Feature-flag RCCS; keep legacy branch |
| `web_search.py` allowlist | Break McNeese live search | Preserve McNeese defaults; fail-closed for externals |
| `source_registry.py` | Break routing | Additive companion loader; seed unchanged for official |
| `llm.py` prompt | Degrade answer quality | Surgical additive trust rules |
| Citations | Break frontend | Optional additive fields only |
| Parallel hybrid | Latency / flaky DDG | Timeouts + bounded counts + graceful degrade |

---

## 13. Planned modifications (mapped to files)

| Change | File(s) |
|--------|---------|
| Audit + report | `docs/rccs/*` |
| Feature flags | `backend/app/services/rccs/config.py` |
| Classification / plan / evidence | `backend/app/services/rccs/*.py` |
| Companion CSV | `knowledge/source_registry_companions.csv` |
| Official faculty seed row | `knowledge/source_registry_seed.csv` (SRC-034) |
| Allowlist | `rccs/allowlist.py` (+ web_search optional reuse) |
| Hybrid orchestration | `rccs/hybrid.py` |
| Citation validation | `rccs/citations.py` |
| Wire orchestration | `backend/app/routers/ask.py` |
| Trust-aware context | `backend/app/services/llm.py` |
| Tests | `backend/tests/unit/test_rccs_*.py` |
| D-05 append | `docs/architecture/SPRINT3_ARCHITECTURE_DECISIONS.txt` |

---

## 14. Rollback strategy

1. Set `RCCS_ENABLED=0` (default) → legacy exclusive KB/web fork.
2. Or set `RCCS_HYBRID_ENABLED=0` / `RCCS_COMPANIONS_ENABLED=0` for staged disable.
3. No Chroma schema migration; no seed deletion required.
4. Companion CSV can remain unused when flags off.

---

## 15. Acceptance criteria (pre-check)

See implementation command §38. All items start as pending and must pass before completion claim.

**Examples note:** NSA, Dr. Menon, and RMP are ruling examples only — classification and registry are domain-general.
