# Week 1 Starter Test Questions — AskMcNeese (CK-04)

**Purpose:** Realistic student questions for QA smoke tests and Sprint 2 retrieval validation.
Each question maps to a **category** and an **expected source** from the registry.

> These are test inputs only — not guaranteed answers until `/ask` is wired in Sprint 2.

---

## Admissions / Future Students

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 1 | When is the deadline to apply for freshman admission? | form/deadline | SRC-002 Admissions Overview |
| 2 | How do I apply as a transfer student? | admissions | SRC-002 Admissions Overview |
| 3 | What are the estimated costs for an undergraduate student? | financial planning | SRC-004 Estimated Costs |
| 4 | Does McNeese offer online degree programs? | academic programs | SRC-009 Online Programs (SRC-007 fallback) |

## Financial Aid

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 5 | How do I apply for financial aid at McNeese? | financial aid | SRC-005 Financial Aid |
| 6 | What scholarships are available for new students? | scholarships | SRC-006 Scholarships |
| 7 | Where is the financial aid office located? | contact | SRC-005 Financial Aid |

## Academic Programs & Catalog

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 8 | What undergraduate majors does McNeese offer? | academic programs | SRC-007 Undergraduate Programs |
| 9 | Where can I find official degree requirements? | catalog / policy | SRC-011 Academic Catalog |
| 10 | What is the add/drop deadline this semester? | form/deadline | SRC-012 Academic Schedule, SRC-011 Catalog |

## Current Student Services

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 11 | How do I request an official transcript? | student services | SRC-015 Office of the Registrar |
| 12 | Where do I find the class schedule and registration dates? | schedule | SRC-012 Academic Schedule, SRC-013 Class Search |
| 13 | What is Student Central and what can I do there? | student services | SRC-014 Student Central |

## Campus Life & Events

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 14 | What student organizations can I join? | engagement | SRC-029 Organizations (Presence) |
| 15 | Where can I find McNeese athletics schedules and tickets? | athletics / event | SRC-028 Athletics |

## ACM / Project (smoke test)

| # | Question | Category | Expected source(s) |
|---|----------|----------|-------------------|
| 16 | Who built AskMcNeese? | ACM info | *(in-app attribution — not from crawl)* |

---

## How QA uses this file

1. Pick a question from the table.
2. Run retrieval (Sprint 2: `POST /ask` or ChromaDB search).
3. Confirm at least one returned chunk cites the **expected source URL**.
4. Log pass/fail in `docs/qa/week1_smoke_tests.md`.
