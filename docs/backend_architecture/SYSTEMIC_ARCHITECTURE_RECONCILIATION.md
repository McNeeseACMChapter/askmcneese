# AskMcNeese campus-intelligence architecture contract

Status: implementation baseline and controlling design contract  
Source blueprint: `output/pdf/AskMcNeese_Backend_System_Blueprint.pdf`  
Scope: the complete McNeese public-information ecosystem, not an employment-specific pipeline

## 1. Executive finding

AskMcNeese already has strong public-source safety controls, a large governed URL registry, useful catalog specialists, and an observable request lifecycle. Its central weakness is the missing layer between natural language and retrieval. Topic-like classifier labels currently drive broad channel flags, while evidence sufficiency is mostly generic. The result is predictable: a correctly governed URL can remain unindexed, a current question can be labeled stable, an irrelevant chunk can satisfy a generic threshold, and a failure can tell the user only that evidence was insufficient.

The corrective architecture is one reusable campus-intelligence stack:

1. Compile ordinary language into a universal `CampusQuery`.
2. Load a domain pack that declares supported operations and evidence needs.
3. Resolve an executable route policy by information characteristic.
4. Execute reusable retrieval primitives and optional structured adapters.
5. Evaluate domain-intent field coverage, trust, freshness, citations, and action links.
6. Render a validated answer shape or a precise failure.
7. Record the reason, timing, outcome, and rejection at every route boundary.

Employment and admissions are proof domains. They do not own separate answer pipelines.

## 2. Blueprint-to-repository reconciliation

| Blueprint claim | Repository/runtime evidence | Reconciled state | Architectural response |
|---|---|---|---|
| FastAPI `/ask` uses deterministic gates before RCCS hybrid retrieval | `backend/app/routers/ask.py`, live traces | Confirmed | Keep the API and shortcut boundary; replace narrow shortcut detection with compiler output. |
| The supervisor plan/execute/reflect path exists but is disabled | `services/orchestrator/*`; runtime capability snapshot | Confirmed inactive | Do not enable by default. First make route policy and evidence tests observable; canary later. |
| Registry size is much larger than indexed coverage | 4,733 merged rows; 4,700 runtime-eligible; 186 timestamps; 1,500 Chroma chunks | Confirmed | Add a source/index manifest. Never report a registered URL as indexed evidence. |
| Proof crawler and expansion backfill read different registries | `crawler/source_registry.py` reads seed; backfill reads merged | Confirmed | Introduce one governed registry reader and adapters for legacy callers. |
| Current heat map routes structured topics away from KB | `rccs/classify.py`, `plan.py`, `hybrid.py`, specialist overrides | Confirmed | Replace implicit flags with policy states and reasons; add structured indexes where appropriate. |
| URL safety and evidence sanitation are material strengths | `safe_url.py`, request guard, adapter checks, citation validation | Confirmed | Preserve fail-closed host, DNS, redirect, size, and trust checks. Domain packs cannot bypass them. |
| Evidence sufficiency can hide coverage scarcity | `rccs/evidence.py` boolean threshold and top-result fallback | Confirmed and reproduced | Return a requirement-aware result with missing fields, rejected evidence, routes attempted, and next permitted route. |
| Route observability exists but is coarse | `query_logger.py`, test recorder, `/ask/stats` | Partially confirmed | Add compiler decision, policy states, source groups, route skips/failures, rejection reasons, field coverage, renderer, and action validation. |
| Citation cap and validation exist | router/citation validation | Confirmed | Preserve URL validation; add claim/field support and action-link checks before rendering. |
| Capability handling exists | `capabilities.py` | Incomplete | Generate from enabled domain packs, active routes, specialists, authenticated boundaries, and limitations. |

## 3. Baseline failure traces

The machine-readable trace set is in `docs/backend_architecture/baseline_traces.json`.

Observed system-level patterns:

