# Role → permission matrix (Phase 0 draft)

**Status:** DRAFT — not live policy until Phase 0 decisions are `APPROVED`.  
**Do not use** a broad `admin.*` permission. Technical System Administrator ≠ organizational approver.

## Legend

| Value | Meaning |
|-------|---------|
| ALLOW | Default grant for that role’s active assignment |
| DENY | Not granted by default |
| CONDITIONAL | Allowed only if listed preconditions + SoD rules pass |
| OWN_SCOPE_ONLY | Allowed only on resources the actor owns / is assigned |

Roles: **Advisor**, **President**, **Vice President**, **Treasurer**, **Secretary**, **Project Manager**, **SGA Representative**, **Social Media Manager**, **General Member**, **Technical System Administrator** (Tech SA).

---

## Permission catalog

For each permission: key, description, resource, scope, role defaults, preconditions, SoD, evidence, audit.

### member.view

| Field | Value |
|-------|--------|
| Permission key | `member.view` |
| Description | View member directory fields allowed by data classification |
| Resource | membership / user profile |
| Scope | organization |
| Role default | Advisor ALLOW; President ALLOW; VP ALLOW; Treasurer ALLOW; Secretary ALLOW; PM ALLOW; SGA ALLOW; Social ALLOW; Member ALLOW; Tech SA DENY (no org directory by default) |
| Preconditions | Active membership (except Tech SA N/A); classification MEMBER+ |
| SoD restriction | — |
| Evidence requirement | — |
| Audit requirement | Optional for bulk export; required for RESTRICTED field access |

### member.edit

| Field | Value |
|-------|--------|
| Permission key | `member.edit` |
| Description | Edit membership profile / standing fields |
| Resource | membership |
| Scope | organization or own profile |
| Role default | Advisor CONDITIONAL; President CONDITIONAL; Secretary ALLOW; others OWN_SCOPE_ONLY for own non-standing fields; Tech SA DENY |
| Preconditions | Not editing own `good_standing` / high-privilege flags without second actor |
| SoD restriction | Actor cannot alone restore good_standing after disciplinary suspension |
| Evidence requirement | Reason for standing changes |
| Audit requirement | Required |

### role.propose

| Field | Value |
|-------|--------|
| Permission key | `role.propose` |
| Description | Propose a role assignment |
| Resource | role_assignment |
| Scope | organization |
| Role default | President ALLOW; Secretary ALLOW; Advisor CONDITIONAL; others DENY; Tech SA DENY |
| Preconditions | GOV-007; nominee eligible if elected track |
| SoD restriction | Cannot propose self for high-privilege elected office |
| Evidence requirement | Nominee, position, term |
| Audit requirement | Required |

### role.approve

| Field | Value |
|-------|--------|
| Permission key | `role.approve` |
| Description | Approve a proposed role assignment |
| Resource | role_assignment |
| Scope | organization |
| Role default | Advisor ALLOW (verify/approve high-privilege); President CONDITIONAL; others DENY; Tech SA DENY |
| Preconditions | Evidence attached; Advisor verified if high-privilege |
| SoD restriction | **Cannot approve own assignment**; cannot approve if sole proposer without second officer when policy requires |
| Evidence requirement | Approval identity |
| Audit requirement | Required |

### role.revoke

| Field | Value |
|-------|--------|
| Permission key | `role.revoke` |
| Description | Suspend or revoke an active assignment |
| Resource | role_assignment |
| Scope | organization |
| Role default | Advisor CONDITIONAL; President CONDITIONAL; Secretary CONDITIONAL (records); others DENY; Tech SA DENY |
| Preconditions | GOV-020 process satisfied |
| SoD restriction | Cannot revoke solely to seize same office for self |
| Evidence requirement | Cause + meeting/emergency record |
| Audit requirement | Required always |

### meeting.create / meeting.publish

| Field | Value |
|-------|--------|
| Permission key | `meeting.create` / `meeting.publish` |
| Description | Create meeting; publish agenda |
| Resource | meeting |
| Scope | organization / committee |
| Role default | President ALLOW; VP ALLOW; Secretary ALLOW; Advisor CONDITIONAL; committee chairs OWN_SCOPE_ONLY; Member DENY; Tech SA DENY |
| Preconditions | Valid term; meeting type per GOV-008 |
| SoD restriction | — |
| Evidence requirement | — |
| Audit requirement | Publish = required |

