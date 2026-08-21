# Notification architecture

Triggered by meaningful events — not spam.

## Example triggers

- Role assignment awaiting approval
- Officer access expires in 14 days
- Agenda published / vote opened
- Task overdue
- Project moved to blocked
- Receipt missing
- Event approval rejected
- Social post awaiting review
- SGA deadline approaching

## Payload shape

Every notification must contain:

| Field | Purpose |
|-------|---------|
| What happened | Event summary |
| Why this user | Targeting reason |
| Required action | Clear next step |
| Deadline | If any |
| Direct link | Deep link into ACM Panel |
| Priority | urgent / high / normal / low |

Avoid notifying everyone about everything. Route by permission + ownership + subscription.
