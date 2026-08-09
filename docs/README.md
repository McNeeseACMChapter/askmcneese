# AskMcNeese Documentation Index

This directory contains current architecture, implementation evidence, release notes, audits, and historical planning records.

## Current release

- [`BETA_SPRINT_COMPLETION.md`](BETA_SPRINT_COMPLETION.md): authoritative beta-sprint scope, validation, known limitations, and change log
- [`onboarding/README.md`](onboarding/README.md): guest identity and 14-step walkthrough
- [`class-planner/README.md`](class-planner/README.md): planner behavior, data contract, and boundaries
- [`BRAND_LOGO_RULES.md`](BRAND_LOGO_RULES.md): approved logo usage
- [`LIVE_TRAIL_IMPLEMENTATION.md`](LIVE_TRAIL_IMPLEMENTATION.md): streamed activity presentation

## Backend and retrieval

- [`rccs/RCCS_IMPLEMENTATION_REPORT.md`](rccs/RCCS_IMPLEMENTATION_REPORT.md)
- [`rccs/RCCS_IMPLEMENTATION_AUDIT.md`](rccs/RCCS_IMPLEMENTATION_AUDIT.md)
- [`rccs/RCCS_WEB_MODE_WIRING_AUDIT.md`](rccs/RCCS_WEB_MODE_WIRING_AUDIT.md)

## Architecture and implementation records

- [`onboarding/ARCHITECTURE.md`](onboarding/ARCHITECTURE.md)
- [`onboarding/IMPLEMENTATION_RECORD.md`](onboarding/IMPLEMENTATION_RECORD.md)
- [`class-planner/ARCHITECTURE.md`](class-planner/ARCHITECTURE.md)
- [`class-planner/IMPLEMENTATION_RECORD.md`](class-planner/IMPLEMENTATION_RECORD.md)
- [`UI_OVERHAUL_IMPLEMENTATION.md`](UI_OVERHAUL_IMPLEMENTATION.md)
- [`UI_OVERHAUL_AUDIT.md`](UI_OVERHAUL_AUDIT.md)

Implementation records and audits describe the system at the date shown. When they conflict with current code or the beta completion record, current code and `BETA_SPRINT_COMPLETION.md` take precedence.

## Historical material

`backlog/` contains Sprint 1 planning artifacts and is retained for traceability. It is not the current product roadmap.

## Separate ACM Panel

The ACM chapter-operations system has its own documentation under [`../acm/`](../acm/). Its data model, authentication plans, and internal workflows are separate from the public AskMcNeese assistant.

## Documentation policy

- Document only implemented behavior.
- Mark mock, staging, beta, and production behavior explicitly.
- Keep secrets, personal data, private logs, and local databases out of documentation commits.
- Update the release record when an externally visible contract changes.
- Treat this beta as subject to change when production bugs, security findings, source changes, or accessibility problems are encountered.
