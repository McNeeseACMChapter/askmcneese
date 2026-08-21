# Phase 0 review — governance package for human decision

**Package status:** DRAFT  
**Date of this review:** 2026-07-18  
**Recommendation for Phase 1:** **NO-GO**

---

## 1. Executive summary

Phase 0 has a complete **working draft** governance package: twenty structured decision records (GOV-001…GOV-020), a draft role→permission matrix (no broad `admin.*`), and a draft workflow-transition matrix for all seven documented workflows. Architectural laws, domain, workflows, modules, and phase plans already exist elsewhere under `askmcneese/acm/`.

**Nothing is chapter-approved.** There is no in-repository evidence that authorized leadership approved titles, elections, quorum, membership, privileges, privilege classes, removal, audit/retention ownership, or emergency recovery. Until those hard blockers move to `APPROVED` with evidence, Phase 0 remains draft and Phase 1 foundation work must not start as production authorization.

---

## 2. Blocking decisions (Phase 1)

These must reach `APPROVED` with evidence before Phase 1 GO:

| ID | Topic | Why blocking |
|----|-------|----------------|
| GOV-006 | Election method | Role evidence path undefined |
| GOV-007 | Appointment workflow | Cannot seed role states safely |
| GOV-009 | Quorum | Binding votes/minutes invalid |
| GOV-010 | Voting rules | Motions/elections/removal undefined |
| GOV-011 | Active-member definition | Authorization step 2 undefined |
| GOV-012 | Member privileges | Baseline permission set undefined |
| GOV-002 / GOV-001 | Position types / titles | Permission ownership keys undefined |
| GOV-003 / GOV-004 | Terms / succession | Access expiry and vacancy undefined |
| GOV-005 | Election eligibility | Franchise and candidacy undefined |
| GOV-016 / GOV-017 | Data classification / retention | Audit and document design blocked |
| GOV-018 | Privileged roles | MFA/verify gates and ownership blocked |
| GOV-019 | Emergency recovery | Lockout/recovery without Law 3 violation |
| GOV-020 | Officer removal/suspension | SUSPENDED/REVOKED semantics blocked |

Per program rule: if **election, quorum, role authority, permission ownership, officer removal, audit ownership, or emergency recovery** remains unresolved → **NO-GO**. All of those remain unresolved (`PROPOSED` only).

---

## 3. Non-blocking decisions (for Phase 1 foundation)

May stay PROPOSED through Phase 1 **if** related modules are not implemented:

| ID | Topic | Blocks instead |
|----|-------|----------------|
| GOV-008 | Meeting types | Soft — needed by Phase 2 meetings |
| GOV-013 | Spending thresholds | Phase 5 finance |
| GOV-014 | Financial SoD | Phase 5 (recommend early adoption) |
| GOV-015 | Sensitive communications | Phase 6 communications |

---

## 4. Contradictions found

1. **`admin.configure` vs no `admin.*`:** Domain/authorization drafts historically imply broad admin capability; Phase 0 matrix replaces this with `system.configure`, `system.emergency_recover`, `system.account_recover`. Domain text may still say `admin.configure` until a later non-policy sync pass.
2. **Quorum alternatives inside one PROPOSED rule:** GOV-009 proposes both “majority of active members” framing and a numeric default (greater of 5 or 25%) — chapter must pick one formula.
3. **Appointment authority ambiguity:** Role workflow assumes President proposes / Advisor verifies; GOV-007 alternatives still include President-alone vs full board — unresolved who is final approver per position.
4. **High-privilege set tension:** Secretary and Tech SA are proposed high-privilege for different reasons; Tech SA must not inherit org approvals — matrix enforces DENY, but GOV-018 wording must stay explicit in approval.
5. **Duplication (not contradiction):** Position lists in `domain/structure.md`, role homes, and GOV-001; Phase 0 checklists in `policy/README.md` vs this review — keep aligned when APPROVED.

---

## 5. Recommended discussion order

