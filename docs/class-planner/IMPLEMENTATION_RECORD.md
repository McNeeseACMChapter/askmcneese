# Class Planner Production Data Platform — 2026-08-09

This record supersedes the earlier SQLite-production and in-process-scheduler assumptions. The approved Class Planner visual system remains unchanged.

# 1. Database

SQLAlchemy Core now provides one repository over PostgreSQL production and SQLite local/test. Live mode requires a PostgreSQL URL and refuses SQLite fallback. The normalized schema includes immutable datasets, term pointers, subjects, courses, sections, meetings, instructors, section relationships, categorized notes, availability overlays, sync telemetry/locks, and course activity.

The Render Blueprint defines a same-region Ohio PostgreSQL database and FastAPI service. Those external resources were not provisioned from this local session.

# 2. Parser Repair

The parser now extracts source-owned subject display names and separates linked instructor identities from the prose sharing the source cell. Registration notes, corequisites, and restrictions have independent fields/tables. The real ENGL online record resolves to instructor `Mahone, Taylor M` and note `ONLINE MAJORS ONLY NOT SELF PACED`; that note is not searchable as a professor.

# 3. Search

Course search executes in SQL over normalized code, title, CRN, and instructor columns. It does not load the dataset into Python and does not contact McNeese during normal search. Source aliases and unique initials canonicalize `Computer Science 180` and `cs 180` to `CSCI 180`. PostgreSQL uses `pg_trgm` similarity with GIN indexes for typo tolerance. Exact normalized course code ranks first.

Verified local searches:

- `CSCI 180` → `202660:CSCI:180`
- `cs 180` → `202660:CSCI:180`
- `Computer Science 180` → `202660:CSCI:180`
- `61166` → `202660:CSCI:180`
- `Lavergne` → four published courses
- registration-note prose → zero course matches

# 4. Query Performance

The former Python full-dataset scan had no preserved trustworthy latency measurement, so no fabricated before number is reported.

After implementation, 30 warm SQLite staging searches over 862 courses/1,606 sections measured:

- median: 13.58 ms
- p95: 18.71 ms
- maximum: 21.81 ms

Section hydration is covered by a constant-query-count test (five statements for one unselected course page), preventing N+1 growth.

# 5. Large Courses

Search responses contain course summaries and counts, not every section. Expansion defaults to six sections with `limit`, `offset`, `hasMore`, and `nextOffset`. ENGL 100 has 13 sections: browser QA rendered six, then `Show 6 more (7 remaining)`, then `Show 6 more (1 remaining)`.

# 6. Freshness

`fetchedAt` is immutable dataset creation time. `metadataVerifiedAt` advances after a successful full comparison even when content is unchanged. `availabilityVerifiedAt` advances after availability verification. `availabilityState` derives from the configured TTL. Unchanged full syncs update clocks/overlays without creating another dataset.

# 7. Add Verification

Add calls the normalized section endpoint with `verify=true`. A successful targeted refresh updates the availability overlay. If instructor, room, meeting, or availability changed, the UI requires review before a later Add. If McNeese cannot be reached, the stored snapshot remains visible, Add continues, and the student sees that availability could not be reverified.

# 8. Synchronization

Full metadata sync follows fetch → parse → normalize → validate → anomaly check → atomic promotion. Availability overlays update independently. Stale course opens queue targeted refresh; recently opened courses are eligible for the five-minute job. GitHub Actions owns recurrence. The web process contains no scheduler loop.

# 9. Full Sync Performance

Previous measured baseline: approximately 34 minutes.

New real Fall 2026 run:

- duration: 508.094 seconds (8 minutes 28 seconds)
- subjects: 76/76
- workers: four
- polite submission delay: one second
- records: 1,606 received / 1,606 valid / 0 rejected
- result: dataset 1 atomically published

Four workers improve throughput without unbounded fan-out or removing the source delay. Correctness gates remained enabled.

# 10. PostgreSQL Production Setup

Complete in code: SQLAlchemy repository, strict live configuration, psycopg driver, Render Blueprint, migration command, same-region topology, Postgres CI service, trigram extension/index migration, protected triggers, and bootstrap documentation.

Actually configured externally: nothing was provisioned or deployed in this session.

Operator actions remaining: apply the Blueprint, set secret values, apply migrations, configure GitHub secrets/term variable, run initial production sync, inspect telemetry, smoke-test the deployed API, then explicitly promote the frontend from staging to live.

# 11. Migrations

Alembic revision `20260809_0001` creates the normalized platform schema. PostgreSQL additionally enables `pg_trgm` and creates GIN indexes on normalized course code/title. `script.py.mako` supports future revisions. Local upgrade, current, and downgrade were executed successfully against temporary SQLite.

# 12. Production API

Implemented and locally smoke-tested with the real staging snapshot:

