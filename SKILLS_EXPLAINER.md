# Writing Skill / Slash-Command Files

A short guide to writing good `.claude/commands/*.md` files (skills / slash commands) for this repo, based on the rewrite of `code-review.md`.

---

## What a skill file is

A markdown file in `.claude/commands/` (project-local) or `~/.claude/commands/` (user-global). The filename becomes the slash command: `.claude/commands/code-review.md` → `/code-review`.

When you type `/code-review <stuff>`, the agent reads that file as the prompt for the turn, with your `<stuff>` substituted into `$ARGUMENTS`.

## File anatomy

```markdown
---
name: code-review
description: Review a diff for bugs, spec drift, invariant violations, and style
argument-hint: [commit SHA | PR# | file paths | blank for HEAD]
---

<the actual prompt body — markdown, as long as you want>
```

Frontmatter fields:
- **name** — slash command name. Match the filename.
- **description** — one line. Shown in command pickers and used by the agent's skill-routing logic to decide if your command matches a natural-language request.
- **argument-hint** — shown next to the command in autocomplete. Keep it short and descriptive.

## Argument substitution

Inside the body:
- `$ARGUMENTS` — the full argument string, verbatim.
- `$0`, `$1`, `$2`, … — positional tokens (whitespace-split).

**Prefer `$ARGUMENTS`.** Positional args are brittle — they force users to remember argument order and break the moment someone passes a SHA instead of a path. Accept a free-form argument, then teach the skill to interpret it.

## How to specify "which files" / "which diff"

The elite pattern is **intent in, resolution inside the skill.** Don't make the user craft `git diff <sha>~1 <sha>`. Let them pass the SHA (or PR number, or nothing) and have the skill figure out what diff command to run.

Resolution ladder for a review-style skill:

1. Arg looks like a hex SHA → `git diff <sha>~1 <sha>`
2. Arg looks like `#123` / a PR URL → `gh pr diff 123`
3. Arg looks like `a..b` → `git diff a..b`
4. Arg is file paths → `git diff HEAD -- <paths>` (fall back to reading files directly if untracked)
5. Arg is empty → `git diff HEAD`, then `git diff @{u}...HEAD`, then `git show HEAD`

State the interpretation in one line and proceed. Only ask the user if every strategy yields nothing.

For "which files to look at, optionally" the answer is the same: accept them as `$ARGUMENTS`, and if blank, pick a sensible default (the working-tree diff, or a hardcoded list if the skill is always scoped to certain paths).

## What makes a good skill body

1. **Resolve inputs first.** Ambiguity ladder with explicit defaults. Never stall asking "which file?" when HEAD is a fine default.
2. **Pull in project context.** Point at `CLAUDE.md`, `DESIGN.md`, specs — anything that grounds judgments in this repo's rules rather than generic advice.
3. **Fix the output shape.** Say exactly what sections you want and in what order. Skills that leave output format open produce variable, hard-to-scan results.
4. **Cite `file:line` everywhere.** Makes findings jump-to-able.
5. **Set guardrails.** "Don't edit files." "Don't pad empty sections." "Don't restate what the diff does." Tight negative instructions prevent a lot of drift.
6. **End with a verdict or next step.** One line. Forces the skill to commit to a conclusion.

## Anti-patterns seen in drafts

- `$0` / `$1` for review commands — breaks on SHAs and PR numbers.
- "Read the spec" with no hint where specs live — tell me the directory.
- "Perform a detailed review" with no output schema — produces a blog post instead of a punch list.
- Asking the user to pre-form git commands — defeats the point of a skill.
- Sections like "findings: none" when there are no findings — skip the section instead.

## A minimal template

```markdown
---
name: my-skill
description: <one line — also used by skill routing>
argument-hint: [what to pass]
---

Target: **$ARGUMENTS**

## 1. Resolve inputs
<ladder of how to interpret $ARGUMENTS, with a default for empty>

## 2. Gather context
<which project files to read: CLAUDE.md, DESIGN.md, specs>

## 3. Do the work
<what to check, in what order>

## 4. Report
<fixed output shape, `file:line` citations, skip-if-empty sections>

## Rules
- <what NOT to do>
- <one-line verdict at the end>
```

## Where to go from here

- `.claude/commands/code-review.md` in this repo is the worked example.
- `/feature`, `/generate-ideas`, `/cleaning-code`, `/quality-assurance` are other project-local skills you can read for contrast.
- Global skills (the long list of `office-hours`, `investigate`, `ship`, etc.) live in `~/.claude/skills/` and are installed outside this repo.
