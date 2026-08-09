# McNeese Full-Spectrum Search Intelligence Pack

**Beta status:** routing and evaluation intelligence only. These artifacts expand coverage planning but do not grant crawl permission, establish official truth, or replace live freshness checks.

This directory contains the actual files requested for an agentic McNeese search backend.

## Included files

- `search_queries_50000.csv` — exactly 50,000 unique search phrases with category, subcategory, intent, audience, source mode, answer schema, freshness, priority, and security metadata.
- `search_queries_50000.jsonl` — the same records, one JSON object per line.
- `taxonomy.csv` — 124 top-level categories and 992 category/subcategory rows. McNeese A–Z offices and departments are preserved rather than collapsed into a small taxonomy.
- `source_registry.csv` — 70 official, government, partner, governing, and external discovery sources with authority tiers and access restrictions.
- `agentic_workflow.md` — end-to-end routing, collection, extraction, verification, ranking, synthesis, caching, and evaluation design.
- `security_controls.md` — prompt injection, SSRF, secrets, FERPA, privacy, high-risk-domain, crawler, document-parser, and action safety controls.
- `quality_summary.json` — validation results and distributions.
- `search_queries_preview.csv` — a smaller representative preview.

## Research grounding

The taxonomy is grounded in McNeese’s public A–Z directory and main navigation, including admissions, academics, student services, colleges, departments, Student Central, catalog, class search, housing, dining, health, counseling, safety, athletics, research, employment, community programs, media, advancement, and compliance.

Core seed pages:
- https://www.mcneese.edu/a-to-z/
- https://www.mcneese.edu/
- https://www.mcneese.edu/admissions/
- https://www.mcneese.edu/admissions/international/
- https://www.mcneese.edu/admissions/estimated-costs/
- https://www.mcneese.edu/studentservices/
- https://www.mcneese.edu/studentservices/resources/
- https://catalog.mcneese.edu/
- https://schedule.mcneese.edu/

## What “researched queries” means

The phrases are research-grounded synthetic queries: they are generated from verified public entities, service areas, common university user intents, typed answer requirements, audience/term variations, and source policies. They are **not** claimed to be direct exports of private search logs or licensed keyword-volume databases.

## Recommended use

1. Load `taxonomy.csv` into the intent/entity router.
2. Load `search_queries_50000.csv` into a lexical/vector retrieval index.
3. Select query rows by category + intent + audience + term, not by nearest embedding alone.
4. Route providers through `source_registry.csv`.
5. Bind answer generation to `answer_schema` and `freshness_class`.
6. Retain source evidence and citations for every returned field.
7. Re-rank and prune the corpus using real McNeese site-search logs, Search Console, help-desk tickets, and human review.

## Minimal database shape

```sql
CREATE TABLE search_queries (
  query_id TEXT PRIMARY KEY,
  query TEXT NOT NULL,
  category_id TEXT NOT NULL,
  subcategory_id TEXT NOT NULL,
  intent TEXT NOT NULL,
  user_segment TEXT,
  source_mode TEXT NOT NULL,
  preferred_domains TEXT NOT NULL,
  answer_schema TEXT NOT NULL,
  freshness_class TEXT NOT NULL,
  priority_score INTEGER NOT NULL,
  risk_level TEXT NOT NULL
);
```

## Limitations requiring human review

- Exact office URLs can change; use the A–Z directory and sitemaps for canonical-link refresh.
- Academic requirements must be catalog-year aware.
- Deadlines, prices, jobs, menus, events, class sections, and emergency status require live verification.
- External sites may prohibit scraping; use licensed APIs, approved feeds, search discovery, and canonical employer/provider links.
- High-risk questions require official sources and authorized university contacts.
