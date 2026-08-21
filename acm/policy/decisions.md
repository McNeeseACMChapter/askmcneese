# Policy decisions log — Phase 0

**Package status:** DRAFT  
**Policy version:** see [`VERSION`](./VERSION) (`0.1.0-draft`)  
**Rule:** Nothing in this file is `APPROVED` unless authorized chapter leadership records approval evidence. All GOV records below are `PROPOSED` working drafts for meeting debate.

**Allowed statuses:** `UNRESOLVED` | `PROPOSED` | `UNDER_REVIEW` | `APPROVED` | `SUPERSEDED` | `REJECTED`

**Related:** [`phase-0-review.md`](./phase-0-review.md) · [`role-permission-matrix.md`](./role-permission-matrix.md) · [`workflow-transition-matrix.md`](./workflow-transition-matrix.md)

---

## Inventory summary (discovery)

| Category | Finding |
|----------|---------|
| Already decided (binding) | **None.** No APPROVED governance records with leadership evidence exist in-repo. |
| Architectural laws (non-decision, binding design constraints) | Laws 1–7 in `laws/README.md` — treat as engineering constraints, not chapter-approved bylaws. |
| Unresolved | All GOV-001…GOV-020; all 12 items in `policy/README.md` “Must decide”. |
| Contradictions | See GOV notes and `phase-0-review.md` §4. |
| Duplications | Position list in `domain/structure.md` ↔ draft matrix roles; Phase 0 checklist in `policy/README.md` ↔ this file; SoD rules in laws ↔ finance workflow. |
| Assumptions stated as process | Role workflow “President proposes / Secretary attaches / Advisor verifies”; finance chain; sensitive content “President or Advisor”; MFA for privileged officers. |
| Blocks Phase 1 | Election method, quorum, role authority, permission ownership, officer removal, audit ownership, emergency recovery (and related GOV IDs below). |

---

## Decision record template

```text
### GOV-XXX — Title
- Decision ID:
- Title:
- Status:
- Proposed rule:
- Alternatives:
- Rationale:
- Systems affected:
- Permissions affected:
- Workflows affected:
- Evidence required:
- Approval authority:
- Effective date:
- Superseded decision:
```

---

### GOV-001 — Official officer titles

- **Decision ID:** GOV-001  
- **Title:** Official officer titles  
- **Status:** PROPOSED  
- **Proposed rule:** Official titled positions for McNeese ACM Student Chapter are exactly: Faculty Advisor; President; Vice President; Treasurer; Secretary; Project Manager; SGA Representative; Social Media Manager. Display names and stable codes: `advisor`, `president`, `vice_president`, `treasurer`, `secretary`, `project_manager`, `sga_representative`, `social_media_manager`.  
- **Alternatives:** (A) Add Webmaster / Membership Chair / Events Chair as titled officers; (B) Collapse Project Manager into Vice President; (C) Use only Executive Board titles (Pres/VP/Treas/Sec) and treat others as committee leads.  
- **Rationale:** Matches current domain/structure and role homes; keeps titled offices finite for permission sets.  
- **Systems affected:** `positions`, role assignments, My Work homes, reporting.  
- **Permissions affected:** All role_permission_sets keyed by position code.  
- **Workflows affected:** Role assignment; succession; elections.  
- **Evidence required:** Constitution/bylaws excerpt or executive board resolution listing titles.  
- **Approval authority:** Executive Board vote; Faculty Advisor acknowledgment for Advisor title definition.  
- **Effective date:** TBD (upon APPROVED).  
- **Superseded decision:** —  

---

### GOV-002 — Position types

- **Decision ID:** GOV-002  
- **Title:** Position types  
- **Status:** PROPOSED  
- **Proposed rule:** Positions are typed as: `FACULTY` (Advisor); `ELECTED_OFFICER` (President, VP, Treasurer, Secretary, SGA Representative); `APPOINTED_OFFICER` (Project Manager, Social Media Manager); `COMMITTEE_ROLE` (non-titled committee leads, not automatic org-wide permissions). Only FACULTY / ELECTED / APPOINTED create org-wide role_permission_sets.  
- **Alternatives:** (A) All non-Advisor positions elected; (B) All non-Advisor positions appointed by President; (C) No type distinction—every position treated identically.  
- **Rationale:** Separates election vs appointment evidence (Law 2) and Advisor verification for high privilege.  
- **Systems affected:** `positions.is_high_privilege`, appointment_method enum.  
- **Permissions affected:** Which positions receive which default sets; Advisor verify gate.  
- **Workflows affected:** Role assignment (election vs appointment branches).  
- **Evidence required:** Bylaws clause or board resolution on election vs appointment.  
- **Approval authority:** Executive Board; Advisor for FACULTY type rules.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-003 — Officer terms

