# Agentic Search Workflow for the McNeese Full-Spectrum Backend

Research date: 2026-08-03

## 1. Operating principle

The backend is not a free-form chatbot that treats every fetched page as equally trustworthy. It is a governed retrieval system. Each user request is mapped to a category, subcategory, intent, answer schema, source policy, freshness requirement, and risk tier before the system searches.

Official McNeese sources are first for institution-specific facts. Government, accreditor, governing-body, and official partner sources are used when they own the rule or data. Commercial marketplaces and social/professional platforms are discovery sources only unless an approved API or license provides stronger access.

## 2. Request lifecycle

1. **Input firewall**
   - Normalize Unicode, trim invisible characters, cap length, and reject control sequences.
   - Detect prompt-injection language, credential requests, illegal data requests, and URLs targeting local/private networks.
   - Separate the user query from system instructions and retrieved content.

2. **Intent and entity classification**
   - Predict `category_id`, `subcategory_id`, and one or more intents.
   - Extract student type, academic term, course code, degree, office, location, deadline, price, employer, and urgency.
   - Resolve “MSU,” “McNeese,” department nicknames, and office aliases against `taxonomy.csv`.
   - Output calibrated confidence. Low confidence goes to a multi-category planner, not directly to answer generation.

3. **Risk gate**
   - High-risk domains include immigration, financial aid eligibility, health, Title IX, safety, academic appeals, FERPA, and legal/policy interpretation.
   - High-risk requests require official sources, direct evidence, conservative wording, and an authorized contact or escalation route.
   - Do not automate consequential decisions or submit forms without explicit user action and a separate authenticated workflow.

4. **Query planner**
   - Retrieve 3–8 rows from `search_queries_50000.csv` that match the category, intent, audience, and term.
   - Issue a precision query, an official-domain query, and—only when appropriate—an external discovery query.
   - Rewrite relative dates into absolute dates before search.
   - Budget searches by expected value; do not fan out indiscriminately.

5. **Source router**
   - Read `source_registry.csv` and rank sources by authority tier, category match, access permission, freshness, and whether authentication is required.
   - Tier 1: McNeese, government, accreditor, regulator, governing body.
   - Tier 2: official partner, affiliate, structured professional source.
   - Tier 3: commercial discovery source, marketplace, social/professional platform.
   - Never turn a registered URL into a factual claim. Registration is routing metadata, not evidence.

6. **Acquisition**
   - Prefer APIs, feeds, sitemaps, structured data, and public HTML.
   - Obey robots.txt, platform terms, API licenses, rate limits, and authentication boundaries.
   - Use conditional requests (`ETag`, `If-Modified-Since`) and domain-specific concurrency limits.
   - Resolve DNS and re-check the destination after every redirect to prevent SSRF.
   - Cap response size, MIME types, redirects, and execution time.

7. **Content isolation and extraction**
   - Treat retrieved content as untrusted data, never as instructions.
   - Strip scripts, forms, hidden text, executable attachments, and navigation noise.
   - Parse PDFs/documents in a sandbox. Preserve page numbers and evidence spans.
   - Extract into the row’s `answer_schema`, retaining canonical URL, title, publisher, publication/update date, retrieval time, and content hash.

8. **Entity resolution and temporal reasoning**
   - Link office aliases to a canonical McNeese entity while preserving the source wording.
   - Label catalog year, academic term, fiscal year, application cycle, event date, and effective date explicitly.
   - Do not mix archived and current policies. If sources conflict, prefer the owning authority and newest effective version.

9. **Evidence scoring**

Suggested score (0–100):

```
score = 0.34*authority + 0.20*directness + 0.18*freshness
      + 0.12*category_match + 0.08*field_completeness
      + 0.05*cross_source_agreement + 0.03*accessibility
      - stale_penalty - conflict_penalty - snippet_only_penalty
```

