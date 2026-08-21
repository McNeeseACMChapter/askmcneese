# Beta Version Sprint Completed

**Date:** 2026-08-08  
**Branch:** `dev`  
**Release state:** Beta candidate  
**Change notice:** Subject to change if production bugs, security findings, accessibility issues, source changes, or operational failures are encountered.

## Outcome

This sprint brings the public AskMcNeese experience, mandatory anonymous onboarding, Class Planner, source-grounded answer presentation, responsive shell, and About/team story into one integrated beta candidate.

The release is not a claim of production finality. It is a tested beta baseline from which defects can be reproduced, prioritized, and corrected.

## Delivered in this beta completion pass

### Guest onboarding and application shell

- Added anonymous guest bootstrap and hashed HttpOnly-cookie persistence.
- Added a canonical 14-step state-machine walkthrough.
- Added mobile menu substates, real route/target progression, and About guided reading.
- Corrected credentialed CORS for `PATCH /guest/tour` and added a POST compatibility alias.
- Added bounded, deduplicated background persistence.
- Fixed the observer feedback loop that could freeze the page.
- Fixed collapsed-desktop Conversations targeting by temporarily expanding the saved sidebar state for that checkpoint.
- Verified final completion persistence and normal return to Ask.
- Refined the walkthrough into a quieter editorial surface with clear progress and reduced-motion handling.

### Class Planner

- Added a normalized backend read API and guarded SQLite publication pipeline.
- Added deterministic search, filtering, meeting normalization, conflicts, credits, and schedule persistence.
- Added phone Find/Week behavior and desktop discovery/calendar composition.
- Added McNeese-local current-time projection.
- Contained desktop result-pane overflow and expanded section layouts.
- Replaced the oversized striped loader with three compact course-shaped skeleton rows.
- Debounced search, aborted stale requests, and retained previous results during refresh.
- Removed the duplicate browser search-cancel affordance.

### Ask and navigation

- Integrated Class Planner into desktop and mobile navigation.
- Added tour anchors to Ask, the composer, welcome area, navigation, settings, and feedback.
- Optically centered collapsed Ask, New Conversation, Settings, and Feedback controls.
- Preserved browser-local conversation behavior and real backend source modes.

### About and contributor story

- Removed redundant hero logo/kicker and decorative orbit labels.
- Aligned the editorial content rhythm and replaced defensive wording with positive evidence language.
- Replaced meaningless trace marks and metadata dots with relevant icons.
- Removed the team-photo background layer from the story stage.
- Refined progress, previous/play-pause/next controls, and portrait crops.
- Added and optimized Evan Weber's supplied portrait.
- Replaced the distracting `HUMAN` background word with `ACM`.
- Verified the contributor story and About tour release in a real browser.

### Backend integration

- Registered guest and Class Planner routers in FastAPI.
- Added explicit credentialed CORS origins and required methods.
- Added lifecycle hooks for the optional class synchronization scheduler.
- Documented the new endpoints, storage ownership, and production configuration.

## Development history incorporated

The `dev` branch already contains the earlier beta foundation from `origin/main` through commit `89d12db`, including:

- Sprint 1 repository, health, QA, and backlog foundation
- initial Ask RAG endpoint and frontend integration
- PDF ingestion and governed source registry expansion
- retrieval ranking, page opening, citation, and hybrid-search improvements
- live activity and structured answer presentation
- public shell, mobile Ask improvements, brand integration, and About redesign
- campus search-intelligence artifacts and capability coverage
- the separate ACM Panel prototype and documentation

Git remains the exact commit-by-commit audit trail; this document is the human-readable release summary.

## Files and domains in the completion commit

- Root environment and documentation
- `backend/app/main.py`
- `backend/app/routers/guest.py`
- `backend/app/routers/class_planner.py`
- `backend/app/services/guest/`
- `backend/app/services/class_planner/`
- guest and planner backend tests/fixtures
- `frontend/src/features/onboarding/`
- `frontend/src/features/class-planner/`
- application shell, mobile navigation, Ask anchors, settings, About, and contributor UI
- responsive styles and approved contributor media
- onboarding, Class Planner, backend, frontend, crawler, and release documentation

## Validation evidence

Completed before publication:

- Frontend TypeScript check: passed
- Frontend full Vitest suite: 192 passed across 29 files
- Backend guest and Class Planner suites: 19 passed
- Frontend production build: passed (`2570` modules transformed)
- Full 14-step desktop walkthrough: passed
- About end-of-page release: passed
- Final guest tour save: passed
- Fresh browser console after QA: no warnings or errors
- Git whitespace validation: passed


## Known boundaries

- This is a beta candidate, not a production guarantee.
- Guest sessions do not own conversation history or planned schedules server-side.
- Class Planner does not register, drop, or modify official enrollment.
- Planner freshness depends on a successful validated source synchronization.
- Ask quality depends on source coverage, freshness, provider availability, and evidence ranking.
- Private or login-only McNeese data remains out of scope.
- The production bundle reports a large main-chunk advisory; code splitting remains follow-up work.
- Local development may use a non-default backend port, but committed examples use port `8000`.

## Production response policy

When a production bug is encountered:

1. Record the exact route, viewport, question/action, time, and visible failure.
2. Preserve sanitized browser/backend evidence.
3. Add a reproducible regression test when practical.
4. Correct documentation when behavior or configuration changes.
5. Publish the fix through `dev` review before merging to `main`.

No release note should imply that the beta is immutable or that an AI answer replaces official university authority.
