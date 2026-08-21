# Financial workflow

```text
REQUESTED
  → TREASURER_REVIEW
  → BUDGET_VERIFIED
  → PRESIDENT_APPROVAL
  → ADVISOR_APPROVAL   (when required by threshold/policy)
  → PURCHASED
  → RECEIPT_SUBMITTED
  → RECONCILED
  → CLOSED
```

## Request fields

- Purpose
- Requester
- Budget category
- Requested amount / approved amount
- Vendor
- Approval chain
- Receipt
- Payment status
- Funding source
- Related event or project

## Protections

- Requester cannot approve their own reimbursement.
- Approved amount cannot be silently changed (change requires new approval / audit).
- Transactions cannot be deleted (reverse instead).
- Missing receipts generate alerts.
- Spending beyond budget requires a change request.

**Do not implement finance until Phase 1 authorization + audit are proven.**
