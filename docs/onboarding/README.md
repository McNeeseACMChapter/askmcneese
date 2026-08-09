# AskMcNeese Guest Onboarding

## Purpose

The public beta assigns an anonymous guest session and guides first-time visitors through the real AskMcNeese interface. No email, fingerprint, McNeese login, or private student data is required.

## Visitor journey

```text
bootstrap guest
    -> admission for newly assigned guests
    -> 14-step guided walkthrough
    -> final progress save
    -> Welcome, Guest {alias}
    -> normal application
```

Returning guests resume an incomplete tour or skip it after completion. Settings exposes **Replay walkthrough** without creating another guest identity.

## Identity and storage

- Secret cookie: `askmcneese_guest`, HttpOnly, `SameSite=Lax`.
- Public label: short `displayAlias`, rendered as `Guest XXXX`.
- Server stores a hash of the token and tour state in SQLite.
- Production HTTPS must use `GUEST_COOKIE_SECURE=true`.
- Identity is not derived from IP address, browser fingerprint, or User-Agent.

## Canonical walkthrough

The tour has 14 conceptual steps:

1. Welcome
2. Ask navigation
3. Ask composer
4. Class Planner
5. Planner week
6. Planner search
7. About and guided reading
8. Updates
9. Usage
10. Conversations
11. Ask welcome area
12. Settings
13. Feedback
14. Completion

The tour advances from real interactions and route state. Mobile menu opening is a substate, not an extra numbered step.

## Interaction behavior

- **Navigation:** visitors activate the actual highlighted navigation item.
- **Mobile menu:** the real menu opens, then the actual destination is activated.
- **About:** the visitor scrolls naturally through three anchors; reaching the final section releases the tour.
- **Conversations:** a collapsed desktop sidebar expands only for this checkpoint and returns to the saved preference afterward.
- **Explanations:** compact acknowledgement controls are used only when no product action is required.
- **Completion:** progress must save before the overlay exits.

## Presentation

- Solid editorial navy annotation surface with restrained depth
- Thin step-progress line and `NN / 14` index
- Four surrounding scrims that keep the target clear
- Subtle gold target halo and short tether
- Compact mobile top/bottom placement
- Reduced-motion behavior for users who request it
- Clear Retry only for missing UI targets, bootstrap failure, or final save failure

Ordinary background progress retries do not replace tour content with technical error copy.

## API

| Method and path | Purpose |
| --- | --- |
| `POST /guest/bootstrap` | Create or resume guest and return public state |
| `PATCH /guest/tour` | Persist current step |
| `POST /guest/tour` | Compatibility alias for restrictive proxies |
| `POST /guest/tour/replay` | Reset progress for the same guest |
| `POST /guest/dev-reset` | Development-only reset when enabled |

Credentialed CORS must explicitly allow the frontend origin and `GET`, `POST`, `PATCH`, and `OPTIONS`.

## Persistence model

`TourPersistQueue` is single-flight, deduplicates repeated steps, retries transient failures with bounded backoff, and does not block local navigation. The state machine owns admission, entering, active, drawer, route transition, guided reading, completion, exit, completed, and recoverable-error phases.

## Development

```env
ONBOARDING_MODE=mandatory
GUEST_DB_PATH=backend/guest_sessions.sqlite3
GUEST_COOKIE_MAX_AGE_SECONDS=5184000
GUEST_COOKIE_SECURE=false
ONBOARDING_DEV_RESET=true
```

Use secure cookies and disable development reset in production.

## Verification

- Backend guest and CORS tests
- Frontend state-machine, step-resolution, API, and persistence tests
- Full desktop 14-step browser traversal
- About end-of-page release check
- Completion persistence check
- Mobile navigation regression tests
- Fresh-console warning/error check

See [`IMPLEMENTATION_RECORD.md`](IMPLEMENTATION_RECORD.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md).
