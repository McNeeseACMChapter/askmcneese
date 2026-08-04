# Workflow transition matrix (Phase 0 draft)

**Status:** DRAFT — documents intended transitions from `askmcneese/acm/workflows/`.  
**Not production code.** Permission keys match [`role-permission-matrix.md`](./role-permission-matrix.md).  
**Failure behavior (default unless noted):** reject transition; leave prior state; emit audit `TRANSITION_DENIED` with actor + reason; notify actor.

Columns for every row:

| Column | Meaning |
|--------|---------|
| From → To | States |
| Required permission | Permission key |
| Preconditions | Must be true |
| Required evidence | Artifacts |
| COI restriction | Conflict of interest |
| Audit event | Event name |
| Notification recipients | Who is notified |
| Failure behavior | On deny / invalid |

---

## 1. Role assignment (`workflows/role-assignment.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → PROPOSED | `role.propose` | Position exists; term open; nominee membership eligible if elected track (GOV-005) | Nominee id, position code, term | Cannot propose self for high-privilege elected office | `ROLE_PROPOSED` | Nominee; Secretary; President | Stay none; notify proposer of denial |
| PROPOSED → EVIDENCE_ATTACHED | (Secretary attach; proposer may attach if allowed) — treat as `role.propose` + records duty | Proposal exists; document type = election result or resolution | Linked document id | — | `ROLE_EVIDENCE_ATTACHED` | Advisor (if high-privilege); President | Remain PROPOSED; flag missing evidence |
| EVIDENCE_ATTACHED → VERIFIED | Advisor verify (high-privilege path); skip/auto-pass non-high-privilege per GOV-018 | Evidence present; Advisor identity confirmed | Verification note | Advisor cannot verify own student nomination as if student officer | `ROLE_VERIFIED` | President; Secretary; nominee | Remain EVIDENCE_ATTACHED; notify President |
| VERIFIED → APPROVED | `role.approve` | Verified (or N/A); GOV-007 | Approver identity | **Approver ≠ nominee**; not sole self-deal | `ROLE_APPROVED` | Nominee; Secretary; Advisor | Remain VERIFIED |
| APPROVED → ACTIVE | System (no org permission) | `start_date` ≤ now; prior APPROVED | Start timestamp | — | `ROLE_ACTIVATED` | Nominee; My Work owners | Remain APPROVED until date |
| ACTIVE → EXPIRED | System | `end_date` passed | Term end | — | `ROLE_EXPIRED` | Former holder; President; Secretary | N/A (system) |
| ACTIVE → SUSPENDED | `role.revoke` CONDITIONAL | GOV-020 process; quorum if board vote | Cause + meeting/emergency record | Cannot suspend solely to seize office | `ROLE_SUSPENDED` | Holder; Advisor; President; Secretary | Remain ACTIVE |
| ACTIVE → REVOKED | `role.revoke` CONDITIONAL | GOV-020 removal; evidence | Cause + vote record | Accused cannot vote on own removal | `ROLE_REVOKED` | Holder; Advisor; Board officers | Remain ACTIVE/SUSPENDED |
| SUSPENDED → ACTIVE (emergency) | `system.emergency_recover` | GOV-019; time-box ≤ 72h; reason | Emergency reason | Cannot erase audit; permanent role still needs GOV-007 | `EMERGENCY_RECOVERY` | President; Secretary; Advisor (actor) | Remain SUSPENDED |
| SUSPENDED → REVOKED | `role.revoke` | GOV-020 | Cause | Same as revoke | `ROLE_REVOKED` | Same as revoke | Remain SUSPENDED |

---