- **Decision ID:** GOV-003  
- **Title:** Officer terms  
- **Status:** PROPOSED  
- **Proposed rule:** Primary governance term is **academic year** (e.g., 2026–2027) with optional semester sub-terms for reporting. Elected/appointed officer assignments default `start_date` = term start, `end_date` = term end. System auto-transitions ACTIVE → EXPIRED at `end_date` 23:59 America/Chicago. Mid-year appointments end at the same term end unless interim succession specifies otherwise.  
- **Alternatives:** (A) Semester-only terms (Fall/Spring separate elections); (B) Calendar-year terms; (C) Staggered terms (e.g., Treasurer 2 years).  
- **Rationale:** Aligns with student leadership cycles; enables automatic access expiry (Law 2).  
- **Systems affected:** `terms`, role_assignments, notifications (14-day expiry warning).  
- **Permissions affected:** Term-scoped authorization checks.  
- **Workflows affected:** Role assignment ACTIVE→EXPIRED; succession.  
- **Evidence required:** Board resolution defining term calendar for current year.  
- **Approval authority:** Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-004 — Vacancy and succession

- **Decision ID:** GOV-004  
- **Title:** Vacancy and succession  
- **Status:** PROPOSED  
- **Proposed rule:** If President becomes vacant: Vice President becomes Interim President (time-bounded assignment, evidence = vacancy record) until special election or board appointment per GOV-006/007. Other vacancies: President proposes interim; Secretary attaches resolution; Advisor verifies if high-privilege; no self-appointment. Interim assignments must set explicit end date ≤ term end.  
- **Alternatives:** (A) Immediate special election for all vacancies; (B) Advisor fills interim presidential duties without VP succession; (C) Leave vacant until next regular election.  
- **Rationale:** Continuity without silent privilege expansion.  
- **Systems affected:** role_assignments, notifications, My Work (President/VP).  
- **Permissions affected:** Interim inherits position permission set for duration only.  
- **Workflows affected:** Role assignment; officer removal.  
- **Evidence required:** Vacancy notice + meeting minutes/resolution.  
- **Approval authority:** Executive Board for permanent fill; Advisor verify for high-privilege interims.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-005 — Election eligibility

- **Decision ID:** GOV-005  
- **Title:** Election eligibility  
- **Status:** PROPOSED  
- **Proposed rule:** To stand for ELECTED_OFFICER: active membership (GOV-011), good standing, McNeese student status for student offices, and any ACM international membership requirement the chapter adopts. Faculty Advisor is not elected. Voters: active members in good standing as of a published eligibility cutoff before the election.  
- **Alternatives:** (A) Any enrolled McNeese student may vote without ACM membership; (B) Officers must hold national ACM membership; (C) GPA minimum for candidates.  
- **Rationale:** Ties franchise to membership definition; blocks Phase 1 role automation until clear.  
- **Systems affected:** memberships, elections module (Phase 2), role evidence.  
- **Permissions affected:** `vote.cast` eligibility.  
- **Workflows affected:** Elections; role assignment EVIDENCE_ATTACHED.  
- **Evidence required:** Bylaws eligibility clause; published cutoff for each election.  
- **Approval authority:** Executive Board; Advisor acknowledgment if university org rules apply.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-006 — Election method

