# Week 1 Sprint Backlog — AskMcNeese

**Sprint 1: Foundation · Week 1 only**
**Workstreams covered:** PM / Full-Stack · Content & Knowledge · DevOps / QA
**Excluded (own separate docs):** Backend Developer · Frontend Developer

[← Back to backlog overview](./README.md)

---

## Week 1 goal

By Friday, the team should have a working foundation: repo + structure, FastAPI `/health`, React chat shell connected to `/health`, crawler/chunker proof on approved public pages, source registry seed file, and QA evidence. **This is not the AI answer week yet.**

---

## 1. PM / Full-Stack — Prince

**Mission:** Make the project real — repo, branch strategy, folder structure, FastAPI health endpoint, DB schema draft, environment docs, task board, and review rhythm. Stable foundation that Backend and Frontend can build on.

| Ticket | Task | Target day | Acceptance criteria | Status |
|--------|------|------------|---------------------|--------|
| **PM-01** | Create repo + branch strategy | Day 1 | `main` / `dev` / `feature/*` exist; team invited; first README committed | ✅ Done |
| **PM-02** | Set project folder structure | Day 2 | Required folders exist and are explained in README | ✅ Done |
| **PM-03** | Build FastAPI `/health` endpoint | Day 3 | `/health` returns valid JSON locally and Frontend can call it | ✅ Done |
| **PM-04** | Draft DB schema | Day 4 | `source_registry`, `chunks`, `query_logs` documented with field names and purpose | ✅ Done |
| **PM-05** | Create `.env.example` + setup docs | Day 5 | No real secrets included; all required variables listed | ✅ Done |
| **PM-06** | Run sprint review + task board cleanup | Day 5 | Every role has done / proof / blocker status by Friday | ✅ Done |

**Notes on completed items:**
- **PM-01** — Repo live with `main`, `dev`, `feature/*`; team has write access.
- **PM-02** — `backend/`, `crawler/`, `docs/`, `frontend/`, `knowledge/`, `scripts/`, `tests/` merged into `dev`; README in place.
- **PM-03** — FastAPI app in `backend/app/`; `GET /health` returns `{ status, service, version }`. Shipped PR #4.
- **PM-04** — `docs/db_schema.md` documents `source_registry`, `chunks`, `query_logs`. Shipped PR #4.
- **PM-05** — Root `.env.example` + `docs/setup.md`. Shipped PR #4.
- **PM-06** — `docs/week1_review.md` with per-role Done / Partial / Blocked status.

---

## 2. Content & Knowledge — Source Registry

**Mission:** Give Backend clean, approved public sources to crawl. Build the source registry seed file, categorize URLs, assign provisional trust tiers, and write starter test questions. **This role does not write code.**

| Ticket | Task | Target day | Acceptance criteria | Status |
|--------|------|------------|---------------------|--------|
| **CK-01** | Create source registry seed CSV | Day 1 | Columns match Backend needs; no unapproved URLs marked approved | ✅ Done |
| **CK-02** | Collect first 3 public seed pages | Day 2 | Homepage, events, and financial aid source entries exist | ✅ Done |
| **CK-03** | Categorize and trust-tier sources | Day 3 | Each row has category, owner, trust tier, and notes | ✅ Done |
| **CK-04** | Write 15 starter test questions | Day 4 | Questions map to categories and expected source URLs | ⬜ To Do |
| **CK-05** | Handoff to Backend | Day 5 | Backend confirms crawler can read the approved list | ⚠️ Partial |

**Targets:**
- **CK-01** — File `knowledge/source_registry_seed.csv` with columns: `url, title, category, trust_tier, department_owner, approval_status, notes, last_checked_date`.
- **CK-02** — Public pages only; anything uncertain gets `approval_status = needs_review`.
- **CK-04** — File `knowledge/test_questions_week1.md`; categories: event, form/deadline, contact, policy, ACM info.

