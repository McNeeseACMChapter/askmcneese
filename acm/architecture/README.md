# Recommended technical architecture

Serious internal system — modular monolith first. No microservices at the start.

```text
Frontend (React + TypeScript)   ← acm/frontend
        ↓
API layer (FastAPI preferred for this repo family)
        ↓
Domain services
  Membership · Governance · Projects · Events
  Finance · Communications · Documents · Audit
        ↓
PostgreSQL  (authoritative structured data)
        ↓
Object storage  (receipts, minutes, images, documents)
        ↓
Background worker  (notifications, reports, schedules)
```

## Core infrastructure

| Component | Role |
|-----------|------|
| PostgreSQL | Authoritative structured data |
| Object storage | Documents and evidence files |
| Redis / queue | Notifications, scheduled jobs, reports |
| Institutional auth | McNeese email / SSO when available |
| MFA | Required for privileged officers |
| Policy engine | Permission + scope enforcement |
| Immutable audit log | Append-only |

## Rules

- Business rules live in **services and policies**, not route handlers.
- Frontend may hide controls; API always re-checks (Law 7).
- Keep ACM code under `askmcneese/acm/` — do not couple to AskMcNeese RAG.
