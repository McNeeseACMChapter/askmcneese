# RCCS Implementation Report

**Date:** 2026-07-12  
**Status:** Complete behind feature flags (default off)

---

## 1. Architecture Implemented

```
Question
  → conversational intent (existing)
  → persona (existing)
  → if RCCS_ENABLED:
        classify evidence needs (deterministic)
        → build RetrievalPlan
        → parallel selective channels:
             KB (Chroma) | official live (registry+DDG McNeese) | companions (adapters)
        → sanitize / dedupe / tier-rank
        → trust-separated context → Claude
        → citation validation
  → else: legacy exclusive KB XOR web fork
```

No agent framework. No open web. Companions activate only via registry + intent + flags.

---

## 2. Files Changed

| Path | Change | Why |
|------|--------|-----|
| `docs/rccs/RCCS_IMPLEMENTATION_AUDIT.md` | New audit | Mandatory pre-change record |
| `docs/rccs/RCCS_IMPLEMENTATION_REPORT.md` | This report | Final deliverable |
| `docs/architecture/SPRINT3_ARCHITECTURE_DECISIONS.txt` | D-05 addendum | Align decision log |
| `knowledge/source_registry_companions.csv` | New Tier C registry | Companion governance |
| `knowledge/source_registry_seed.csv` | Add SRC-034 faculty catalog | Official faculty identity |
| `backend/app/services/rccs/*` | New package | Classification, plan, allowlist, adapters, hybrid, citations |
| `backend/app/services/source_registry.py` | SRC-034 keywords | Faculty routing |
| `backend/app/services/web_search.py` | `is_mcneese_url` → allowlist | SSRF-safe official check |
| `backend/app/services/llm.py` | Trust rules + tiered context | Citation integrity / injection defense |
| `backend/app/routers/ask.py` | RCCS branches + additive fields | Selective hybrid orchestration |
| `backend/tests/unit/test_rccs_*.py` | New tests | Classification, allowlist, evidence, injection |

---

## 3. Registry Changes

### Official seed

- **SRC-034** Catalog Faculty List → `catalog.mcneese.edu` faculty roster (Tier A)

### Companions CSV fields

`source_id, name, description, content_type, source_tier, category, base_url, url_template, domain_allowlist, query_template, fetch_mode, trust_level, entity_types, topic_keywords, aliases, enabled, allowed_for_ai_retrieval, allow_chroma_ingest, citation_label, notes`

### Initial rows

| ID | Status | Notes |
|----|--------|-------|
| SRC-C-RMP-001 | enabled in CSV; runtime gated by `RCCS_RMP_ENABLED` | McNeese school 587 |
| SRC-C-SOCIAL-EXAMPLE | **disabled** | Schema fixture only — no fabricated URL |

---

## 4. Classification Rules

| Intent | KB | Official live | Companions |
|--------|----|---------------|------------|
| faculty_identity | yes | yes | **no** |
| faculty_ratings | yes | yes | student_rating |
| organization_identity | yes | yes | social (if enabled) |
| organization_activity | yes | yes (fresh) | social (if enabled) |
| social_profile | yes | yes | social link_only |
| admissions_policy | yes | if current | **no** |
| campus_services | yes | if hours/current | **no** |
| academic_programs | yes | no | **no** |
| athletics / events | yes | yes | **no** |

Entity extraction handles Dr/Prof titles, multi-word names, and org abbreviations generically.

---

## 5. Security Controls

- Fail-closed `is_allowed_url`
- Official domains for official channel only
- Tier C host only if enabled companion + plan category + domain allowlist match
- One companion does not unlock all external domains
- Reject file/data/javascript schemes, localhost, private IPs, cloud metadata
- URL normalize strips fragments/tracking
- Fetched text framed as untrusted evidence; injection fixtures tested
- No CAPTCHA/bot/stealth bypass

---

## 6. Hybrid Retrieval Behavior

- Selective: not every channel every time
- KB insufficient → official live fallback (not companions)
- User web mode → forces official live; companions still intent-gated
- Companion failure → continue with official/KB
- Bounded counts + timeouts via `RCCS_*` env vars

