# Organizational structure

## terms

Every governance record belongs to a term.

Examples:

- Fall 2026
- Spring 2027
- Academic year 2026–2027

Fields:

- `id`, `organization_id`
- `label`
- `start_date`, `end_date`
- `kind` (semester / academic_year)
- `status` (upcoming / active / closed)

## positions

Offices (not permissions):

- Advisor
- President
- Vice President
- Treasurer
- Secretary
- Project Manager
- SGA Representative
- Social Media Manager

Fields:

- `id`, `organization_id`
- `code` (stable key, e.g. `president`)
- `title`
- `description`
- `is_high_privilege` (triggers Advisor verification)
- `default_permission_set_id`

## role_assignments

Connects a **member** to a **position** for a defined period (Law 2).

Required:

- `user_id` / `membership_id`
- `position_id`
- `term_id`
- `start_date`, `end_date`
- `appointment_method`
- `nominated_by`
- `approved_by`
- `evidence_document_ids` / meeting_resolution_id / election_record_id
- `status` (see role workflow)
- `suspension_reason` / `revocation_reason`

## committees

Examples:

- Executive Board
- Project Committee
- Events Committee
- Finance Committee
- Election Committee

## committee_memberships

A person may hold different responsibilities across committees.

- `committee_id`
- `membership_id`
- `role_in_committee`
- `term_id`
- `status`