## 2. Meetings & decisions (`workflows/meetings-decisions.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → AGENDA_DRAFT | `meeting.create` | Valid meeting type (GOV-008); creator authorized | Draft agenda body | — | `MEETING_CREATED` | Officers (optional) | No meeting created |
| AGENDA_DRAFT → AGENDA_PUBLISHED | `meeting.publish` | Agenda non-empty; meeting time set | Published agenda version | — | `AGENDA_PUBLISHED` | Active members (GENERAL); Board (EXEC) | Remain DRAFT |
| AGENDA_PUBLISHED → MEETING_IN_PROGRESS | Chair/Secretary operational (President/VP/Secretary ALLOW) | Start time reached or chair opens | Attendance start | — | `MEETING_STARTED` | Attendees list | Remain PUBLISHED |
| MEETING_IN_PROGRESS → MINUTES_DRAFT | `minutes.edit` | Meeting closed/ended | Draft minutes | — | `MINUTES_DRAFTED` | Secretary; President | Remain IN_PROGRESS |
| MINUTES_DRAFT → MINUTES_REVIEW | `minutes.edit` | Draft complete | Draft version id | — | `MINUTES_SUBMITTED_REVIEW` | President; Advisor (optional) | Remain DRAFT |
| MINUTES_REVIEW → MINUTES_APPROVED | `minutes.approve` | Quorum was recorded for binding content (GOV-009) if minutes assert votes | Approver identity; immutable version | Contested minutes: second reader preferred | `MINUTES_APPROVED` | Members (summary); Board | Remain REVIEW |
| MINUTES_APPROVED → ARCHIVED | System / Secretary | Retention policy (GOV-017) | Archive stamp | No destructive purge | `MINUTES_ARCHIVED` | Secretary | Remain APPROVED |

**Embedded decision/vote transitions (same workflow file):**

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| Motion open → Vote open | `motion.create` then chair opens | Meeting IN_PROGRESS; motion seconded if required by GOV-010 | Motion text | — | `MOTION_OPENED` / `VOTE_OPENED` | Meeting attendees | Motion stays draft |
| Vote open → Vote closed (binding) | `vote.cast` (eligible) | Quorum true; eligibility cutoff | Ballot/tally | No vote on own removal; election teller ≠ alter alone | `VOTE_CLOSED` | Secretary; teller | Votes discarded if no quorum; mark INVALID |

---

## 3. Projects (`workflows/projects.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → IDEA / PROPOSAL | `project.create` | Active member | Problem statement | — | `PROJECT_PROPOSED` | PM; President | No project |
| PROPOSAL → SCREENING | President/PM operational | Proposal fields complete | Screening notes | — | `PROJECT_SCREENING` | Proposer | Remain PROPOSAL |
| SCREENING → APPROVED | `project.approve` | Feasible; owner assigned | Approver identity | PM cannot approve own proposal | `PROJECT_APPROVED` | PM; proposer; President | Remain SCREENING / reject to ARCHIVED |
| APPROVED → PLANNING | `project.manage` OWN_SCOPE | Approved | Plan / milestones | — | `PROJECT_PLANNING` | Task assignees | Remain APPROVED |
| PLANNING → ACTIVE | `project.manage` | Plan accepted | Kickoff date | — | `PROJECT_ACTIVE` | Team | Remain PLANNING |
| ACTIVE → AT_RISK \| BLOCKED | `project.manage` | Risk/block noted | Reason | — | `PROJECT_AT_RISK` / `PROJECT_BLOCKED` | President; PM | Remain ACTIVE |
| AT_RISK \| BLOCKED → ACTIVE | `project.manage` | Issue cleared | Clearance note | — | `PROJECT_UNBLOCKED` | Team | Remain prior |
| ACTIVE → REVIEW | `project.manage` | Deliverables submitted | Review packet | — | `PROJECT_REVIEW` | Approver; PM | Remain ACTIVE |
| REVIEW → COMPLETED | `project.approve` or designated closer | Acceptance criteria met | Completion evidence | Closer ≠ sole conflicted beneficiary if graded/credit contested | `PROJECT_COMPLETED` | Team; President | Remain REVIEW |
| COMPLETED → ARCHIVED | System / PM | Retention | Archive stamp | — | `PROJECT_ARCHIVED` | PM | Remain COMPLETED |

---

