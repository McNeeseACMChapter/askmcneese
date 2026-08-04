# Phase 0 implementation record

## Date

2026-07-18

## Pass scope

Prepare the ACM Dashboard **Phase 0 governance package for human decision-making** only:

- Close structured content in `policy/decisions.md` (GOV-001…GOV-020)
- Draft permission matrix, workflow-transition matrix, Phase 0 review, and this record
- **No** production application code; **no** marking decisions `APPROVED` without chapter evidence
- **No** file create/modify/delete outside `askmcneese/acm/`
- Within this pass, only `askmcneese/acm/policy/` files were created or modified

## Files inspected

### Program entry

- `askmcneese/acm/README.md`
- `askmcneese/acm/PROGRAM.md`

### Policy

- `askmcneese/acm/policy/README.md`
- `askmcneese/acm/policy/VERSION`
- `askmcneese/acm/policy/decisions.md` (before/after rewrite in this pass)

### Laws

- `askmcneese/acm/laws/README.md`

### Domain

- `askmcneese/acm/domain/README.md`
- `askmcneese/acm/domain/structure.md`
- `askmcneese/acm/domain/identity.md`
- `askmcneese/acm/domain/authorization.md`

### Workflows

- `askmcneese/acm/workflows/README.md`
- `askmcneese/acm/workflows/role-assignment.md`
- `askmcneese/acm/workflows/meetings-decisions.md`
- `askmcneese/acm/workflows/projects.md`
- `askmcneese/acm/workflows/finance.md`
- `askmcneese/acm/workflows/events.md`
- `askmcneese/acm/workflows/communications.md`
- `askmcneese/acm/workflows/sga.md`

### Architecture

- `askmcneese/acm/architecture/README.md`

### Phases

- `askmcneese/acm/phases/README.md`
- `askmcneese/acm/phases/MVP.md`

## Files created

- `askmcneese/acm/policy/role-permission-matrix.md` (rewritten as complete draft catalog + compact matrix)
- `askmcneese/acm/policy/workflow-transition-matrix.md`
- `askmcneese/acm/policy/phase-0-review.md`
- `askmcneese/acm/policy/phase-0-implementation-record.md` (this file)

## Files modified

- `askmcneese/acm/policy/decisions.md` — inventory summary + structured GOV-001…GOV-020 records (status `PROPOSED`) + Phase 1 blocking table

## Decisions made

**None binding.** Agent did not approve chapter policy.

Structured **PROPOSED** records were authored for debate:

- GOV-001…GOV-020 (see `decisions.md`)

## Decisions deliberately not made

- No status set to `APPROVED`, `REJECTED`, or `SUPERSEDED` for any GOV item
- No numeric quorum or dollar thresholds finalized as chapter law (placeholders remain PROPOSED)
- No Phase 0 complete / Phase 1 GO declaration
- No sync edits to `domain/`, `laws/`, `workflows/`, or `phases/` to resolve `admin.configure` wording (out of allowed file set for this pass)
- No production auth, API, DB, or frontend implementation

## Contradictions found

1. Broad `admin.*` / `admin.configure` language in earlier domain drafts vs Phase 0 rule forbidding broad `admin.*` (matrix uses `system.*` keys).
2. GOV-009 contains competing quorum formulations pending a single chapter choice.
3. GOV-007 appointment final authority still has open alternatives (President vs board vs Advisor).
4. High-privilege inclusion of Tech SA vs prohibition on org approval authority (resolved in matrix as DENY for org approvals; must be confirmed in GOV-018 approval).

## Assumptions

- Existing ACM plan laws (1–7) remain engineering constraints, not evidence of chapter bylaw approval.
- Workflow state names in `workflows/*.md` are the authoritative draft state machines for the transition matrix.
- Technical System Administrator is a privileged **technical** role distinct from Faculty Advisor and student officers.
- Finance and communications modules remain out of Phase 1 implementation scope even if policies are discussed early.
- America/Chicago assumed for term end-of-day expiry in GOV-003 draft.

## Validation performed

- Confirmed allowed statuses used only: `UNRESOLVED` | `PROPOSED` | `UNDER_REVIEW` | `APPROVED` | `SUPERSEDED` | `REJECTED` — and all new GOV records are `PROPOSED`.
- Confirmed no GOV record marked `APPROVED` without leadership evidence.
- Confirmed permission matrix values limited to `ALLOW` | `DENY` | `CONDITIONAL` | `OWN_SCOPE_ONLY`.
- Confirmed no broad `admin.*` permission key in the new matrix.
- Confirmed Tech SA defaults deny organizational approve/publish/finance-approve powers.
- Confirmed workflow matrix covers all seven workflows listed in `workflows/README.md`.
- Confirmed Phase 0 review recommendation is **NO-GO** while hard blockers remain unresolved.
- Confirmed this pass only writes under `askmcneese/acm/policy/` (subset of `askmcneese/acm/`).

## Confirmation: no file outside `askmcneese/acm/` changed

**Confirmed for this pass:** no create, modify, move, rename, or delete outside `askmcneese/acm/`.  
All writes were under `askmcneese/acm/policy/`.

## Confirmation: no production code implemented

**Confirmed:** no authentication implementation, API routes, migrations, frontend screens, role-check code, financial workflow code, dependency changes, or modifications to the AskMcNeese RAG backend / public frontend as part of this pass.
