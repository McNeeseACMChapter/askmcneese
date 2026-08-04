# Role assignment workflow

```text
PROPOSED
  → EVIDENCE_ATTACHED
  → VERIFIED
  → APPROVED
  → ACTIVE
  → EXPIRED | SUSPENDED | REVOKED
```

## Recommended process

1. President or authorized officer proposes an appointment.
2. Secretary attaches election results or meeting resolution.
3. Advisor verifies high-privilege positions.
4. System activates access.
5. Access expires automatically at end of term.
6. All changes remain in audit history.

Advisor emergency recovery is allowed but must be labeled and permanently logged (cannot be erased).

## Transition notes

| From → To | Who | Evidence |
|-----------|-----|----------|
| → PROPOSED | `role.propose` | Nominee identity, position, term |
| → EVIDENCE_ATTACHED | Secretary / proposer | Election record or resolution |
| → VERIFIED | Advisor (high privilege) | Verification note |
| → APPROVED | `role.approve` (not self) | Approval actor |
| → ACTIVE | System | Start date reached + approved |
| → EXPIRED | System | End of term |
| → SUSPENDED / REVOKED | Authorized + reason | Mandatory reason + audit |
