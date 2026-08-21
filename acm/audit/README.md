# Audit architecture

Every privileged action produces an audit event.

## Event fields

- `actor`
- `action`
- `resource_type`
- `resource_id`
- `previous_state`
- `new_state`
- `reason`
- `timestamp`
- `ip` / session information
- `approval_reference` (when applicable)

## Important audited actions

- Login and failed login
- Permission changes
- Role assignment / revocation
- Financial approval
- Transaction correction
- Minutes modification
- Election result entry
- Project closure
- Document access
- Content publication
- Emergency recovery

## Immutability

Audit records must **not** be editable through the normal application.

Prefer append-only table or separately protected storage.