---

## 7. Citation Integrity

- Additive fields: `source_tier`, `trust_level`, `retrieval_channel`, `is_link_only`, `source_id`
- Legacy `id/title/url/snippet` preserved for SSE
- `validate_citations` drops blocked URLs; flags rating claims without rating evidence
- Trust-separated context sections for Claude

---

## 8. Tests Added

| File | Focus |
|------|--------|
| `test_rccs_classify.py` | Golden classification questions |
| `test_rccs_allowlist.py` | Authorization / SSRF |
| `test_rccs_evidence.py` | Merge, rank, citations, companion failure |
| `test_rccs_prompt_injection.py` | Injection framing |

---

## 9. Commands Run

```text
python -c "from app.routers import ask; ... flags_snapshot()"
→ import ok; RCCS_ENABLED False by default

python -m unittest discover -s tests/unit -v
→ Ran 50 tests in ~0.05s — OK

RCCS_ENABLED=0 → app start/import OK, rccs_enabled() False
RCCS_ENABLED=1 → flag module True after reload
```

No formatter/linter config found in backend beyond unittest; typing via existing style.

---

## 10. Feature Flags

| Flag | Default |
|------|---------|
| `RCCS_ENABLED` | `0` |
| `RCCS_HYBRID_ENABLED` | `1` |
| `RCCS_COMPANIONS_ENABLED` | `0` |
| `RCCS_RMP_ENABLED` | `0` |
| `RCCS_SOCIAL_LINKS_ENABLED` | `0` |
| `RCCS_MAX_KB_RESULTS` | `6` |
| `RCCS_MAX_OFFICIAL_RESULTS` | `5` |
| `RCCS_MAX_COMPANION_RESULTS` | `3` |
| `RCCS_MAX_TOTAL_EVIDENCE` | `10` |
| `RCCS_MAX_CHARS_PER_SOURCE` | `4000` |
| `RCCS_FETCH_TIMEOUT_SECONDS` | `15` |
| `RCCS_TOTAL_RETRIEVAL_TIMEOUT_SECONDS` | `25` |
| `RCCS_KB_MIN_RESULTS` | `1` |

---

## 11. Known Limitations

- Instagram/LinkedIn: **link_only**; no post content claims  
- RMP may be blocked/empty → graceful degradation  
- Undated pages are not treated as “recent”  
- Short/ambiguous entities may refuse RMP match (by design)  
- Hybrid live path still depends on DDG rate limits when official live runs  
- No claim-level citation mapping beyond URL evidence set validation  

---

## 12. Rollback

Set `RCCS_ENABLED=0` (default). Legacy `use_web_search` exclusive fork remains intact.

---

## 13. Related records

- D-05 addendum in `docs/architecture/SPRINT3_ARCHITECTURE_DECISIONS.txt`

---

## 14. Acceptance Checklist

- [x] Existing live McNeese web search still works (legacy path when RCCS off)
- [x] Existing KB retrieval still works
- [x] KB and official live can merge selectively (RCCS on)
- [x] Companion retrieval registry-constrained
- [x] External domains fail closed
- [x] RMP only for rating/student-opinion intent (+ flags)
- [x] Official faculty facts from official sources (SRC-034 / Tier A)
- [x] Organization routing general (not NSA-specific)
- [x] Social profiles link_only unless proven fetch
- [x] No Instagram post hallucination path
- [x] No companion Chroma ingest (`allow_chroma_ingest=false`)
- [x] Source tiers in evidence model
- [x] Trust-separated Claude context
- [x] Citation validation after generation
- [x] Frontend citation fields compatible (additive)
- [x] Prompt-injection fixtures neutralized as data
- [x] SSRF / unsafe URLs blocked
- [x] Feature flags support rollback
- [x] Deterministic tests cover golden questions
- [x] Decision log and public RCCS docs updated
- [x] Unit tests pass (50 OK); blockers: none for unittest
