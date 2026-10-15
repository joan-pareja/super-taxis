---
name: wrap-up
description: Draft a Conventional Commit title and message for the current work session. Use when the user asks to wrap up, says they are done, or requests a commit message.
---

# Wrap-Up

## 1. Review the changes

Work directly on main for this single-developer monorepo. Do not suggest switching branches or opening a pull request unless requested.

Inspect git status and the relevant staged and unstaged diffs, including new files, to understand the changes.

## 2. Draft commit title and message

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): summary
```

- Choose the type from the changes: `feat` for new capabilities, `fix` for defect fixes, `chore` for maintenance, `refactor` for behavior-preserving restructuring, and `docs` for documentation.
- Scope: this project does not define scopes yet — omit the `(scope)` part for now (e.g. `feat: add wrap-up skill`)
- Summary: verb-led, ≤ 70 characters total for the title line

### Body sizing — match to the diff

Check the relevant staged and unstaged diff statistics, accounting for new files, and pick the tier:

| Tier | Signal | Body |
|---|---|---|
| Trivial | 1 file, < 20 lines, or copy/comment-only | Title only |
| Small | A handful of files, < 200 lines, no architectural decisions | 1–2 sentences or skip entirely |
| Medium | Multiple surfaces or non-trivial feature, hundreds of lines | 3–5 bullets |
| Large | Cross-cutting, schema/contract changes, many sessions | 5–8 bullets grouped by surface |

When in doubt, pick the smaller tier.

**Body rules:**
- Bullets only when needed; capitalize the first word; end with a period
- No narrative replay; no git command narration; no PR numbers
- Each bullet stays on one physical line (no hard-wrapping)
- Omit the body entirely when the title is sufficient

### Examples

Title only (trivial):
```
fix(api): default Settings env for pytest and CI
```

With body (medium):
```
feat(api): enforce user-linked transaction ownership

- Added user FK validation in transaction and category routers.
- Regenerated API and web contract artifacts after schema changes.
- Centralized remote API base URL resolution for web server calls.
```

## 3. Output

Return the commit block as a single copy-paste-ready text block. Do not suggest or print git commands (`git add`, `git commit`, `git push`).