- **Decision ID:** GOV-006  
- **Title:** Election method  
- **Status:** PROPOSED  
- **Proposed rule:** Regular elections use secret ballot (paper or approved digital tool). Winner = simple majority of valid votes cast; if no majority, runoff between top two. Election Committee (or Secretary + independent teller who is not a candidate) records results. Person recording results cannot unilaterally alter them (Law 3). Results become evidence documents linked to role_assignments.  
- **Alternatives:** (A) Plurality without runoff; (B) Ranked-choice; (C) Unanimous consent / voice vote for uncontested seats only.  
- **Rationale:** Deterministic evidence for Law 2; **blocking for Phase 1** if roles can be “elected” without method.  
- **Systems affected:** elections records, documents, role assignment.  
- **Permissions affected:** election record create/edit (split from alter).  
- **Workflows affected:** Role assignment (election path).  
- **Evidence required:** Ballot tally sheet / export + minutes recognizing results.  
- **Approval authority:** Executive Board adopts method; Election Committee executes.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-007 — Appointment workflow

- **Decision ID:** GOV-007  
- **Title:** Appointment workflow  
- **Status:** PROPOSED  
- **Proposed rule:** APPOINTED_OFFICER and interim fills follow: PROPOSED (`role.propose`) → EVIDENCE_ATTACHED (resolution) → VERIFIED (Advisor if `is_high_privilege`) → APPROVED (`role.approve`, not self) → ACTIVE. President may propose; Secretary may attach evidence; Approver cannot be nominee.  
- **Alternatives:** (A) President alone appoints without board; (B) Full board vote required for every appointment; (C) Advisor must approve all appointments.  
- **Rationale:** Codifies existing workflow draft with SoD.  
- **Systems affected:** role_assignments, permissions.  
- **Permissions affected:** `role.propose`, `role.approve`, Advisor verify capability.  
- **Workflows affected:** Role assignment.  
- **Evidence required:** Meeting resolution or written appointment with approver identity.  
- **Approval authority:** Per position type (board vs President)—**must be chosen in meeting**.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-008 — Meeting types

- **Decision ID:** GOV-008  
- **Title:** Meeting types  
- **Status:** PROPOSED  
- **Proposed rule:** Meeting types: `GENERAL` (open to members); `EXECUTIVE_BOARD`; `COMMITTEE`; `SPECIAL` (called for a stated purpose); `ELECTION`. Quorum and voting rules may differ by type (see GOV-009/010). Only GENERAL and EXECUTIVE_BOARD may create chapter-binding decisions unless bylaws delegate.  
- **Alternatives:** (A) Only two types (General / Board); (B) Informal “standups” as meetings without quorum; (C) Committee meetings never bind chapter.  
- **Rationale:** Prevents informal chats from becoming fake official decisions.  
- **Systems affected:** meetings module.  
- **Permissions affected:** `meeting.create`, `meeting.publish` by type.  
- **Workflows affected:** Meetings & decisions.  
- **Evidence required:** Bylaws meeting classification.  
- **Approval authority:** Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-009 — Quorum

- **Decision ID:** GOV-009  
- **Title:** Quorum  
- **Status:** PROPOSED  
- **Proposed rule:** GENERAL meeting quorum = majority of active members present **or** a fixed minimum (chapter must pick one). PROPOSED default for debate: **greater of 5 active members or 25% of active members**. EXECUTIVE_BOARD quorum = majority of currently filled elected/appointed officer seats (Advisor optional for quorum unless university requires). No binding vote without quorum recorded.  
- **Alternatives:** (A) Fixed number only (e.g., 7); (B) Majority of all active members (hard online); (C) Board quorum = 3 officers including President or VP.  
- **Rationale:** **Blocking for Phase 1/2** — without quorum, minutes/votes cannot be authoritative.  
- **Systems affected:** meetings attendance, vote validity.  
- **Permissions affected:** `vote.cast` counted only if quorum true.  
- **Workflows affected:** Meetings; elections.  
- **Evidence required:** Bylaws quorum clause.  
- **Approval authority:** Executive Board; Advisor if required by university org policy.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-010 — Voting rules

- **Decision ID:** GOV-010  
- **Title:** Voting rules  
- **Status:** PROPOSED  
- **Proposed rule:** Ordinary motions: majority of votes cast (yes/no), abstentions not counted in denominator. Constitutional/bylaw amendments: 2/3 of votes cast with quorum present. Officer removal: see GOV-020. Secret ballot required for elections and removal; other votes may be open unless requested secret by any member. Proxy voting: **DENY** unless later APPROVED.  
- **Alternatives:** (A) Allow proxies; (B) Unanimous consent for routine items; (C) President breaks all ties vs re-vote.  
- **Rationale:** **Blocking** for governance core.  
- **Systems affected:** motions, votes, decisions.  
- **Permissions affected:** `motion.create`, `vote.cast`.  
- **Workflows affected:** Meetings; elections; removal.  
- **Evidence required:** Bylaws voting section.  
- **Approval authority:** Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-011 — Active-member definition