## 4. Finance (`workflows/finance.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → REQUESTED | `finance.request` | Active member; Phase 5+ policy live | Purpose, amount, category, vendor | — | `FINANCE_REQUESTED` | Treasurer | No request |
| REQUESTED → TREASURER_REVIEW | `finance.review` | Request complete | — | Treasurer ≠ silent self-deal later | `FINANCE_TREASURER_REVIEW` | Requester | Remain REQUESTED |
| TREASURER_REVIEW → BUDGET_VERIFIED | `finance.review` | Budget available or change request | Budget line id | — | `FINANCE_BUDGET_VERIFIED` | President (if next) | Remain REVIEW; alert over-budget |
| BUDGET_VERIFIED → PRESIDENT_APPROVAL | `finance.approve` CONDITIONAL | Threshold requires President (GOV-013) | Approver identity | **Requester ≠ approver** | `FINANCE_PRESIDENT_APPROVAL` | Treasurer; requester | Remain BUDGET_VERIFIED |
| PRESIDENT_APPROVAL → ADVISOR_APPROVAL | `finance.approve` (Advisor) | Threshold requires Advisor | Approver identity | Same SoD | `FINANCE_ADVISOR_APPROVAL` | Treasurer; President | Remain PRESIDENT_APPROVAL |
| ADVISOR_APPROVAL (or prior terminal approve) → PURCHASED | Purchaser authorized (Treasurer CONDITIONAL) | Approval chain complete for amount | Purchase record | Treasurer cannot approve own reimbursement | `FINANCE_PURCHASED` | Requester; Treasurer | Remain last approval state |
| PURCHASED → RECEIPT_SUBMITTED | Requester / Treasurer | Purchase done | Receipt document | — | `FINANCE_RECEIPT_SUBMITTED` | Treasurer | Remain PURCHASED; alert if overdue |
| RECEIPT_SUBMITTED → RECONCILED | `finance.reconcile` | Receipt present | Reconciliation note | Reconciler should not be sole requester without second check | `FINANCE_RECONCILED` | President (optional) | Remain RECEIPT_SUBMITTED |
| RECONCILED → CLOSED | Treasurer close | Receipt + reconcile done | Close stamp | No delete—reverse only | `FINANCE_CLOSED` | Requester; audit export eligible | Block CLOSED if missing receipt |

**Amount change:** any approved-amount edit → re-enter approval chain; audit `FINANCE_AMOUNT_CHANGED`.

---

## 5. Events (`workflows/events.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → IDEA / FEASIBILITY path start | `event.create` | Active / officer | Event concept | — | `EVENT_CREATED` | President | No event |
| → FEASIBILITY_REVIEW | Officers | Concept filed | Feasibility notes | — | `EVENT_FEASIBILITY` | Creator | Remain prior |
| FEASIBILITY_REVIEW → BUDGET_REVIEW | Treasurer path if cost | Feasible | Budget draft | Link finance SoD | `EVENT_BUDGET_REVIEW` | Treasurer | Remain FEASIBILITY |
| BUDGET_REVIEW → APPROVAL_PENDING | Complete budget | Budget ok or waived | — | — | `EVENT_APPROVAL_PENDING` | President; Advisor | Remain BUDGET_REVIEW |
| APPROVAL_PENDING → APPROVED | `event.approve` | Feasibility + budget ok | Approver identity | — | `EVENT_APPROVED` | Creator; Social; SGA if needed | Remain PENDING / REJECT path archive |
| APPROVED → PROMOTION | `content.*` / Social | Approved | Promo plan | Sensitive → GOV-015 | `EVENT_PROMOTION` | Social | Remain APPROVED |
| PROMOTION → REGISTRATION_OPEN | Event owner | Promo ready | Registration config | — | `EVENT_REG_OPEN` | Members | Remain PROMOTION |
| REGISTRATION_OPEN → READY | Checklist complete | Venue/time/staff | Checklist evidence | — | `EVENT_READY` | Officers | Remain REG_OPEN |
| READY → COMPLETED | Event owner | Event occurred | Attendance summary | — | `EVENT_COMPLETED` | President; Secretary | Remain READY |
| COMPLETED → POST_EVENT_REVIEW | Owner | Complete | Lessons learned | — | `EVENT_POST_REVIEW` | Board | Remain COMPLETED |
| POST_EVENT_REVIEW → ARCHIVED | System / Secretary | Review done | Archive stamp | — | `EVENT_ARCHIVED` | Secretary | Remain POST_REVIEW |

