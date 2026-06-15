# Pull Request Checklist — AskMcNeese (DQ-02)

Use this checklist **before opening** or **before merging** any PR to `dev`.

---

## Branch & scope

- [ ] Branch name follows `feature/<short-description>` (never push directly to `main`)
- [ ] PR targets **`dev`** (not `main`)
- [ ] One logical task per PR — small and reviewable
- [ ] Ticket ID referenced in PR title or description (e.g. BE-06, FE-06, PM-07)

## Secrets & safety

- [ ] No `.env`, API keys, passwords, or student/private data in the diff
- [ ] No `docs/pm/` or `docs/devlog/` files staged (internal only)
- [ ] No `.cursor/` files staged (local IDE config only)
- [ ] `git check-ignore` passes for any sensitive paths you touched

## Proof (required)

- [ ] Runs locally — include **how to verify** in the PR description
- [ ] Terminal output, screenshot, or sample file attached for non-trivial changes
- [ ] Frontend changes: mobile **and** desktop screenshot if UI changed
- [ ] Backend changes: example request/response (e.g. `/health` or `/ask`)

## Code quality

- [ ] Matches project conventions (`docs/frontend_guidelines.md` for frontend)
- [ ] No unrelated refactors or drive-by edits
- [ ] README or `docs/setup.md` updated if setup steps changed

## Review

- [ ] Reviewer assigned (PM for foundation; role owner for implementation)
- [ ] PM verification for tickets marked Done on the backlog

---

## Quick reject reasons

| Issue | Fix |
|-------|-----|
| Pushed to `main` | Revert; re-open PR to `dev` |
| Missing proof | Add screenshot or curl output |
| Secrets in diff | Remove file; rotate if real key was exposed |
| Scope creep | Split into a second PR |