**Content rules:**
- No Canvas, student records, login-only pages, or private documents.
- Do not approve a URL just because it is useful — PM must approve uncertain sources.
- Prefer official McNeese sources over unofficial summaries.
- Every source must support future citations, freshness checks, and conflict review.

---

## 3. DevOps / QA — Governance Support

**Mission:** Make the team's work verifiable. Confirm setup instructions, define PR/review rules, prepare smoke tests, collect evidence, and support the PM verification path. **No production deployment in Week 1.**

| Ticket | Task | Target day | Acceptance criteria | Status |
|--------|------|------------|---------------------|--------|
| **DQ-01** | Validate repo setup | Day 1 | A new teammate can clone and follow README without guessing | ⚠️ Partial |
| **DQ-02** | Create PR checklist | Day 2 | Checklist protects branch strategy, secrets, proof, and review ownership | ⬜ To Do |
| **DQ-03** | Create Week 1 smoke tests | Day 3 | Tests cover PM, Backend, Frontend, and Content outputs | ⚠️ Partial |
| **DQ-04** | Support simple CI if ready | Day 4 | CI draft checks basic build/import only, or blocker is documented | ⬜ To Do |
| **DQ-05** | Collect sprint review proof | Day 5 | Evidence folder proves Week 1 output without verbal explanation | ⚠️ Partial |

**Targets:**
- **DQ-01** — Log issues in `docs/qa/week1_setup_notes.md`.
- **DQ-02** — File `docs/qa/pr_checklist.md`: issue linked, branch from `dev`, no secrets, local run proof, screenshot/terminal proof, reviewer assigned.
- **DQ-03** — File `docs/qa/week1_smoke_tests.md`: backend `/health` returns 200; frontend loads; frontend shows `/health` status; crawler fetches one approved URL; chunker produces chunks.
- **DQ-04** — Keep CI light (backend lint/import check, frontend build check). Don't block the team.

**DevOps/QA rules:**
- No production deployment in Week 1.
- No heavy CI before the foundation works locally.
- Nothing is marked **Done** without proof.
- PM verification comes before DevOps/QA marks a deliverable accepted.

---

## Dependencies / handoffs (excluded streams)

These are **not tasks on this board** — they belong to the Backend and Frontend role docs — but they connect to the tickets above:

| Depends on | Needed by |
|------------|-----------|
| Backend reads `knowledge/source_registry_seed.csv` | CK-05 handoff |
| Backend confirms DB schema field names | PM-04 |
| Frontend calls FastAPI `/health` | PM-03 |
| Backend crawler + chunker proof | DQ-03 smoke tests |
| Frontend chat shell loads | DQ-03 smoke tests |

---

## Week 1 meeting rhythm

| Meeting | Timebox | Purpose | Required output |
|---------|---------|---------|-----------------|
| Kickoff | 30 min | Confirm repo access, roles, Week 1 scope, source approval rule | Everyone knows their file and ticket list |
| Midweek check | 20 min | Catch blockers before Friday | Blocked tasks moved to PM action list |
| Friday review | 45 min | Demo proof, not explanations | Done / Partial / Blocked status per role |

---

## Hard scope boundaries (Week 1)

- ❌ No Canvas integration
- ❌ No Microsoft SSO
- ❌ No LLM answer generation
- ❌ No full-site crawling
- ❌ No production deployment
- ❌ No private / login-only / student-record data

---

## Ticket count summary

| Workstream | Tickets | Done | Remaining |
|------------|---------|------|-----------|
| PM / Full-Stack | 6 | 6 | 0 |
| Content & Knowledge | 5 | 3 | 2 |
| DevOps / QA | 5 | 0 | 5 (3 partial) |
| **Total** | **16** | **9** | **7** |

> **Excluded streams (tracked separately):** Frontend FE-01..FE-05 ✅ all done (PR #5). Backend BE-01..BE-05 ✅ reference done (PR #3); assigned dev submission ⚠️ partial.
