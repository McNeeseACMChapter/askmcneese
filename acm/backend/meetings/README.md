# `meetings` module

Bounded ACM domain module. See `../README.md` and `../../PROGRAM.md`.

## Layout (target)

```
meetings/
├── models/
├── schemas/
├── repository/
├── service/
├── policy/
├── workflow/
├── routes/
├── events/
└── tests/
```

## Rules

- Enforce permissions via `authorize(actor, permission, scope)` — never role-name shortcuts.
- Soft-delete / archive / reverse / supersede only (Law 4).
- Emit audit events for privileged transitions.
- No production business logic until Phase 0 policy decisions are closed for this module's dependencies.
