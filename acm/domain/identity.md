# Organization and identity

## organizations

Even with one ACM chapter, include `organization_id`.

Supports later:

- Multiple ACM chapters
- Committees as scoped orgs (optional)
- Separate environments
- Historical organizations

Suggested fields:

- `id`
- `name` (e.g. McNeese ACM Student Chapter)
- `slug`
- `status` (active / archived)
- `created_at`

## users

Human identity (authentication subject):

- `id`
- `display_name`
- `mcneese_email`
- `auth_provider`
- `account_status` (active / suspended / deactivated)
- `last_login_at`
- `security_settings` (MFA flags, etc.)

## memberships

Relationship between a user and ACM (chapter affiliation):

- `id`
- `organization_id`
- `user_id`
- `membership_type` (student / alumni / advisor / affiliate)
- `status` (active / inactive)
- `join_date`
- `graduation_estimate`
- `acm_membership_number` (where relevant)
- `good_standing`
- `skills` / interests (structured tags)

A user account and an ACM membership are different things. Auth proves identity; membership proves chapter standing.