---

## 6. Communications (`workflows/communications.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → DRAFT | `content.draft` | Author authorized | Draft body | — | `CONTENT_DRAFTED` | Social (if member draft) | No draft |
| DRAFT → INTERNAL_REVIEW | `content.review` submit | Draft complete | Review request | — | `CONTENT_IN_REVIEW` | Reviewer (Pres/Social/Advisor) | Remain DRAFT |
| INTERNAL_REVIEW → APPROVED | `content.review` | Non-sensitive: designated reviewer; Sensitive: President **or** Advisor (GOV-015) | Approver identity | Social cannot solo-approve sensitive | `CONTENT_APPROVED` | Author | Remain REVIEW |
| APPROVED → SCHEDULED | Social CONDITIONAL | Approved | Schedule time | — | `CONTENT_SCHEDULED` | Author | Remain APPROVED |
| SCHEDULED → PUBLISHED | `content.publish` | Schedule reached or manual publish; sensitive already approved | Published URL | Same sensitive rule | `CONTENT_PUBLISHED` | Officers (optional); archive | Remain SCHEDULED; revoke schedule on policy fail |
| PUBLISHED → ARCHIVED | Social / Secretary | Retention / end of campaign | Archive stamp | — | `CONTENT_ARCHIVED` | Social | Remain PUBLISHED |

---

## 7. SGA (`workflows/sga.md`)

| From → To | Required permission | Preconditions | Required evidence | COI restriction | Audit event | Notification recipients | Failure behavior |
|-----------|---------------------|---------------|-------------------|-----------------|-------------|-------------------------|------------------|
| (none) → DRAFT / intake | SGA Rep operational + `event.create` or dedicated sga draft (treat as officer CONDITIONAL) | Need identified | Packet draft | — | `SGA_DRAFT` | President; Treasurer | No packet |
| → INTERNAL_REVIEW | SGA Rep / President | Packet fields | — | — | `SGA_INTERNAL_REVIEW` | Board | Remain draft |
| INTERNAL_REVIEW → BUDGET_ATTACHED | `finance.review` / Treasurer | Budget numbers | Budget attachment | Finance SoD if spend | `SGA_BUDGET_ATTACHED` | Treasurer; SGA Rep | Remain INTERNAL_REVIEW |
| BUDGET_ATTACHED → ACM_APPROVED | `event.approve` or President/Advisor CONDITIONAL | Internal ok | ACM approver identity | — | `SGA_ACM_APPROVED` | SGA Rep | Remain BUDGET_ATTACHED |
| ACM_APPROVED → SGA_SUBMITTED | SGA Rep | ACM approved | External submission receipt | — | `SGA_SUBMITTED` | President; Treasurer | Remain ACM_APPROVED |
| SGA_SUBMITTED → HEARING | SGA Rep update | Hearing scheduled | Hearing date | — | `SGA_HEARING` | Board | Remain SUBMITTED |
| HEARING → APPROVED \| REJECTED | Record outcome (SGA Rep + Secretary) | Hearing held | External decision evidence | Cannot forge external approval | `SGA_EXTERNAL_APPROVED` / `SGA_EXTERNAL_REJECTED` | Board; Advisor | Remain HEARING until evidence |
| APPROVED → CONDITIONS_TRACKED | SGA Rep / Treasurer | Conditions listed | Conditions checklist | — | `SGA_CONDITIONS` | Treasurer; President | Remain APPROVED |
| CONDITIONS_TRACKED → CLOSEOUT | SGA Rep + Treasurer | Conditions met / rejected closed | Closeout report | — | `SGA_CLOSEOUT` | Board | Remain CONDITIONS_TRACKED |

---

## Cross-cutting rules

1. Every denied transition audits `TRANSITION_DENIED` with permission key and precondition failure.
2. Technical System Administrator has **no** rows granting org approve/publish/finance approve transitions.
3. Emergency paths only via GOV-019 and labeled audit events.
4. Numeric finance thresholds and final quorum numbers remain PROPOSED until GOV-009/013 APPROVED.