1. GOV-011 Active member → GOV-012 privileges  
2. GOV-001 titles → GOV-002 types → GOV-003 terms → GOV-004 succession  
3. GOV-005 eligibility → GOV-006 election method → GOV-007 appointment  
4. GOV-018 privileged roles → GOV-019 emergency → GOV-020 removal  
5. GOV-009 quorum → GOV-010 voting → GOV-008 meeting types  
6. GOV-016 classification → GOV-017 retention (audit ownership)  
7. GOV-013/014 finance (park if Phase 5 far) → GOV-015 communications  

---

## 6. Questions requiring President input

1. Confirm official titled officers (GOV-001) and which are elected vs appointed (GOV-002).  
2. Who may propose and who may approve appointments (GOV-007)?  
3. Quorum formula for GENERAL and EXECUTIVE_BOARD (GOV-009)?  
4. Proxy voting yes/no; tie-break rule (GOV-010)?  
5. What counts as active membership for voting rights (GOV-011)?  
6. Interim succession when President vacant (GOV-004)?  
7. Removal thresholds and who may suspend (GOV-020)?  
8. Does President share emergency recovery with Advisor, or Advisor-only (GOV-019)?  

---

## 7. Questions requiring Treasurer input

1. Real spending thresholds to replace placeholders (GOV-013).  
2. Confirm SoD: requester ≠ approver; Treasurer cannot approve own reimbursement (GOV-014).  
3. Funding sources and budget categories the chapter will use.  
4. Retention needs for receipts vs university/SGA rules (GOV-017).  
5. Which finance fields are RESTRICTED (GOV-016)?  

---

## 8. Questions requiring Secretary input

1. Who attaches election/appointment evidence, and required document types (GOV-006/007)?  
2. Minutes approval: Secretary alone vs President/Advisor second approve?  
3. Retention custody of minutes and decisions (GOV-017).  
4. Meeting types the chapter will actually run (GOV-008).  
5. How eligibility cutoffs are published before elections (GOV-005).  

---

## 9. Questions requiring Faculty Advisor approval

1. Advisor verification gate for high-privilege activations (GOV-018).  
2. Emergency recovery protocol ownership and 72-hour limit (GOV-019).  
3. Data classification / FACULTY_CONFIDENTIAL and export control (GOV-016).  
4. Retention alignment with university student-org rules (GOV-017).  
5. Advisor role on finance thresholds and sensitive communications (GOV-013/015).  
6. Whether university rules constrain election eligibility or removal (GOV-005/020).  

---

## 10. Exact Phase 0 closure checklist

Phase 0 may be marked complete only when **all** of the following are true:

- [ ] Executive Board meeting held; minutes filed under ACM records  
- [ ] GOV-001…GOV-012 status = `APPROVED` with evidence links (or `REJECTED` with replacement APPROVED)  
- [ ] GOV-016, GOV-017, GOV-018, GOV-019, GOV-020 status = `APPROVED` with evidence  
- [ ] Election method (GOV-006) and quorum (GOV-009) explicitly approved  
- [ ] Role authority and permission ownership approved (titles/types/privileges/matrix ownership)  
- [ ] Officer removal/suspension (GOV-020) approved  
- [ ] Audit ownership (classification + retention + who may export) approved  
- [ ] Emergency recovery (GOV-019) approved by Faculty Advisor + board informed  
- [ ] [`role-permission-matrix.md`](./role-permission-matrix.md) revised to match APPROVED decisions (still draft until then)  
- [ ] [`workflow-transition-matrix.md`](./workflow-transition-matrix.md) revised to match APPROVED decisions  
- [ ] [`decisions.md`](./decisions.md) records approval authority, effective date, evidence for each APPROVED item  
- [ ] [`VERSION`](./VERSION) bumped only after approvals (human decision)  
- [ ] Explicit written **GO** for Phase 1 recorded by President + Advisor acknowledgment  
- [ ] No production auth/finance code started under the false claim that Phase 0 is done  

**Current checklist status:** all boxes unchecked.

---

## 11. GO / NO-GO recommendation for Phase 1

### **NO-GO**

**Reason:** Election method, quorum, role authority, permission ownership, officer removal, audit ownership, and emergency recovery are all still `PROPOSED` without chapter approval evidence. Marking Phase 1 GO would encode unverified power into software.

**Exit criterion for GO:** Checklist §10 complete for hard blockers; remaining finance/comms decisions explicitly deferred in writing if modules are out of scope.
