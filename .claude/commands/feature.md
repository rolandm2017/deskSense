---
name: feature
description: Collaborative feature design — interview the user, pressure-test the idea, and emit a spec file a developer agent can implement from
argument-hint: [short feature name or description | blank to start from scratch]
---

Feature seed: **$ARGUMENTS**

You are running a feature design session. Your job is **not** to start coding. Your job is to leave the session with a spec file precise enough that a fresh developer agent — one with no memory of this conversation — can implement the feature correctly on the first try.

## 1. Ground yourself

Before asking the user anything, read:

- `PRODUCT.md` — what this product is and who it's for
- `CLAUDE.md` — invariants, architecture, dev constraints (backend owns timing, WSL limits, etc.)
- `DESIGN.md` — only if the feature plausibly touches UI
- `spec/` — skim filenames and one recent spec to match the house format

If `$ARGUMENTS` points at an obvious area of code, glance at it so your questions are grounded, not generic. Do not read exhaustively — you're orienting, not implementing.

State in one line what you understood the seed to be, then begin the interview.

## 2. Interview — 2–4 rounds, more if warranted

Use the `/grill-me` skill to drive this. Each round should surface things the user hasn't said yet, not restate what they have. Prioritize questions in roughly this order:

1. **What problem is this solving, for whom, and what happens if we don't build it?** (kills vanity features early)
2. **In scope vs. explicitly out of scope** — force the user to name things the feature will *not* do
3. **The happy path** as a concrete user story, end to end
4. **Edge cases and failure modes** — empty states, concurrent writes, offline, stale data, permission denied, the Arbiter being mid-transition, etc. Tailor to the component touched.
5. **Data model and contracts** — new tables/columns, API shapes, message formats between activitytracker / chrome / dashboard
6. **Invariant check** — does anything in this feature want to violate a CLAUDE.md invariant? (client doing timing, high-res data leaving the server, dashboard writing data, etc.) If yes, resolve before writing the spec.
7. **Explore the codebase together** — do targeted reads of the files this feature will touch or sit next to. Report back in 3–6 bullets: what already exists, which abstractions look reusable, where the natural seams are. Do not read exhaustively; you're mapping the territory, not implementing.
8. **Architecture decision (with the user)** — given what the exploration surfaced, discuss out loud: extend an existing class/service or build a sibling? Where does the new code live? What's the data flow across activitytracker ↔ chrome ↔ dashboard? What must *not* cross which boundary? Surface non-obvious constraints (e.g. "IDs that look like implementation details must not leak to the client") and name them explicitly so they land in the spec as hard rules, not implied ones. The user stays in the driver's seat — propose, don't decide.
9. **Testability** — how will we prove it works? What's the failing test that would demonstrate the feature is missing?
10. **Developer experience** — where does this code live, what's the smallest surface area, what existing abstractions should it reuse?

Ask **one focused cluster of questions per turn**, not a wall. Prefer concrete examples ("when user has 0 entries on Monday, what does the chart show?") over abstract ones. If the user's answer is vague, push back — vague answers become developer-agent guesses, which become bugs.

## 3. Pressure-test before writing

Before drafting the spec, do a quick self-check out loud:

- Is there any question a developer agent would have to guess at? If yes, ask it.
- Is there any part where the user said "you figure it out"? Flag it and either get a decision or mark it explicitly as a developer-agent choice in the spec.
- Does the plan account for the WSL test setup? Agents **can** run pytest via `win-pytest <args>` and the npm test suite via `win-npm-test <args>` — these wrap `cmd.exe` under the hood and report results back. Direct `pytest` / `npm test` invocations still fail under WSL; the spec's test plan should call out `win-pytest` / `win-npm-test` where relevant.
- Does it cross the activitytracker ↔ chrome ↔ dashboard boundary cleanly?

## 4. Write the spec

Create `spec/<kebab-name>-<yyyy-mm-dd>.md`. Use today's date from the environment context. The spec is the handoff artifact — write it for the developer agent, not the user.

```markdown
# <Feature name>

**Date:** YYYY-MM-DD
**Status:** Ready for /developer
**Components touched:** activitytracker | chrome | dashboard (list only what applies)

## Problem
2–6 sentences. Who has the pain, what the pain is, why now.

## Goals
- Bulleted, outcome-shaped ("user can X", not "add Y function")

## Non-goals
- Explicit list of things this feature will NOT do. This is load-bearing — it prevents scope creep in the developer agent.

## User story (happy path)
Concrete, step by step. Real values where possible.

## Behavior spec
Enumerated rules the implementation must satisfy. One rule per bullet. Prefer "must" / "must not" phrasing. Cover edge cases surfaced in the interview.

## Architecture & constraints
The decisions reached in the architecture round. Treat each bullet as a hard rule the developer agent must honor, not a suggestion.
- Where the new code lives (file paths, which class/service it extends or sits beside, and why)
- Data flow across activitytracker ↔ chrome ↔ dashboard (who owns what, who calls whom)
- Boundary rules — things that must NOT cross a given seam (e.g. "internal IDs stay server-side; client receives abstract labels only")
- Existing abstractions to reuse, and the reason they're the right fit
- Anything the developer agent might otherwise re-derive incorrectly — spell it out here

## Data & contracts
- DB changes (tables, columns, migrations)
- API endpoints (method, path, request, response, error codes)
- Cross-component messages (chrome → backend payloads, etc.)
Only include sections that apply.

## Invariants to preserve
Cite the relevant CLAUDE.md invariants and say how this feature respects them.

## Test plan
- Failing test(s) to write first (per project rule). Name the file path and the behavior each test proves.
- Any integration / e2e coverage needed.
- What CANNOT be tested by the agent (UI under WSL) — call it out so /qa picks it up.

## Open questions / developer-agent latitude
Things intentionally left to the developer agent's judgment, with constraints on acceptable choices. Keep this list short — most things should be decided in the spec.

## Out-of-scope follow-ups
Nice-to-haves surfaced in the interview that we're deferring.
```

Keep the spec tight. A developer agent reads better from 1 page of precision than 4 pages of prose.

## 5. Hand off

Show the user the spec path and a 3–5 bullet summary of what it commits to. Ask for approval or edits. Do not proceed to implementation — the next step is the user running `/developer` in a fresh chat, followed by `/code-review` and `/qa`.

## Rules

- Do not write code during this skill. Not even a stub. The artifact is the spec file.
- Do not skip the interview to "save time." Thin specs produce developer-agent drift, which costs more than the interview.
- If the user pushes to start coding, remind them once that the spec is the deliverable, then respect their call.
- Prefer reusing existing abstractions over introducing new ones; note reuse points in the spec.
- Convert any relative dates in the conversation to absolute `YYYY-MM-DD` in the spec.
