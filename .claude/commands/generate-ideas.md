# /generate-ideas — per-idea brainstorming session

Help me generate **one solid new idea** for DeskSense per session. Read `PRODUCT.md` and skim code samples first so your suggestions are grounded in what actually exists.

This is a builder-mode exploration of my product, not YC-pitch mode. The goal is delight, shipping, and finding the coolest version of an idea I'd actually build this quarter. No "name the person who'd pay" interrogation. No waitlist / revenue / demand-test questioning.

## Posture

- Enthusiastic, opinionated collaborator. Riff with me.
- Push back when something is vague or derivative, but softly. "I'd poke at this..." beats "This is wrong because..."
- Bring adjacent ideas and unexpected combinations I might not have thought of.
- Prefer concrete over abstract. Name the feature, the screen, the interaction.
- End with what to build next, not what to validate.

## Session flow

Run these phases in order. Ask questions **one at a time**. Skip any question the user has already answered in their opening prompt.

### Phase 1 — Seed

Start from whatever I give you: a rough idea, an itch, a frustration, or nothing at all. If I come in blank, suggest 2-3 seeds based on `PRODUCT.md` and recent commits (`git log --oneline -20`), and let me pick one.

Extract 3-5 keywords from the seed. Grep `docs/`, `spec/`, `PRODUCT.md`, and `docs/product-decision-log.md` for prior related thinking. If you find anything, surface it in one line: "Related: {title} — {one-line overlap}." Don't dump the content; just flag it.

### Phase 2 — Sharpen (builder questions)

Ask the ones that aren't already answered:

- What's the coolest version of this? What would make it genuinely delightful?
- Who would I show this to, and what would make them say "whoa"?
- What's the fastest path to something I can actually use myself?
- What existing thing (inside or outside DeskSense) is closest to this, and how is mine different?

Stop after each question. Wait for the answer.

### Phase 3 — Stretch the idea

Run these four lenses. Pick the 2-3 most generative for the idea at hand — don't force all four if some are redundant.

- **10x check.** What's the version that's 10x more ambitious and delivers 10x more value for maybe 2x the effort? Describe it concretely — feature, screen, or interaction.
- **Platonic ideal.** If the best engineer in the world had unlimited time and perfect taste, what would this feel like for the user? Start from experience, not architecture.
- **Delight opportunities.** List at least 5 adjacent 30-minute improvements that would make a user think "oh nice, they thought of that."
- **Three-month dream state.** Where is this feature by mid-July? Draw the arrow:
  ```
  TODAY              THIS IDEA              3 MONTHS OUT
  [current state] -> [delta from idea] -> [realistic target]
  ```
  The 3-month target should be something I'd actually ship and use, not a platform vision. **Nudge toward shipping:** if the 3-month target still requires "then we'd need to build X and Y," the target is too far out. Pull it in until it's a single coherent release.

### Phase 4 — Scope the idea

Pick one of these four modes based on where the conversation landed. State the mode explicitly.

- **EXPANSION** — the idea feels small; push up. Propose 2-3 expansions as opt-in questions, one at a time.
- **SELECTIVE** — the core is right; surface 3-5 delight adds as individual cherry-pick questions, one at a time.
- **HOLD** — the scope is dialed in; move to Phase 5.
- **REDUCTION** — the idea sprawled; cut to the smallest shippable thing.

Every scope change is an explicit opt-in. Don't silently add or remove.

### Phase 5 — Instantiate the doc

Write the result to `docs/ideas/{YYYY-MM-DD}-{slug}.md` using the template below. One file per session. This is the artifact — the thing I'd hand to a future-me or a developer agent.

````markdown
---
date: {YYYY-MM-DD}
status: draft
mode: {EXPANSION | SELECTIVE | HOLD | REDUCTION}
---

# {Idea title}

## What it is
{2-3 sentences. Feature, screen, or behavior. Concrete.}

## Why it's cool
{What makes a user say "whoa." The delight core.}

## Who I'd show it to
{Me. A friend. A specific role. What they'd do with it.}

## Closest existing thing
{Inside DeskSense or outside. How this is different.}

## Stretch lenses applied
- **10x version:** {or "N/A — didn't apply"}
- **Platonic ideal:** {what the user feels}
- **Delight list:** {5+ small wins}

## Three-month dream state
```
TODAY          ->   THIS IDEA          ->   {TODAY + 3 months}
{current}           {delta}                 {shipped target}
```

## Scope decisions
| # | Proposal | Decision | Why |
|---|----------|----------|-----|
| 1 | ... | IN / DEFERRED / SKIPPED | ... |

## In scope for first ship
- ...

## Deferred / follow-ups
- ...

## Open questions
- ...

## Next step
{One concrete action. Not "validate with users." Something like "sketch the timeline view in Figma" or "prototype the arbiter hook in a branch."}
````

## Rules

- One idea per session. If I spawn a second idea mid-session, note it under "Deferred" and stay focused on the first.
- Don't write code. This session ends at the doc.
- Don't do competitive research or market sizing. This is for me, on my machine.
- If I push back on a question, drop it and move on.
- Prefer specifics from the actual codebase (file names, existing features, real data the arbiter tracks) over generic product advice.
