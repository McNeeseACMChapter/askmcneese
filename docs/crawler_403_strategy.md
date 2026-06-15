# Crawler 403 Strategy — `www.mcneese.edu`

**Status:** Resolved (technical) · **Owner:** Backend  
**Last updated:** June 15, 2026

---

## Problem (was)

`www.mcneese.edu` returns **HTTP 403** to plain Python `requests` because **Cloudflare**
shows a "Just a moment… Checking your browser" challenge. Subdomains like
`catalog.mcneese.edu` were never blocked.

**Why ChatGPT / Claude can read the site but `requests` could not:** browsing tools run a
**real browser engine** that executes Cloudflare's JavaScript challenge. Simple HTTP clients
do not run JavaScript — they only see the 403 challenge page.

---

## Solution (implemented)

**Automatic browser fallback** in the crawler pipeline:

1. `crawler.py` tries fast HTTP (`requests`) first.
2. If the response is a Cloudflare block (403 or challenge HTML), it retries via
   **`browser_fetch.py`** — headless Chromium through Playwright.
3. Real page HTML is saved to `crawler/raw/` and the normal clean → chunk → ingest path runs.

**Setup (one time per machine):**

```bash
cd crawler
pip install -r requirements.txt
python -m playwright install chromium
```

**Proof:**

```bash
python crawler.py https://www.mcneese.edu/admissions/
# OK 200  ... [browser]

python ingest.py --url https://www.mcneese.edu/admissions/
# INGESTED ... chunks=N ...
```

---

## Domains that still use fast HTTP only

These return 200 without browser fallback (faster):

| Domain | Notes |
|--------|-------|
| `catalog.mcneese.edu` | Academic catalog |
| `schedule.mcneese.edu` | Class search |
| `mcneesesports.com` | Athletics |
| `mcneese.presence.io` | Student orgs |

---

## Optional future improvement (not required for crawl to work)

Contact McNeese web/IT for an official crawler allowlist — reduces reliance on headless
browser and is better for high-volume production. **Not a blocker** for the student project.

---

## Decision log

| Date | Decision | By |
|------|----------|-----|
| 2026-06-14 | Document Cloudflare options | PM |
| 2026-06-15 | Implement Playwright auto-fallback in crawler | Backend fix |
