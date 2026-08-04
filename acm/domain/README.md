# Core domain model

Design around organizational reality, not UI pages.

## Entities index

| Area | Doc |
|------|-----|
| Organization & identity | [`identity.md`](./identity.md) |
| Structure (terms, positions, committees) | [`structure.md`](./structure.md) |
| Authorization | [`authorization.md`](./authorization.md) |

## Modeling rules

1. Always include `organization_id` even for one chapter.
2. User account ≠ ACM membership.
3. Every governance record belongs to a `term`.
4. Role assignment is time-bounded evidence, not a free-form enum on the user.
5. Soft state changes only (Law 4).