- Capability discovery has two inconsistent paths: an 18-second retrieval path for one phrasing and a 17-millisecond manual shortcut for another.
- The employment proof query is classified `general_campus/stable`; one Admissions chunk can survive ranking while actual employment routes are absent.
- A general admissions action can return useful content, but takes about 20 seconds and depends on free-form synthesis.
- Academic calendar and suspension-form queries return the same generic failure even though their missing requirements differ.
- Catalog retrieval can be rich yet slow (about 30 seconds in the baseline).
- A structured directory contact succeeds but takes about 14 seconds.
- A high-risk suspension-policy question retrieves the wrong evidence and infers a contact without direct policy support.

These traces are regression fixtures, not university facts.

## 4. Current route heat-map analysis

Notation: `CURRENT -> TARGET`. The target states are `FORBIDDEN`, `NOT_APPLICABLE`, `FALLBACK`, `CONDITIONAL`, `PRIMARY`, and `REQUIRED`.

### Academic calendar

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. The current specialist bypass prevents stale generic chunks, but also discards a low-latency term-aware cache. Build a term-keyed index; accept it only when term and source hash match. |
| Official web | `PRIMARY -> REQUIRED`. Current dates require direct official verification. If unavailable, return a precise stale/unavailable result rather than a date guess. |
| Specialist | `PRIMARY -> PRIMARY`. Structured event/date extraction is justified and should precede prose retrieval. |
| Companion | `OFF -> FORBIDDEN`. No companion source should establish the academic calendar. |
| Agentic web | `OFF -> FORBIDDEN`. Approved official schedule sources are the authority; broad web search adds ambiguity without authority. |

### Degree plan

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. Generic vectors are unsafe as the sole route, but a catalog-year structured index is valuable. Public degree rules must remain distinct from personal progress. |
| Official web | `PRIMARY -> REQUIRED`. Requirements must map to an official catalog/program version. |
| Specialist | `PRIMARY -> PRIMARY`. A program/curriculum structure preserves sequence, credits, concentration, and catalog year. |
| Companion | `OFF -> FORBIDDEN`. Third-party degree plans cannot establish completion requirements. |
| Agentic web | `OFF -> FORBIDDEN`. Official catalog evidence should be sufficient; no broad synthesis for degree completion. |

### Course catalog

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. Replace generic chunks with catalog-year course records; use as fast path only when versioned. |
| Official web | `PRIMARY -> REQUIRED`. Course changes and prerequisites require the requested/current catalog source. |
| Specialist | `PRIMARY -> PRIMARY`. Course codes, credits, prerequisites, and descriptions have stable structure. |
| Companion | `OFF -> FORBIDDEN`. Companions cannot define official courses. |
| Agentic web | `OFF -> FORBIDDEN`. Official catalog search is sufficient and more precise. |

### Policy / suspension

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. Versioned policy sections can accelerate retrieval but must not be the only support for high-risk claims. |
| Official web | `PRIMARY -> REQUIRED`. Material policy claims require direct official text and owner/version information where available. |
| Specialist | `CONDITIONAL -> PRIMARY when available`. A policy adapter adds value only if it preserves sections, owner, effective metadata, and related forms; otherwise direct official evidence remains primary. |
| Companion | `OFF -> FORBIDDEN`. Companion content cannot establish university policy. |
| Agentic web | `OFF -> FORBIDDEN`. High-risk procedures remain inside official evidence. |

### Form lookup

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. A form index should store identity and ownership, but cached links must be revalidated. |
| Official web | `PRIMARY -> REQUIRED`. The owning page and final URL/content type must be checked. |
| Specialist | `PRIMARY -> PRIMARY`. Forms are structured action records and benefit from deterministic matching. |
| Companion | `OFF -> CONDITIONAL`. Only an explicitly affiliated action portal linked by the official owner is acceptable. |
| Agentic web | `OFF -> FORBIDDEN`. Broad web synthesis is inappropriate for actionable links. |

### Career / Handshake

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. Cached categories and portal identities are useful, but openings and availability are live. |
| Official web | `PRIMARY -> REQUIRED`. The official career/employment owner must establish affiliation and current guidance. |
| Specialist | `PRIMARY -> PRIMARY where records exist`. Employment records, job categories, verification timestamps, and application links have useful structure; the adapter uses the same shared interface as calendar/forms/directory. |
| Companion | `OFF -> CONDITIONAL`. Handshake and approved hiring portals are valid only through explicit governance and ownership links. |
| Agentic web | `OFF -> CONDITIONAL`. It is a final governed-search fallback only when explicit provider policy allows it and evidence remains insufficient. |

