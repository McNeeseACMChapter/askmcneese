# Crawler 403 Strategy — `www.mcneese.edu` (Sprint 1 blocker → Sprint 2 decision)

**Status:** Documented · **Owner:** PM + Backend  
**Last updated:** June 14, 2026

---

## Problem

The main McNeese website (`www.mcneese.edu` and most child paths) returns **HTTP 403**
to programmatic HTTP requests, even with a realistic browser `User-Agent`. This blocks
automated ingestion for **~20 approved registry URLs** on that domain.

**Domains that work today (proven):**

| Domain | Example | Notes |
|--------|---------|-------|
| `catalog.mcneese.edu` | SRC-011 | Primary Sprint 1 proof source |
| `schedule.mcneese.edu` | SRC-013 | Class search landing |
| `mcneesesports.com` | SRC-028 | Separate athletics domain |
| `mcneese.presence.io` | SRC-029 | Student org platform |

---

## Current behavior (Sprint 1)

- Crawler uses `CRAWLER_USER_AGENT` from `.env` and standard browser-like headers.
- `ingest.py` fails gracefully when fetch returns non-200.
- PM has **content-approved** many `www.mcneese.edu` pages, but they remain **crawl-blocked**
  until a fetch strategy succeeds.
- `ALLOW_PENDING_SOURCES=true` in `.env` allows Week 1 proof on Pending rows; set
  `allow_pending=False` in production ingest runs.

---

## Options for Sprint 2 (pick one — PM decision)

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **A. Contact McNeese web team** | Official, sustainable | Needs admin lead time | Low code |
| **B. Sitemap + allow-listed paths** | May bypass some blocks | Still may 403 | Medium |
| **C. Manual HTML drop folder** | Unblocks demos fast | Not scalable | Low |
| **D. Headless browser fetch** | Often passes bot checks | Heavy, fragile, slower | High |
| **E. Prioritize subdomains only** | Works now | Misses main-site pages | Low |

**PM recommendation for Sprint 2 start:** **Option E** now (catalog + schedule + athletics + Presence)
while **Option A** runs in parallel for official bot allowance.

---

## What developers should do until resolved

1. **Do not** fake-ingest or scrape around auth/login pages.
2. Use **approved, reachable URLs** for ingest proofs (`catalog.mcneese.edu` minimum).
3. Mark ingest failures in PR proof — a 403 on `www.mcneese.edu` is a **known blocker**, not a bug.
4. When `/ask` ships in Sprint 2, answers will only come from **successfully ingested** chunks.

---

## Acceptance criteria (when this blocker is "resolved")

- [ ] PM documents chosen option in this file (section below)
- [ ] At least 3 previously-blocked `www.mcneese.edu` URLs ingest successfully
- [ ] `crawler/README.md` updated with the approved fetch method

### Decision log

| Date | Decision | By |
|------|----------|-----|
| 2026-06-14 | Document options; use subdomain-first for Sprint 2 | PM |
| | *(fill when web team / method chosen)* | |
