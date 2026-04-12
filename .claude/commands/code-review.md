---
name: code-review
description: Review a diff for bugs, spec drift, invariant violations, and style
argument-hint: [commit SHA | PR# | file paths | blank for HEAD]
---

Review target: **$ARGUMENTS**

## 1. Resolve the target

Try in order; stop at the first that yields a non-empty diff:

1. Looks like a git SHA (hex, 7+ chars) → `git diff <sha>~1 <sha>`
2. Looks like `#123`, `PR 123`, or a GitHub PR URL → `gh pr diff 123`
3. Looks like `<ref>..<ref>` → `git diff <that range>`
4. One or more existing file paths → `git diff HEAD -- <paths>`; if paths aren't tracked, read them directly and review as-is
5. Empty → `git diff HEAD` (uncommitted); if empty, fall back to `git diff @{u}...HEAD` (branch vs upstream); if still empty, `git show HEAD`

State the interpretation in one line ("Reviewing PR #123 via `gh pr diff`") and proceed. Only ask the user if every strategy returns nothing.

## 2. Gather context

- Read `CLAUDE.md` for invariants (backend owns timing, Arbiter is authority, etc.)
- Read `DESIGN.md` if the diff touches UI (dashboard/, any `.tsx`, `.css`, Tailwind classes)
- If the commit message or PR description references a spec/issue, read it

## 3. Review

Evaluate the diff against:

- **Bugs** — logic errors, off-by-ones, null/undefined, race conditions, missing awaits, error paths
- **Invariant violations** — anything that contradicts CLAUDE.md (e.g. client doing timing logic, high-res data leaving the server)
- **Spec drift** — behavior doesn't match the linked spec/issue
- **Design drift** — UI changes that deviate from DESIGN.md
- **Tests** — is the change covered? For bug fixes, is there a regression test per the project's "write failing test first" rule?
- **Style** — only flag if it departs from neighboring code or project config (black line-length 93, isort profile black, eslint)

## 4. Report

Group findings under these headers, in this order. Skip any section with nothing to report — don't write "none found."

```
## Bugs
- `path/to/file.py:42` — <1-2 sentence description + suggested fix>

## Invariant violations
## Spec / design drift
## Test coverage
## Style / nits
```

Cite `file:line` for every finding. Keep each bullet to 1–2 sentences; if a fix needs more, show a short code block.

End with a one-line verdict: **Ship it**, **Ship with nits**, or **Needs changes** + the blocking item.

## Rules

- Don't edit files. This is review only.
- Don't restate what the diff does — the user can read it. Focus on what's wrong or risky.
- Don't pad. If there are zero findings, say so in one line and stop.