Hard rules:
- A search snippet cannot be final evidence when the destination page is accessible.
- A commercial listing cannot override an official employer, university, regulator, or property source.
- A cached result outside its freshness window must be revalidated before answering.
- A source containing prompt injection is quarantined; its factual content may be re-fetched by a non-agentic parser if safe.

10. **Verification agent**
    - Re-fetch volatile facts: emergency status hourly, events/jobs/menus/schedules daily, deadlines and costs weekly, stable history monthly or quarterly.
    - Check that the page still exists, the stated date applies to the requested term, and the application/status link is canonical.
    - For jobs, verify `open/closed`, employer, job ID, location, posting date, closing date, and application URL.

11. **Answer synthesis**
    - Fill only fields supported by evidence.
    - Cite every consequential fact and state `last_verified`.
    - Separate **Official McNeese information** from **External options**.
    - State conflicts, missing fields, and uncertainty instead of filling gaps with an LLM guess.
    - Provide the responsible office/contact for high-risk or account-specific matters.

12. **Post-answer logging and evaluation**
    - Log category, intent, selected query IDs, source IDs, latency, cache status, evidence score, missing fields, and user feedback.
    - Do not log full personal queries when they contain sensitive data; store a redacted event instead.
    - Feed zero-result queries, corrections, and unsupported answer fields into a review queue.

## 3. Recommended services

- `taxonomy-service`: categories, aliases, answer schemas, versioning.
- `intent-router`: deterministic rules + classifier with confidence calibration.
- `query-planner`: retrieves and adapts search phrases without changing the user’s meaning.
- `source-registry`: domains, permissions, tiers, freshness, credentials metadata.
- `fetch-gateway`: outbound network policy, robots/terms checks, rate limits, caching, SSRF controls.
- `extractor-workers`: HTML, JSON, XML, PDF, calendar, structured data parsers in sandboxes.
- `evidence-store`: immutable source snapshots, hashes, evidence spans, timestamps, retention rules.
- `ranker-verifier`: source scoring, conflict detection, field-level verification.
- `answer-composer`: schema-bound generation with citations and refusal/escalation policies.
- `evaluation-service`: golden questions, freshness tests, citation correctness, and regression tests.

## 4. Predefined answer schemas

Use typed schemas rather than a single universal response:

- **Contact**: office, person/role, phone, email, building, room, hours, URL, verified time.
- **Deadline**: requirement/event, exact date, time, time zone, term, status, URL, verified time.
- **Cost**: item, amount, currency, term, residency/student type, included/excluded fees, URL.
- **Job**: title, employer, location, type, compensation if published, posting ID, dates, status, apply URL.
- **Course**: subject/number, title, credits, prerequisite, section, modality, meeting time, instructor, seats/status.
- **Policy**: title, rule, scope, effective/version date, exceptions, owner, canonical URL.
- **Service**: eligibility, services, access steps, cost, hours, contact, urgent alternative.
- **Event**: title, organizer, start/end, time zone, venue, price, registration, status.

## 5. Search-provider strategy

Use a pluggable provider interface. A provider returns normalized search results; it does not decide truth. Support official site search, a licensed general web-search API, government APIs, and partner feeds. Avoid brittle HTML scraping of platforms whose terms prohibit automation. Indeed and LinkedIn should be user-link/authorized-access discovery channels, not unrestricted crawler targets.

## 6. Caching and freshness

- Cache key: normalized query + provider + locale + source policy version.
- Evidence key: canonical URL + content hash.
- Use stale-while-revalidate only for low-risk content.
- Emergency/status answers must fail closed: when verification fails, say status cannot be confirmed and provide the official status/contact route.
- Keep archived versions for policy/catalog auditability, with explicit version labels.

## 7. Evaluation suite

Maintain at least 20 human-reviewed questions per category. Measure classification accuracy, authoritative-source precision, field completeness, citation support, stale-answer rate, conflict handling, zero-result rate, latency, and unsafe-tool-call rate. Red-team prompt injection, SSRF, malicious PDFs, credential leakage, and poisoned external listings.
