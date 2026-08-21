# Non-negotiable system laws

These principles are architectural rules. Violating them in code or process is a defect.

## Law 1 — A role is not automatically a permission

“President” is a **position**. Permissions are capabilities, for example:

- `meeting.create`
- `minutes.approve`
- `project.assign_member`
- `finance.request`
- `finance.approve`
- `role.grant`
- `content.publish`

Roles map to permission sets, but the backend must check the **actual permission** for every protected action.

Forbidden:

```text
if user.role == "president":
    allow_everything()
```

Required:

```text
authorize(user, "project.approve", project_scope)
```

See [`../domain/authorization.md`](../domain/authorization.md).

## Law 2 — Every authority must have evidence

No officer receives access merely because someone picked a role from a dropdown.

Every role assignment must contain:

| Field | Purpose |
|-------|---------|
| User | Who receives authority |
| Position | Which office |
| Academic term | Governance period |
| Start date / End date | Validity window |
| Appointment method | Election, appointment, interim, emergency |
| Who nominated | Proposer |
| Who approved | Approver(s) |
| Supporting record | Meeting resolution or election evidence |
| Current status | Proposed → active → expired/suspended/revoked |
| Reason for suspension/revocation | When applicable |

This creates defensible access control.

## Law 3 — Privileged actions require separation of duties

One person must not initiate, approve, and complete the same high-risk action.

Examples:

- Treasurer cannot approve their own reimbursement.
- President cannot grant themselves a new role.
- Social Media Manager cannot independently publish a sensitive statement.
- Project Manager cannot approve their own project proposal.
- Person recording election results cannot silently alter them.
- Advisor may recover access but cannot erase the recovery record.

## Law 4 — History must not disappear

Avoid destructive deletion.

| Instead of delete | Do this |
|-------------------|---------|
| Role assignment | Mark expired or revoked |
| Project | Archive or cancel |
| Meeting minutes | Create a corrected version |
| Transaction | Reverse with another transaction |
| Decision | Supersede through another decision |
| User | Deactivate membership |

Institutional history must survive leadership transitions.

## Law 5 — Every important process is a state machine

Do not store vague statuses such as “almost done” or “working on it”.

Use controlled states. Example:

```text
PROPOSED → UNDER_REVIEW → APPROVED → ACTIVE → COMPLETED → ARCHIVED
```

Each transition must define:

- Who may perform it (permission)
- Preconditions
- Required evidence
- Notification recipients
- Audit entry
- What happens next

Workflow catalogs: [`../workflows/`](../workflows/).

## Law 6 — Completion requires proof

A task does not become completed merely because someone clicks “Done.”

Completion may require (as configured):

- Deliverable attached
- Reviewer assigned
- Acceptance criteria satisfied
- Receipt uploaded
- Minutes approved
- Event report submitted
- Project owner acceptance
- Link to published content

## Law 7 — The backend is the authority

The frontend may hide buttons. Hiding buttons is not security.

Every API operation must independently verify:

1. Identity  
2. Active membership  
3. Permission  
4. Scope  
5. Term  
6. Workflow state  
7. Approval requirements  
8. Conflict of interest (where applicable)  