- **Decision ID:** GOV-011  
- **Title:** Active-member definition  
- **Status:** PROPOSED  
- **Proposed rule:** Active member = membership status `active` AND good_standing = true AND (for student members) currently affiliated with McNeese for the term, AND has completed chapter onboarding checklist (to be defined). Inactive = graduated, resigned, removed, or failed standing criteria. Only active members receive `member.*` baseline privileges (GOV-012).  
- **Alternatives:** (A) Dues-paid only; (B) Attendance-based (N meetings/semester); (C) Self-declared Discord members count as active.  
- **Rationale:** Foundation for authorization checks (Law 7 step 2). **Blocking for Phase 1.**  
- **Systems affected:** memberships, all authorize() calls.  
- **Permissions affected:** Baseline member set.  
- **Workflows affected:** All.  
- **Evidence required:** Written membership policy approved by board.  
- **Approval authority:** Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-012 — Member privileges

- **Decision ID:** GOV-012  
- **Title:** Member privileges  
- **Status:** PROPOSED  
- **Proposed rule:** Active general members may: view member directory (non-sensitive fields); view published agendas/minutes; create project ideas/proposals; request finance (own requests); draft content for review; receive My Work tasks; vote when eligible; volunteer for events. Members may **not**: approve roles, approve finance, publish sensitive content, edit others’ minutes, export full audit logs, or grant permissions.  
- **Alternatives:** (A) Members cannot create finance requests; (B) Members see all financial detail; (C) Members can publish social posts without review.  
- **Rationale:** Least privilege; matches MVP spirit.  
- **Systems affected:** permission defaults for General Member.  
- **Permissions affected:** See matrix rows for General Member.  
- **Workflows affected:** Project IDEA/PROPOSAL; finance REQUESTED; content DRAFT.  
- **Evidence required:** Board approval of member bill of rights / privileges.  
- **Approval authority:** Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-013 — Spending thresholds

- **Decision ID:** GOV-013  
- **Title:** Spending thresholds  
- **Status:** PROPOSED  
- **Proposed rule (numeric placeholders for debate):**  
  - ≤ $50: Treasurer review + budget verify; President approval optional if pre-budgeted miscellaneous.  
  - $50.01–$250: Treasurer + President.  
  - $250.01–$1,000: Treasurer + President + Advisor.  
  - > $1,000: above + Executive Board motion.  
  Dollar amounts are **PROPOSED placeholders** until Treasurer + Advisor set real limits.  
- **Alternatives:** (A) Any spend needs Advisor; (B) Single threshold $100; (C) Follow SGA rules only.  
- **Rationale:** Enables finance workflow gates; not required to code in Phase 1 but must be decided before Phase 5. Non-blocking for Phase 1 foundation **if** finance APIs are not built.  
- **Systems affected:** finance approvals.  
- **Permissions affected:** `finance.approve` CONDITIONAL by amount.  
- **Workflows affected:** Finance.  
- **Evidence required:** Budget policy + Advisor acknowledgment.  
- **Approval authority:** Treasurer proposes; Executive Board adopts; Advisor for university compliance.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-014 — Financial conflicts and separation of duties

- **Decision ID:** GOV-014  
- **Title:** Financial conflicts and separation of duties  
- **Status:** PROPOSED  
- **Proposed rule:** Requester ≠ approver for the same request. Treasurer cannot approve own reimbursement. Approved amount changes require re-approval chain and audit. No delete of transactions—only reverse. Missing receipt blocks CLOSED. Same person cannot alone complete REQUESTED→CLOSED.  
- **Alternatives:** (A) Allow President to solo-approve under $X emergency with post-audit; (B) Dual control always including Advisor.  
- **Rationale:** Law 3; **blocking for Phase 5**; recommended as APPROVED-intent before any finance code. Not blocking Phase 1 if finance not implemented.  
- **Systems affected:** finance service/policy.  
- **Permissions affected:** `finance.approve`, `finance.reconcile`.  
- **Workflows affected:** Finance.  
- **Evidence required:** Financial SoD policy.  
- **Approval authority:** Treasurer + President + Advisor.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-015 — Sensitive communications