### minutes.edit / minutes.approve

| Field | Value |
|-------|--------|
| Permission key | `minutes.edit` / `minutes.approve` |
| Description | Edit draft minutes; approve minutes version |
| Resource | minutes |
| Scope | meeting |
| Role default | edit: Secretary ALLOW; President CONDITIONAL; approve: Secretary CONDITIONAL; President ALLOW; Advisor ALLOW; others DENY; Tech SA DENY |
| Preconditions | Meeting past IN_PROGRESS for approve |
| SoD restriction | Approver should not be sole author without second reader when contested (PROPOSED) |
| Evidence requirement | Approved version immutable except new version |
| Audit requirement | Approve = required |

### motion.create / vote.cast

| Field | Value |
|-------|--------|
| Permission key | `motion.create` / `vote.cast` |
| Description | Create motion; cast vote |
| Resource | motion / vote |
| Scope | meeting |
| Role default | motion: President/VP/Secretary ALLOW; members CONDITIONAL if GENERAL meeting; vote: active eligible members ALLOW; Tech SA DENY |
| Preconditions | Quorum for binding vote (GOV-009); eligibility (GOV-005/011) |
| SoD restriction | No vote on own removal (GOV-020); election teller rules |
| Evidence requirement | Tally retained |
| Audit requirement | Binding votes required |

### project.create / project.approve / project.manage / task.assign

| Field | Value |
|-------|--------|
| Permission key | `project.create` / `project.approve` / `project.manage` / `task.assign` |
| Description | Propose/create project; approve; manage approved; assign tasks |
| Resource | project / task |
| Scope | organization or project |
| Role default | create: Member ALLOW (proposal); President/VP/PM ALLOW; approve: President/Advisor ALLOW; manage: PM OWN_SCOPE_ONLY; President CONDITIONAL; task.assign: PM OWN_SCOPE_ONLY; Tech SA DENY |
| Preconditions | Approve ≠ manage entire chapter |
| SoD restriction | PM cannot approve own proposal |
| Evidence requirement | Proposal fields; acceptance criteria for complete |
| Audit requirement | approve / complete required |

### finance.request / finance.review / finance.approve / finance.reconcile

| Field | Value |
|-------|--------|
| Permission key | `finance.request` / `finance.review` / `finance.approve` / `finance.reconcile` |
| Description | Request spend; treasurer review; approve; reconcile |
| Resource | finance_request / transaction |
| Scope | organization / own request |
| Role default | request: Member+ officers ALLOW (own); review: Treasurer ALLOW; approve: Treasurer/President/Advisor CONDITIONAL by GOV-013; reconcile: Treasurer ALLOW; Tech SA DENY |
| Preconditions | Phase 5+ only; budgets exist |
| SoD restriction | **Requester ≠ approver**; Treasurer ≠ approve own reimbursement (GOV-014) |
| Evidence requirement | Receipt before CLOSED |
| Audit requirement | All approve/reconcile/reverse required |

### event.create / event.approve

| Field | Value |
|-------|--------|
| Permission key | `event.create` / `event.approve` |
| Description | Create event proposal; approve event |
| Resource | event |
| Scope | organization |
| Role default | create: officers ALLOW; Member CONDITIONAL; approve: President/Advisor CONDITIONAL; Tech SA DENY |
| Preconditions | Feasibility/budget as workflow |
| SoD restriction | — |
| Evidence requirement | Checklist completion for READY |
| Audit requirement | approve required |

### content.draft / content.review / content.publish

| Field | Value |
|-------|--------|
| Permission key | `content.draft` / `content.review` / `content.publish` |
| Description | Draft; review; publish communications |
| Resource | content_post |
| Scope | organization / campaign |
| Role default | draft: Social ALLOW; Member OWN_SCOPE_ONLY; review: President/Social/Advisor CONDITIONAL; publish: Social CONDITIONAL (non-sensitive); President/Advisor CONDITIONAL (sensitive GOV-015); Tech SA DENY |
| Preconditions | Sensitive → President or Advisor |
| SoD restriction | Social cannot solo-publish sensitive |
| Evidence requirement | Approver identity; published URL |
| Audit requirement | publish required |

### audit.view / audit.export

