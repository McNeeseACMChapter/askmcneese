# Authorization domain

## permissions

Capability strings. Catalog (extend carefully; keep stable codes):

### Members & roles
- `member.view`, `member.edit`
- `role.propose`, `role.approve`, `role.revoke`

### Meetings & governance
- `meeting.create`, `meeting.publish`
- `minutes.edit`, `minutes.approve`
- `motion.create`, `vote.cast`

### Projects & tasks
- `project.create`, `project.approve`, `project.manage`
- `task.assign`

### Finance
- `finance.request`, `finance.review`, `finance.approve`, `finance.reconcile`

### Events & content
- `event.create`, `event.approve`
- `content.draft`, `content.review`, `content.publish`

### System
- `audit.view`
- `admin.configure` (high privilege)

## role_permission_sets

Maps **positions** → default permissions for a term template.

## permission_overrides

Temporary or scoped access. Example: Member A can manage Project AskMcNeese, not all projects.

Every override must have:

| Field | Required |
|-------|----------|
| Subject (membership/user) | yes |
| Permission | yes |
| Scope (resource type + id, or org-wide) | yes |
| Reason | yes |
| Grantor | yes |
| Expiration | yes |
| Audit record | yes |

## Enforcement pattern

```text
authorize(actor, permission_code, scope) -> Allow | Deny(reason)
```

Checks (all must pass):

1. Authenticated identity  
2. Active membership in organization  
3. Effective permissions (role sets ∪ non-expired overrides)  
4. Scope match  
5. Term validity for governance actions  
6. Workflow state allows the transition  
7. Separation-of-duties / conflict rules  