- **Decision ID:** GOV-015  
- **Title:** Sensitive communications  
- **Status:** PROPOSED  
- **Proposed rule:** “Sensitive” includes: statements on university policy/controversy; crisis/safety; elections; finance/fundraising claims; personal data; legal accusations; anything Advisor or President flags. Sensitive content requires `content.review` by President **or** Advisor before `content.publish`. Social Media Manager may draft and schedule non-sensitive content after INTERNAL_REVIEW by any designated reviewer.  
- **Alternatives:** (A) All posts need President; (B) Social Media Manager full autonomy; (C) Advisor must approve all external posts.  
- **Rationale:** Codifies communications workflow assumption. Non-blocking for Phase 1; blocking for Phase 6.  
- **Systems affected:** communications.  
- **Permissions affected:** `content.publish` CONDITIONAL.  
- **Workflows affected:** Communications.  
- **Evidence required:** Communications policy.  
- **Approval authority:** President + Social Media Manager draft; Advisor for university brand/risk.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-016 — Data classification

- **Decision ID:** GOV-016  
- **Title:** Data classification  
- **Status:** PROPOSED  
- **Proposed rule:** Classes: `PUBLIC` (published posts, public event info); `MEMBER` (rosters, non-sensitive minutes); `OFFICER` (executive sessions, draft budgets); `RESTRICTED` (receipts with account numbers, personal contact private fields, emergency recovery logs, raw audit exports); `FACULTY_CONFIDENTIAL` (Advisor-only notes). Access by classification + permission.  
- **Alternatives:** (A) Two-tier Public/Private only; (B) Follow university data classification scheme verbatim.  
- **Rationale:** Needed for documents module and audit export control. **Blocking for Phase 1** audit export design.  
- **Systems affected:** documents, audit, members directory.  
- **Permissions affected:** `audit.view`, `audit.export`, `member.view` field masks.  
- **Workflows affected:** Documents; Admin & Audit.  
- **Evidence required:** Data handling policy.  
- **Approval authority:** Advisor + Secretary (records) + President.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-017 — Data retention

- **Decision ID:** GOV-017  
- **Title:** Data retention  
- **Status:** PROPOSED  
- **Proposed rule:** Governance records (minutes, decisions, role assignments, election evidence): retain ≥ 7 years or while chapter exists, whichever longer. Financial evidence: ≥ 7 years. Audit log: retain ≥ 7 years, append-only. Soft-deleted/deactivated users: retain membership history; scrub authentication secrets on deactivate. Public social metrics: retain ≥ 2 years. No destructive purge of APPROVED minutes.  
- **Alternatives:** (A) 3-year retention; (B) Follow university student-org retention schedule if stricter.  
- **Rationale:** Law 4; leadership transition memory. **Blocking for Phase 1** storage design choices.  
- **Systems affected:** documents, audit, object storage.  
- **Permissions affected:** retention jobs (system), not officer delete.  
- **Workflows affected:** All archive paths.  
- **Evidence required:** Retention policy + Advisor/university alignment.  
- **Approval authority:** Advisor + Executive Board.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-018 — Privileged roles

- **Decision ID:** GOV-018  
- **Title:** Privileged roles  
- **Status:** PROPOSED  
- **Proposed rule:** High-privilege positions (`is_high_privilege=true`): Faculty Advisor, President, Treasurer, Secretary (records), and Technical System Administrator (technical only). High-privilege role activation requires Advisor VERIFIED step except Advisor’s own university-confirmed appointment. MFA required at login for users holding any high-privilege active assignment (architecture assumption → chapter should confirm).  
- **Alternatives:** (A) Only Advisor+President+Treasurer; (B) All officers high-privilege; (C) No MFA mandate.  
- **Rationale:** **Blocking for Phase 1** permission ownership and auth hardening.  
- **Systems affected:** identity, authorization, role assignment verify gate.  
- **Permissions affected:** who may hold `role.approve`, `finance.approve`, `audit.export`, `system.*`.  
- **Workflows affected:** Role assignment VERIFIED.  
- **Evidence required:** Security/privilege policy.  
- **Approval authority:** Advisor + President.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-019 — Emergency recovery

