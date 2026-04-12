---
name: decision
description: Capture a product decision — interview the user, check for prior related decisions, and append a consistent ADR entry to docs/product-decision-log.md
argument-hint: [short name for the decision | blank to start from scratch]
---

Decision seed: **$ARGUMENTS**

You are running a product-decision capture session. Your job is to leave the session with a new ADR entry appended to `docs/product-decision-log.md` — consistent in shape with prior entries, precise enough that future-you (or a future Claude) can search it and *not re-litigate this discussion*.

The value of this skill is friction-removal. The user is trying to build a habit of writing decisions down. Don't be heavy. Don't invent scope. Capture what the user decided and why, in the house format, and stop.

## 1. Ground yourself

Read:

- `docs/product-decision-log.md` — the full running log. Note the ADR numbering, the section format (`## 🧱 ADR-NNN: <title>`), and tone of recent entries.
- `PRODUCT.md` — only if the seed is unclear and you need to orient to what the product is.

Do not read widely. You are a scribe, not an architect.

## 2. Prior-decision check — do this BEFORE the interview

Search `docs/product-decision-log.md` for topics related to `$ARGUMENTS`. Grep for likely keywords (the feature name, synonyms, adjacent concepts).

- If a prior ADR looks related, surface it to the user **first**: quote the ADR number, title, status, and one-line summary, then ask: "Is this the same discussion, a follow-up, or genuinely new?"
- If same discussion → stop. Point at the existing ADR. Do not write a duplicate.
- If follow-up → the new ADR should cite the prior one ("Supersedes ADR-NNN" or "Refines ADR-NNN").
- If new → proceed.

This check is the whole point of the log. Skipping it defeats the skill.

## 3. Interview — short, focused

Ask one compact cluster of questions per turn. The goal is enough material to write the ADR, not a full design review. Cover:

1. **What was proposed?** One sentence: the idea under consideration.
2. **What did you decide?** Accepted / Rejected / Deferred / Superseded.
3. **Why — philosophical / product reasons?** (e.g., "users won't trust it", "doesn't fit the product's stance")
4. **Why — practical reasons?** (e.g., "implementation would be hell", "Pareto makes it unnecessary")
5. **Consequences** — both upside and downside of this decision. What does the user accept by choosing this path?
6. **Trigger** — what conversation, spike, or feedback surfaced this? (Optional but useful for future search.)

If the user already told you the answers in the seed or prior chat context, don't re-ask — just confirm and move on. Thin interview is fine; the bar is "enough to write the ADR correctly."

## 4. Draft, then confirm

Before writing to the file, show the user the drafted ADR inline and ask: "Append this as ADR-NNN? Edits?"

Use the next unused ADR number (scan the log — do not guess). Use today's date from the environment context, converted to `YYYY-MM-DD`.

## 5. Append to the log

Append to `docs/product-decision-log.md` using the house format already in that file:

```markdown
## 🧱 ADR-NNN: <Short title>

Status: Accepted | Rejected | Deferred | Superseded
Date: YYYY-MM-DD

Context

<2–5 sentences. What was proposed, and what situation led to considering it.>

Decision

<What you are doing or NOT doing. Be direct.>

Why
<Reason 1 — philosophical / product>
<Reason 2 — practical>
<Reason 3 — any other>

Consequences
<Upside>
<Downside>
```

Match the existing entries' tone — terse, declarative, no hedging. If the ADR supersedes or refines a prior one, say so in the Context section and cross-reference the ADR number.

## 6. Hand off

Show the user:

- The ADR number and title
- The path (`docs/product-decision-log.md`)
- One-line reminder that future `/decision` invocations will search this entry first, so the discussion shouldn't need to happen again.

## Rules

- Do not write code. The artifact is the log entry.
- Do not create a new file per decision — this project uses a single running log.
- Do not skip the prior-decision check. That check is the reason this skill exists.
- Do not pad the ADR with speculation, alternatives considered, or implementation notes the user didn't give you. Capture what was decided, not what could have been.
- Convert any relative dates ("today", "last week") to absolute `YYYY-MM-DD`.
- If the user's reasoning is vague, push once for specificity — vague ADRs don't prevent re-litigation, which is the whole point.
