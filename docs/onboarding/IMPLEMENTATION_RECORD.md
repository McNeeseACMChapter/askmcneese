# Onboarding Implementation Record — 2026-08-08

## Root CORS cause

Browsers preflight `PATCH /guest/tour` with `OPTIONS`. When `Access-Control-Allow-Methods` omitted `PATCH` (or the API process had not reloaded the credentials/PATCH CORS update), the preflight failed with `net::ERR_FAILED`. `TourProvider` then retried progress saves, producing a PATCH storm and “Connection needed / Retry” UI on ordinary steps.

## CORS fix

In `backend/app/main.py`:

- `allow_credentials=True` with **explicit** origins (never `*`)
- Origins from `CORS_ALLOWED_ORIGINS` or legacy `CORS_ALLOW_ORIGINS`, defaulting to `http://127.0.0.1:5173,http://localhost:5173`
- Methods: `GET`, `POST`, `PATCH`, `OPTIONS`
- Headers: `Content-Type`, `Accept`, `Last-Event-ID` (and lowercase variants)
- `max_age=600`

Also added `POST /guest/tour` as an alias of PATCH for stubborn proxies.

## Guest admission

New guests (`isNewAssignment` + `not_started`) see a brand-canvas admission (mark → wordmark → alias) before tour enter. Returning incomplete guests resume the tour without re-announcing assignment. Completed guests skip onboarding.

## Guest identity

| Field | Role |
| --- | --- |
| Cookie `askmcneese_guest` | Secret session token (HttpOnly; never displayed) |
| `guestId` | Stable public server id (`guest_…`) |
| `displayAlias` | Short 4-char UI label derived from a hash of `guestId` |

## Tour state machine

Phases: `BOOTSTRAPPING`, `ADMISSION`, `TOUR_ENTERING`, `TOUR_ACTIVE`, `DRAWER_SUBSTATE`, `ROUTE_TRANSITION`, `GUIDED_READING`, `TOUR_COMPLETING`, `TOUR_EXITING`, `COMPLETED`, `RECOVERABLE_ERROR`.

## Tour visual model

Ordinary walkthrough cards removed. Desktop uses a gradient annotation field; mobile uses an edge caption. Four-scrim spotlight keeps the target sharp.

## Mobile navigation

Hamburger highlight → real open → same conceptual step → destination auto-spotlighted → real item tap → route observer advances. No duplicate “Open X” tour CTAs.

## About

One global step. After route open: light guided reading caption; natural scroll; auto-complete at ~92% scroll or final anchor in view. No redundant Continue chain.

## Duplicate actions

Click-target steps show an action hint (“Tap Updates…”) and advance from `completeRoute` / target activation, not from a second tour Open button.

## Tour entrance / exit

`TOUR_ENTERING` (~240ms) and `TOUR_EXITING` (~340ms), reduced-motion aware, before normal Ask.

## Welcome Guest

After successful completion, Ask empty hero shows `Welcome, Guest {alias}` via `useTour().showWelcomeGuest`.

## Persistence

`TourPersistQueue`: single-flight, dedupe, max 5 retries with backoff. Final failure only shows a brand-canvas retry state.

## Files changed (this corrective pass)

- `backend/app/main.py`
- `backend/app/routers/guest.py`
- `backend/app/services/guest/store.py`
- `backend/tests/unit/test_guest_onboarding.py`
- `frontend/src/features/onboarding/*` (provider, overlay, steps, api, persist queue, admission, css)
- `frontend/src/components/chat/EmptyState.tsx`
- `frontend/src/components/layout/SettingsPanel.tsx`
- `frontend/index.html` (`mobile-web-app-capable`)
- `askmcneese/.env.example`
- `docs/onboarding/README.md`
- `docs/onboarding/ARCHITECTURE.md`
- `docs/onboarding/IMPLEMENTATION_RECORD.md`

## Tests

- `python -m unittest tests.unit.test_guest_onboarding -v` → 7 passed (includes CORS preflight + PATCH/POST + replay)
- `vitest run src/features/onboarding/tourSteps.test.ts` → 4 passed
- Live on `127.0.0.1:8003`: `OPTIONS /guest/tour` allows `PATCH`; bootstrap returns `displayAlias` + `isNewAssignment`; `PATCH /guest/tour` with cookie succeeds

Note: a zombie listener was observed on port `8001` serving stale guest payloads without `displayAlias`. Local frontend `.env` was pointed at `8003` for a clean API process. Free/kill `:8001` and switch back if desired.

## Freeze fix (post-admission UI hang)

**Cause:** `MutationObserver` watched `attributes: true` on `document.body` while `refreshRect` toggled `tour-target-active` (and body tour classes). Each class write re-fired the observer → `setRect` → main-thread livelock (“Page Unresponsive”) immediately after Guest Admission / tour start.

**Fix:** observe `childList` only; rAF-throttle measures; skip `setRect` when geometry unchanged; apply target class only when the active target changes; scroll-into-view once per target; About completion armed after a short delay.

## Limitations

- Conversations / Class Planner schedules are not server-owned by guest id yet.
- Welcome Guest is session-flagged after first completion in the browser tab set; not a permanent chrome badge.
- Full multi-viewport visual QA remains iterative on local servers.
- If port `8001` still hosts a zombie API process, use the configured clean API port in `frontend/.env`.

## Beta completion verification — 2026-08-08

Final interaction and visual pass:

- Replaced the previous sparse annotation treatment with a compact editorial navy surface, thin progress line, restrained target halo, and reduced-motion fallback.
- Preserved the canonical 14-step model and real product actions.
- Confirmed About advances from Reading 1/3 to 2/3 and releases only after a user-initiated traversal reaches the final anchor.
- Found and fixed a remaining desktop step-10 defect: the collapsed sidebar did not render `data-tour-id="conversations"`. `PublicAppShell` now temporarily expands the conversation region only while that checkpoint is active, preserving the saved preference afterward.
- Completed steps 1 through 14 in a real browser and confirmed the final guest save returns to Ask without the former connection-error screen.
- Confirmed a clean fresh-browser console after the fix.

Validation:

- `npm run typecheck`: passed.
- Focused onboarding and mobile navigation tests: 22 passed.
- `npm run build`: passed; 2,570 modules transformed.
- Browser traversal: 14/14 steps passed, including Settings and Feedback route targets.