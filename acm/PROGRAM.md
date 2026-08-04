# ACM Dashboard — First-Principles Program Plan

> Product name in UI: **ACM Panel**  
> System role: chapter internal operating system and permanent system of record.

## Start from the fundamental problem

See [`README.md`](./README.md) for the seven objects and the questions the system must always answer.

Do not begin by designing sidebar pages or officer cards. Begin by defining what the system must protect and what organizational work it must make possible.

## Plan index

| Section | Location |
|---------|----------|
| 2. Non-negotiable system laws | [`laws/README.md`](./laws/README.md) |
| 3. Core domain model | [`domain/README.md`](./domain/README.md) |
| 4. Organizational workflows | [`workflows/README.md`](./workflows/README.md) |
| 5. Program modules | [`modules/README.md`](./modules/README.md) |
| 6. Role-specific home screens | [`roles/README.md`](./roles/README.md) |
| 7. Notification architecture | [`notifications/README.md`](./notifications/README.md) |
| 8. Audit architecture | [`audit/README.md`](./audit/README.md) |
| 9. Technical architecture | [`architecture/README.md`](./architecture/README.md) |
| 10. Backend module structure | [`backend/README.md`](./backend/README.md) |
| 11. Build order | [`phases/README.md`](./phases/README.md) |
| 12. MVP | [`phases/MVP.md`](./phases/MVP.md) |
| 13. Phase 0 policy (must decide first) | [`policy/README.md`](./policy/README.md) |

## Design order (enforced)

```
Phase 0 policy
  → Phase 1 foundation (auth, membership, roles, permissions, audit)
    → Phase 2 governance core
      → Phase 3 projects
        → Phase 4 events
          → Phase 5 finance + SGA
            → Phase 6 communications
              → Phase 7 intelligence / automation
```

AI may interpret and assist. AI must never independently approve money, grant roles, modify votes, or publish sensitive communications.