| Field | Value |
|-------|--------|
| Permission key | `audit.view` / `audit.export` |
| Description | View audit trail; export audit packages |
| Resource | audit_event |
| Scope | organization |
| Role default | view: Advisor ALLOW; President ALLOW; Secretary ALLOW; Treasurer CONDITIONAL (finance subset); export: Advisor CONDITIONAL; President CONDITIONAL; Tech SA CONDITIONAL (technical logs only, not org approval forgery); Member DENY |
| Preconditions | GOV-016 classification |
| SoD restriction | Exporters cannot delete/alter audit |
| Evidence requirement | Export reason |
| Audit requirement | Meta-audit on export |

### system.configure

| Field | Value |
|-------|--------|
| Permission key | `system.configure` |
| Description | Configure integrations, term templates, non-org technical settings |
| Resource | system_config |
| Scope | organization technical |
| Role default | Tech SA ALLOW; Advisor CONDITIONAL; President DENY for raw infra; others DENY |
| Preconditions | Does **not** include organizational approval powers |
| SoD restriction | Tech SA cannot approve roles/finance/minutes via this key |
| Evidence requirement | Change ticket / reason |
| Audit requirement | Required |

### system.emergency_recover / system.account_recover

| Field | Value |
|-------|--------|
| Permission key | `system.emergency_recover` / `system.account_recover` |
| Description | Advisor emergency org recovery; Tech SA account/auth recovery |
| Resource | role_assignment / user_account |
| Scope | organization |
| Role default | emergency_recover: Advisor ALLOW; account_recover: Tech SA ALLOW; others DENY |
| Preconditions | GOV-019; reason; time-box |
| SoD restriction | Cannot erase recovery audit; Tech SA cannot grant org approvals |
| Evidence requirement | Reason + notifications |
| Audit requirement | Required (immutable) |

---

## Compact role matrix

Values: A = ALLOW, D = DENY, C = CONDITIONAL, O = OWN_SCOPE_ONLY

| Permission | Adv | Pres | VP | Treas | Sec | PM | SGA | Social | Mem | Tech SA |
|------------|-----|------|----|-------|-----|----|-----|--------|-----|---------|
| member.view | A | A | A | A | A | A | A | A | A | D |
| member.edit | C | C | D | D | A | D | D | D | O | D |
| role.propose | C | A | D | D | A | D | D | D | D | D |
| role.approve | A | C | D | D | D | D | D | D | D | D |
| role.revoke | C | C | D | D | C | D | D | D | D | D |
| meeting.create | C | A | A | D | A | D | D | D | D | D |
| meeting.publish | C | A | A | D | A | D | D | D | D | D |
| minutes.edit | D | C | D | D | A | D | D | D | D | D |
| minutes.approve | A | A | D | D | C | D | D | D | D | D |
| motion.create | C | A | A | D | A | D | D | D | C | D |
| vote.cast | C | A | A | A | A | A | A | A | A | D |
| project.create | C | A | A | D | D | A | D | D | A | D |
| project.approve | A | A | D | D | D | D | D | D | D | D |
| project.manage | C | C | D | D | D | O | D | D | D | D |
| task.assign | D | C | D | D | D | O | D | D | D | D |
| finance.request | C | A | A | A | A | A | A | D | A | D |
| finance.review | D | D | D | A | D | D | D | D | D | D |
| finance.approve | C | C | D | C | D | D | D | D | D | D |
| finance.reconcile | D | D | D | A | D | D | D | D | D | D |
| event.create | C | A | A | D | D | C | D | C | C | D |
| event.approve | C | A | D | D | D | D | D | D | D | D |
| content.draft | C | C | D | D | D | D | D | A | O | D |
| content.review | A | A | D | D | D | D | D | C | D | D |
| content.publish | C | C | D | D | D | D | D | C | D | D |
| audit.view | A | A | D | C | A | D | D | D | D | C |
| audit.export | C | C | D | D | D | D | D | D | D | C |
| system.configure | C | D | D | D | D | D | D | D | D | A |
| system.emergency_recover | A | D | D | D | D | D | D | D | D | D |
| system.account_recover | D | D | D | D | D | D | D | D | D | A |

**Tech SA note:** May keep systems running and recover accounts; must not auto-receive `role.approve`, `finance.approve`, `minutes.approve`, or `content.publish`.