- `/class-planner/terms`: 200
- `/class-planner/freshness?term=202660`: 200
- course search: 200
- bounded course sections: 200
- direct section lookup: covered by automated API tests
- protected sync without a valid token: 401
- missing validated dataset: 503 by contract

No deployed production API smoke test was claimed.

# 13. GitHub Workflows

- `class-planner-sync.yml`: daily at 08:17 UTC plus manual dispatch; iterates comma-separated `CLASS_PLANNER_TERM_IDS`.
- `class-planner-availability.yml`: every five minutes plus manual dispatch; refreshes active courses for configured terms.
- `ci.yml`: dependency checks, PostgreSQL 16 service, Alembic migration, backend tests, frontend typecheck/tests/build.

Required secrets: `CLASS_PLANNER_BACKEND_URL` and `CLASS_SYNC_ADMIN_TOKEN`. Required variable: `CLASS_PLANNER_TERM_IDS`.

# 14. Reliability

- last-known-good term pointer
- one-transaction dataset publication
- owner-token locks with stale-lock expiry
- atomic operator rollback
- four-dataset retention per term
- anomaly gates for collapse, removals, validation loss, instructor loss, and meeting loss
- deterministic structural errors with bounded HTTP retry
- per-subject status, duration, count, and hash telemetry
- no raw HTML or secrets stored in logs

# 15. Tests

Actually run:

- backend Class Planner suite: 20 passed
- full frontend suite: 209 passed across 32 files
- TypeScript: passed
- production frontend build: passed
- Alembic SQLite upgrade/current/downgrade: passed
- workflow and Render YAML parsing: passed
- real source bootstrap: passed
- real local API smoke: passed
- responsive browser interaction checks: passed

# 16. Production Smoke Test

Not run against Render because no deployment, database provisioning, commit, or push was authorized. The equivalent local staging smoke used the real Fall 2026 snapshot and returned 200 for terms, freshness, search, and bounded sections. Production readiness remains gated on the deployed PostgreSQL smoke.

# 17. Responsive Verification

Browser QA used the real staging API at:

- 390 × 844
- 768 × 1024
- 1440 × 900

All three had document width equal to viewport width, zero detected main-content overflow, no card overlap, and no browser console warnings/errors. Mobile alias search and course expansion worked. The approved responsive visual composition was not redesigned.

# 18. Files Created

- `backend/app/services/class_planner/db.py`
- `backend/app/services/class_planner/availability.py`
- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/20260809_0001_class_planner_platform.py`
- `.github/workflows/class-planner-sync.yml`
- `.github/workflows/class-planner-availability.yml`
- `render.yaml`

# 19. Files Modified

- `backend/app/services/class_planner/models.py`
- `backend/app/services/class_planner/pipeline.py`
- `backend/app/services/class_planner/store.py`
- `backend/app/routers/class_planner.py`
- `backend/app/main.py`
- `backend/requirements.txt`
- `backend/tests/unit/test_class_planner_data.py`
- `frontend/src/features/class-planner/plannerTypes.ts`
- `frontend/src/features/class-planner/plannerApi.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `.github/workflows/ci.yml`
- `.env.example`
- Class Planner documentation

# 20. Documentation

Updated `docs/class-planner/README.md`, `ARCHITECTURE.md`, and this implementation record. Environment/deployment guidance now describes PostgreSQL production, SQLite local/test, current/next term configuration, GitHub-owned scheduling, six-section loading, targeted availability, migrations, rollback, and the explicit live-promotion gate.

# 21. Remaining Risks

- PostgreSQL migration and query behavior have not yet been exercised on the actual Render database.
- `pg_trgm` creation depends on the managed database owner's extension permission.
- McNeese currently publishes Fall 2026 but not Spring 2027; a nonexistent next term was not fabricated.
- GitHub secrets and `CLASS_PLANNER_TERM_IDS` still require operator configuration.
- FastAPI background tasks are best-effort rather than a durable queue; a process restart can interrupt a triggered job, while last-known-good data remains safe.
- Targeted availability still uses the verified course-search contract because no cheaper section-only source endpoint is known.
- The production bundle passes but reports an existing main-chunk size warning.
- Production deployment and smoke testing remain undone by instruction.

# 22. Current Data Mode

- Runtime fixtures: removed; deterministic course records exist only inside unit tests.
- Staging: active locally with the validated Fall 2026 SQLite snapshot.
- Live: code path is implemented but not promoted. `render.yaml` intentionally leaves the static frontend in staging until the production gate passes.

# 23. Production Readiness

**PARTIALLY READY**

The code, local real-data bootstrap, migrations, tests, performance measurement, and responsive behavior are ready. It is not ready for controlled beta until Render PostgreSQL is provisioned, migrations and the initial sync succeed there, GitHub secrets are configured, the deployed smoke suite passes, and live mode is explicitly promoted.
