# TODO: Per-Pursuit Daily Goals

Deferred from the "Commitment Gap" idea (see `docs/ideas/2026-04-13-commitment-gap.md`). The first
ship of that feature uses hardcoded goal values so the hour-resolution timeline and debug value can
land immediately. This doc tracks the work to replace those hardcodes with real, user-configurable
daily goals.

## Current state

- Pursuits already support an **optional weekly goal** (see `PRODUCT.md` core vocabulary).
- There is no daily-goal concept in the data model or UI.
- The Commitment Gap card needs a per-day "committed" number to compare "actual" against.

## Target

Let a user say, per Pursuit: "I want to do 60 minutes of this today" — and have the dashboard honor
it. The originating use case is the language learner committing to, e.g.:

- 60 minutes of immersion
- 90 minutes of a specific YouTube channel (already a Pursuit member type)
- 120 minutes of a specific TV series (Netflix title, already tracked)

## Open design questions

1. **Daily vs. weekly vs. both.** Does a Pursuit get one or both? If both, how do they interact
   (does the daily goal derive from the weekly, or are they independent commitments)?
2. **Per-weekday schedules.** Language learners often have different weekday vs. weekend targets.
   Is day-of-week scheduling in scope, or is a single daily number enough for v1?
3. **Sub-Pursuit goals.** Can the user set a goal on a *member* of a Pursuit (one YouTube channel,
   one Netflix title) instead of only on the whole Pursuit? The seed conversation implied yes.
   If so, the goal concept may need to live one level below Pursuit.
4. **Rollover / make-up rules.** If the user misses Monday's goal by 20m, does Tuesday's target
   bump? Default: no rollover — each day stands alone. Confirm.
5. **"What good looks like" band.** Beyond a single target, the user floated a self-defined
   good/great/exceeded band. Is that a second number per goal (a stretch target), or a qualitative
   zone around the committed number (e.g. 80–120% = "on target")?

## Implementation sketch (non-binding)

- Extend the Pursuit model with `daily_goal_seconds: Optional[int]`.
- New endpoint `/api/daily/commitment-gap?date=...` returning, per Pursuit with a goal:
  `{ pursuit_id, committed_seconds, actual_seconds, top_offenders: [{pursuit_id, seconds}] }`.
- UI: settings panel on each Pursuit to set the number; dashboard Commitment Gap card consumes the
  new endpoint.
- Migration: Alembic migration adds the column, nullable, default NULL.

## Dependencies

- Pursuit creation UI (in flight — see `spec/create-pursuits-ui-2026-04-12.spec.md`).
- Endpoint contract work (`spec/endpoints.md`).

## Out of scope for this doc

- Goal streaks, notifications, celebration animations.
- Weekly-goal rework. Existing weekly goal stays as-is until this lands.