### Faculty identity

| Channel | Analysis |
|---|---|
| Indexed KB | `PRIMARY -> FALLBACK`. An index is fast, but roles and contacts change. |
| Official web | `PRIMARY -> REQUIRED`. Current identity, role, department, and contact require official verification. |
| Specialist | `PRIMARY -> PRIMARY`. Directory records are structured and avoid free-form extraction. |
| Companion | `OFF -> FORBIDDEN`. Ratings/social context cannot establish official identity. |
| Agentic web | `OFF -> FORBIDDEN`. Official directory/department sources are authoritative. |

### Faculty ratings

| Channel | Analysis |
|---|---|
| Indexed KB | `PRIMARY -> FALLBACK`. KB may establish official identity but never rating claims. |
| Official web | `PRIMARY -> REQUIRED for identity only`. The official channel verifies the person and institution; it is not a rating source. |
| Specialist | `CONDITIONAL -> PRIMARY for entity resolution`. The directory specialist resolves the exact person before companion lookup. |
| Companion | `PRIMARY -> PRIMARY`. Approved rating platforms provide labeled student-opinion context with exact-host and exact-entity matching. |
| Agentic web | `OFF -> FORBIDDEN`. Broad web results would weaken entity and trust controls. |

### Organization

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. A registered-organization snapshot is useful if freshness is visible. |
| Official web | `OFF -> REQUIRED for ownership/status when available`. The engagement owner should validate recognized status; lack of an official listing must be disclosed. |
| Specialist | `CONDITIONAL -> PRIMARY`. Presence-style organization records have stable fields and benefit from deterministic extraction. |
| Companion | `PRIMARY -> PRIMARY`. Approved organization platforms can supply live profiles/activity under explicit governance. |
| Agentic web | `OFF -> CONDITIONAL`. Only for explicit web mode after recognized sources fail; social discovery remains exact-host constrained. |