- **Decision ID:** GOV-019  
- **Title:** Emergency recovery  
- **Status:** PROPOSED  
- **Proposed rule:** Faculty Advisor may perform emergency access recovery to restore chapter continuity (unlock lockout, temporary role reactivation ≤ 72 hours). Every emergency action: labeled `EMERGENCY_RECOVERY`, immutable audit, reason required, notify President + Secretary, cannot erase audit, cannot silently grant permanent roles without GOV-007 afterward. Technical System Administrator may restore **technical** access (auth/account) but **cannot** grant organizational approvals or finance authority.  
- **Alternatives:** (A) President also has emergency recovery; (B) Dual Advisor+President required; (C) University IT only.  
- **Rationale:** Law 3 Advisor clause; **blocking for Phase 1.**  
- **Systems affected:** identity, authorization, audit, notifications.  
- **Permissions affected:** `system.emergency_recover` (Advisor); `system.account_recover` (Tech SA).  
- **Workflows affected:** Role assignment SUSPENDED→ACTIVE (emergency path).  
- **Evidence required:** Written emergency protocol.  
- **Approval authority:** Faculty Advisor owns protocol; Board informed.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

### GOV-020 — Officer removal and suspension

- **Decision ID:** GOV-020  
- **Title:** Officer removal and suspension  
- **Status:** PROPOSED  
- **Proposed rule:** Suspension: Executive Board majority with quorum + written cause → status SUSPENDED (permissions paused, history kept). Removal: 2/3 votes cast with quorum, secret ballot, accused may speak, cannot vote on own removal. Advisor may recommend suspension for safety/compliance; permanent removal still needs board process unless university mandates otherwise. Revocation produces audit + reason; no deletion of assignment.  
- **Alternatives:** (A) President alone can suspend; (B) Advisor alone can remove student officers; (C) Automatic removal after N absences.  
- **Rationale:** **Blocking for Phase 1** — revoke/suspend must be defined before coding role states.  
- **Systems affected:** role_assignments, permissions effective set.  
- **Permissions affected:** `role.revoke` CONDITIONAL.  
- **Workflows affected:** Role assignment → SUSPENDED/REVOKED.  
- **Evidence required:** Bylaws removal section + minutes of action.  
- **Approval authority:** Executive Board; Advisor for safety overrides as defined.  
- **Effective date:** TBD  
- **Superseded decision:** —  

---

## Closure tracking

| ID | Title | Status | Blocks Phase 1? |
|----|-------|--------|-----------------|
| GOV-001 | Official officer titles | PROPOSED | Yes (positions seed) |
| GOV-002 | Position types | PROPOSED | Yes |
| GOV-003 | Officer terms | PROPOSED | Yes |
| GOV-004 | Vacancy and succession | PROPOSED | Yes |
| GOV-005 | Election eligibility | PROPOSED | Yes |
| GOV-006 | Election method | PROPOSED | **Yes (hard)** |
| GOV-007 | Appointment workflow | PROPOSED | **Yes (hard)** |
| GOV-008 | Meeting types | PROPOSED | Soft (needed by Phase 2) |
| GOV-009 | Quorum | PROPOSED | **Yes (hard)** |
| GOV-010 | Voting rules | PROPOSED | **Yes (hard)** |
| GOV-011 | Active-member definition | PROPOSED | **Yes (hard)** |
| GOV-012 | Member privileges | PROPOSED | **Yes (hard)** |
| GOV-013 | Spending thresholds | PROPOSED | No (blocks Phase 5) |
| GOV-014 | Financial SoD | PROPOSED | No (blocks Phase 5; recommend early) |
| GOV-015 | Sensitive communications | PROPOSED | No (blocks Phase 6) |
| GOV-016 | Data classification | PROPOSED | **Yes (hard)** |
| GOV-017 | Data retention | PROPOSED | **Yes (hard)** |
| GOV-018 | Privileged roles | PROPOSED | **Yes (hard)** |
| GOV-019 | Emergency recovery | PROPOSED | **Yes (hard)** |
| GOV-020 | Officer removal/suspension | PROPOSED | **Yes (hard)** |

**Phase 0 remains DRAFT until hard blockers are APPROVED with evidence.**