### Social profile

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> NOT_APPLICABLE`. General campus chunks are not the source of truth for social identities. |
| Official web | `OFF -> CONDITIONAL`. Use only to establish an official outbound affiliation link. |
| Specialist | `OFF -> PRIMARY`. An exact-host link registry is a small structured specialist, not an isolated domain workflow. |
| Companion | `PRIMARY -> PRIMARY`. Only pre-approved hosts and resolved entity matches are admitted and labeled. |
| Agentic web | `OFF -> FORBIDDEN`. Unrestricted social discovery creates impersonation and entity-collision risk. |

### Athletics / current

| Channel | Analysis |
|---|---|
| Indexed KB | `OFF -> FALLBACK`. Cached schedules/results are useful only inside a short freshness policy. |
| Official web | `PRIMARY -> REQUIRED`. Current schedules and results require the official athletics owner. |
| Specialist | `CONDITIONAL -> PRIMARY`. Schedule/result records have stable structure and should be normalized when available. |
| Companion | `OFF -> PRIMARY`. `mcneesesports.com` is an approved affiliated owner and should be modeled explicitly, not hidden inside generic official web. |
| Agentic web | `OFF -> CONDITIONAL`. Only after the approved athletics source fails and explicit provider policy allows a fallback. |

### General campus

| Channel | Analysis |
|---|---|
| Indexed KB | `PRIMARY -> PRIMARY`. This remains the low-latency path for stable, well-covered facts. |
| Official web | `PRIMARY -> CONDITIONAL`. Running both primaries creates unnecessary fanout. Fetch live only for weak, stale, action-oriented, or current evidence. |
| Specialist | `OFF -> CONDITIONAL`. Use a specialist only when the compiler discovers a structured subdomain. |
| Companion | `OFF -> CONDITIONAL`. Only a domain pack with an approved companion may enable it. |
| Agentic web | `OFF -> CONDITIONAL`. Explicit web mode plus insufficient governed evidence; never a default substitute for coverage. |

### Why multiple PRIMARY routes currently hurt

Faculty and general-campus queries can activate multiple primary routes without an explicit precedence contract. This increases fanout, duplicate evidence, ranking ambiguity, citation clutter, provider cost, and tail latency. The executable policy now declares precedence and bounded concurrency. `REQUIRED` means a route must succeed for an unqualified final claim; `PRIMARY` means preferred acquisition; `FALLBACK` means run only after a documented insufficiency; `CONDITIONAL` includes its condition; `FORBIDDEN` is a safety or authority boundary; `NOT_APPLICABLE` means the route has no semantic role.

## 5. System taxonomies and schemas

The contracts are machine-readable:

- Domain taxonomy: `knowledge/campus_intelligence/domain_taxonomy.json`
- Intent taxonomy: `knowledge/campus_intelligence/intent_taxonomy.json`
- Audience, freshness, and risk: `knowledge/campus_intelligence/operational_taxonomies.json`
- Universal query schema: `knowledge/campus_intelligence/campus_query.schema.json`
- Domain-pack schema and instances: `knowledge/campus_intelligence/domain_pack.schema.json`, `domain_packs.json`
- Source-group schema and instances: `knowledge/campus_intelligence/source_group.schema.json`, `source_groups.json`
- Route-policy schema and executable policies: `knowledge/campus_intelligence/route_policy.schema.json`, `route_policies.json`
- Evidence requirement schema: `knowledge/campus_intelligence/evidence_requirement.schema.json`
- Answer-shape registry: `knowledge/campus_intelligence/answer_shapes.json`
- Failure taxonomy: `knowledge/campus_intelligence/failure_taxonomy.json`
- Evaluation coverage matrix: `docs/backend_architecture/evaluation_coverage.csv`

The taxonomy includes all requested categories and adds research/grants, alumni/giving, bookstore, and compliance/Title IX because they appear in the actual governed registry.

## 6. Universal query plan

Every request compiles to the same representation:

```json
{
  "original_query": "Where is the academic suspension appeal form?",
  "normalized_query": "where is the academic suspension appeal form?",
  "domain": "forms",
  "subdomain": "suspension_appeal",
  "intent": "find_form",
  "action": "download",
  "entities": {"form": "academic suspension appeal", "policy": "academic suspension"},
  "audience": "unknown",
  "freshness": "live",
  "risk": "high",
  "answer_shape": "form_result",
  "required_source_groups": ["official_forms", "academic_standing"],
  "required_fields": ["form", "active_url", "owner", "content_type", "last_verified"],
  "confidence": 0.93,
  "ambiguities": [],
  "clarification_required": false
}
```

The compiler is deterministic for high-confidence phrases, misspellings, intent verbs, term/year entities, explicit audiences, and capability discovery. Semantic fallback is reserved for close or ambiguous matches and cannot override policy safety boundaries.

## 7. Shared retrieval and specialist contract

Retrieval primitives are reusable: indexed search, configured-source fetch, official-domain search, approved companion lookup, action-link validation, and authenticated-boundary response. A specialist exists only when stable structure improves accuracy or latency.

All specialists return the same envelope:

```json
{
  "records": [],
  "evidence": [],
  "source_attempts": [],
  "field_coverage": {},
  "freshness": {},
  "failures": [],
  "latency_ms": 0
}
```

Calendar, catalog/program, forms, directory, policy, employment, events, organizations, locations, and tuition are candidates. They plug into shared sufficiency and rendering and cannot bypass citation, trust, URL, or action-link validation.

## 8. Evidence and failure contract

Sufficiency is a structured result, not a boolean. It includes accepted and rejected evidence, reasons, field coverage, trust/freshness checks, action-link status, required source-group coverage, attempted routes, and the next permitted route. A partial response is allowed only when the domain pack declares the missing fields non-material or explicitly permits a verified portal/contact fallback.

The universal failure taxonomy is stored in `failure_taxonomy.json`. User messages remain safe, while internal telemetry records one or more diagnostic codes. Personal queries are never answered from public evidence.

## 9. Evaluation model

The matrix covers domain x intent x audience x freshness x answer shape x risk x route x source group. Tests score the compiled operation and evidence behavior, not text similarity alone:

- domain, subdomain, intent, audience, freshness, and risk accuracy;
- resolved route states, precedence, and avoided provider/LLM calls;
- source-group selection and registered-versus-indexed distinction;
- evidence relevance, required-field coverage, and rejection reasons;
- citation support and action-link validity;
- precise partial/failure behavior;
- latency by compiler, route, retrieval, validation, and rendering;
- unchanged SSRF, trust, size, redirect, and private-data protections.

## 10. Dependency-based implementation plan

1. Freeze baseline traces and schemas.
2. Implement configuration loaders with validation and last-known-good behavior.
3. Implement the universal compiler and policy resolver; expose trace output without changing retrieval.
4. Generate capability discovery from live configuration and eliminate unnecessary retrieval/LLM work.
5. Introduce shared route telemetry and requirement-aware evidence evaluation behind an environment flag.
6. Migrate admissions, employment, calendar, catalog, forms, directory, and policy as proof domains using existing adapters where safe.
7. Introduce shared answer renderers and precise failure rendering; keep evidence-supported LLM synthesis only where needed.
8. Unify registry reading and add source/index/freshness manifests before any broad backfill.
9. Expand domain packs and structured indexes based on measured coverage gaps.
10. Replay the coverage suites, compare route/evidence/latency traces, and retain rollback flags until parity and security gates pass.

No university dates, deadlines, fees, positions, policies, or delivery timelines belong in code or configuration. Configuration contains routing semantics and source ownership only; facts remain evidence.

## 11. Migration and rollback boundary

The new layer is additive and versioned. Existing request and response contracts remain stable. Compiler metadata and resolved policies are attached to RCCS plans, then representative domains migrate behind `CAMPUS_INTELLIGENCE_ENABLED`. The legacy classifier and hybrid path remain a rollback route during validation. Disabling the flag restores legacy behavior without deleting the registries, source manifests, or test corpus.
## 12. Implemented state and acceptance evidence

The architecture above is now executable rather than aspirational:

- `campus_intelligence/compiler.py` compiles every query to the shared operation contract.
- `route_policy.py` resolves every channel to FORBIDDEN, NOT_APPLICABLE, FALLBACK, CONDITIONAL, PRIMARY, or REQUIRED with a reason and condition.
- `specialists.py` supplies governed destination/action records without converting registered URLs into factual claims.
- `evidence.py` rejects topical drift, scores required-field/source-group coverage, and preserves typed failure codes.
- RCCS executes the shared specialist, KB, governed official fetch, companion, and optional agentic channels under one trace.
- Query logs now preserve the compiled query, resolved policy, per-route attempt, rejected evidence, and sufficiency result.
- The crawler, backfill, and runtime use one merged governed registry and one source/index manifest.

Acceptance results on 2026-08-03:

- 174 backend unit tests passed, including legacy routing/security tests and new compiler, specialist, manifest, provenance, persona, and evidence tests.
- Capability discovery moved from a baseline 18,382 ms retrieval/generation path to a deterministic 209 ms live response in the acceptance run.
- Employment no longer accepts unrelated admissions evidence. A warm acceptance run completed internally in 10,240 ms (5,808 ms retrieval plus 4,432 ms synthesis) and returned exact governed HR/student-employment destinations while explicitly stating that vacancy records were not available.
- An international-undergraduate application question is no longer misclassified as graduate; the substring bug was fixed with boundary-aware persona matching and a regression test.
- Calendar/date requests still fail closed when the required date and verification evidence are unavailable. The source registry link alone cannot satisfy a date claim.
- The full source manifest currently reports 4,698 registered sources, 188 indexed sources, and 1,500 chunks. This is measured coverage, not a claim of ecosystem completeness.

The most important remaining limitation is data coverage, not routing architecture. Calendar, policy, employment-portal, forms, career-center, events, organization, and technology groups contain registered sources with uneven or zero indexed coverage. Those gaps must be closed through governed crawl/backfill and freshness validation; they must not be hidden by broad provider search or LLM synthesis.

