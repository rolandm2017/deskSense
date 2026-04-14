# Commitment Gap — recent-activity audit page

**Date:** 2026-04-14
**Status:** Ready for /developer
**Components touched:** activitytracker, dashboard

Seeded from `docs/ideas/2026-04-13-commitment-gap.md`. The original seed
proposed a full-day hour-chip timeline; during design it pivoted to a
minute-resolution 2-hour swimlane strip. Hover-to-top-3 tooltips were cut
(logged in `docs/ideas/cut-ideas.md`). The whole-day "gap stripe" inside
the card was also dropped.

## Problem

The user (primary: the developer, a language learner; secondary: a curious
friend who wants an honest time mirror) wants to glance at the dashboard a
few times a day and know two things at once:

1. **Am I on track toward what I committed to today?** (E.g., "2h immersion.")
2. **Is the tracker being honest about the last couple hours?** — i.e., can
   I verify at minute resolution what it thinks I was doing? ("Did I really do _that_?")

Existing dashboard routes show whole-day rollups or the single-lane Pursuit
Timeline; neither lets the user audit recent behavior at minute resolution,
and no surface frames time against a _commitment_. Without this view, trust
in the tracker stays low and the "did I actually do my immersion?" question
requires manual math.

## Goals

- User sees, in one sentence, how today's progress looks against up to two
  committed Pursuits, phrased per `COPY.md` (mirror, never scolding).
- User sees the last 120 minutes of activity at minute resolution, one
  swimlane per activity, so overlap and fragmentation are visible.
- User can tell at a glance which of the last two hours contributed to a
  committed Pursuit vs. which did not.
- User can click a committed Pursuit in the card to change which Pursuit's
  contributions are visually emphasized in the strip.
- Developer can audit the tracker's raw decisions for the 2-hour window
  via a page-level debug toggle.

## Non-goals

- No user-configurable daily goals in v1. Both goals are **hardcoded** in
  code. Real per-Pursuit goals are tracked in `spec/todo-goals.md`.
- No live updating. Page is a snapshot — refresh to advance.
- No user-adjustable window length. Fixed at 120 minutes.
- No hover tooltips on strip blocks. Click-to-receipts only.
- No whole-day 24-hour timeline on this page. (The existing daily Pursuit
  Timeline covers that axis.)
- No "gap stripe" showing when committed time landed across the whole day.
- No notifications, streaks, coaching, or productivity scores.
- No pacing math. "On pace" is not calculated — the headline speaks to
  _how much of the goal remains_ and _how much of the day remains_, not to
  an even-spread expectation.
- No attention-quality scoring. A block either contributes to a Pursuit or
  it does not — clean yes/no based on whether its underlying program /
  domain / video channel is a member of that Pursuit. Idle and
  Uncategorized never contribute.
- No authentication gating on the debug overlay. App is single-user today.

## User story (happy path)

It's 2026-04-14, 3:47pm. The user opens `/activity-overview`.

At the top of the page: a **Commitment Gap card** with two rows, primary
above secondary. Example hardcoded goals:

- **Primary:** Language Immersion — `1h 10m / 2h`
- **Secondary:** Deep Work — `2h 05m / 3h`

Primary row is saturated on load; secondary is dimmed. Above the rows is
one sentence in COPY.md voice: _"Some progress so far. There's still
time."_ Each row shows the Pursuit's color dot, name, `actual / committed`,
a thin progress bar, and the top 2–3 offender Pursuits for today.

Below the card: a **2-hour strip** running from 1:47pm to 3:47pm, one
horizontal swimlane per distinct activity (program / domain / video
channel) that appeared in the window. Each swimlane shows colored blocks
at the times that activity was foreground. Blocks shorter than 3 minutes
are merged with adjacent same-activity blocks in the same lane; any block
in the rendered data is at least 3 minutes wide. Blocks whose underlying
activity is a member of the currently-saturated Pursuit (primary, by
default) render at full saturation; all other blocks render dimmed. A
thin "now" marker sits at the right edge.

The user clicks **Deep Work** in the card. The card's saturation swaps:
Deep Work is now saturated, Language Immersion dimmed. In the strip, the
blocks contributing to Deep Work become saturated; Immersion blocks dim.
No refetch needed.

The user clicks a block in the strip → an inline panel expands showing
the raw Activity rows backing that block (start/end timestamps, exact
program/domain/video).

The user presses **Shift** and clicks the page-level debug toggle (or
uses a keyboard affordance). A debug overlay appears, dumping the raw
arbiter state transitions for the full
120-minute window. The debug overlay ought to opt for plainness, as
it is for the developer.

## Behavior spec

### Card

1. The card must show exactly two goals in v1: a **primary** row on top,
   a **secondary** row below. Both are hardcoded in code (Pursuit id or
   name + committed seconds). A developer-agent-facing constants module
   must be the single edit point for changing them.
2. Each row must display: Pursuit color dot, Pursuit name,
   `actual / committed` in `Hh MMm` format, a thin horizontal progress
   bar clamped to [0, 100%], and a list of top 2–3 "offender" Pursuits
   for today (the non-committed Pursuits with the most time today).
3. Above the rows, a single headline sentence must be rendered whose
   wording is driven by the **primary** goal's state. States and their
   copy must follow `COPY.md`. State selection rule (v1):
    - `0m` done, before noon local → "Start of day"
    - `actual >= committed` → "Hit" (or "Slightly Over" / "Far Ahead" at
      developer-agent discretion within COPY.md options)
    - `actual >= 0.85 * committed` and not hit → "Close"
    - `actual > 0` and `remaining > 0` and current local hour < 22:00 →
      "Slipping (recoverable)"
    - `remaining > 0` and current local hour >= 22:00 → "Missed"
    - `actual > 1.15 * committed` → "Far Ahead / Over"
      The headline must never use the words "behind", "should", "need to",
      "only", or "missed your goal". Follow COPY.md antipatterns.
4. Exactly one row is saturated at any time; the other is dimmed. On
   initial render, the primary row is saturated. Clicking the dimmed row
   swaps saturation (behavior type (a) from design: toggle between the
   two; "neither saturated" is unreachable).
5. Clicking the saturated row is a no-op visually.
6. Offender lists include Idle and Uncategorized.

### 2-hour strip

7. The strip must cover exactly the most recent 120 minutes, ending at
   page-load "now" (wall clock at render time). It must not live-update;
   refresh is the only way to advance the window.
8. The strip must render one horizontal swimlane per distinct underlying
   activity (program, domain, or video channel) that appeared within the
   window. Lanes must be stacked vertically. Lane ordering: most total
   time in-window at top, descending. Ties broken alphabetically.
9. Within a lane, a block represents a contiguous period where that
   activity was foreground. Adjacent or overlapping same-activity
   segments (gap ≤ the minimum-block constant) must be merged into a
   single visual block.
10. Rendered blocks must be **at least `MIN_BLOCK_SECONDS` wide** where
    `MIN_BLOCK_SECONDS` defaults to 180 and must be defined as a single
    named constant in the dashboard code, easily changeable to 60. Raw
    segments shorter than `MIN_BLOCK_SECONDS` that cannot merge into an
    adjacent same-activity block must be widened to `MIN_BLOCK_SECONDS`
    at render time (anchored at their true start); they must not
    overwrite or eat segments in other lanes, because lanes are
    independent.
11. Overlap across lanes is allowed and expected; a minute where the
    user had two foreground activities shows a block in each lane.
12. A block whose underlying activity is a member of the currently
    **saturated** Pursuit (from the card) must render at full
    saturation; all other blocks render dimmed. Saturation is the only
    goal-attribution signal — no badges, no labels.
13. Membership is a clean yes/no lookup (program/domain/video-channel
    ∈ Pursuit members). Idle and Uncategorized activities must never
    render as saturated.
14. A thin "now" marker must sit at the right edge of the strip at the
    current local-hour-minute.
15. Clicking a block must expand an inline panel listing the raw
    Activity rows that compose the block (start, end, duration, exact
    program/domain/video identifier). Clicking again collapses it.
16. If zero activities occurred in the window, render an empty-state
    message in COPY.md voice (e.g. "Nothing on the board yet.") and
    still render the "now" marker.

### Debug overlay

17. A page-level debug toggle must reveal, for the full 120-minute
    window: arbiter state transitions (timestamp, from-state,
    to-state, reason if available). Toggle is not auth-gated in v1.
18. Toggle interaction: developer-agent latitude — a shift-click on a
    dedicated button, or a keyboard shortcut, or a small "debug" link
    in the page footer. Must not be findable by a casual user; need
    not be hidden from a determined one.

### Day boundary

19. "Today" for card `actual` values must use the PRODUCT.md day rule
    (4:00am local). The 120-minute strip window is independent of the
    day boundary and may cross it.

## Data & contracts

### Backend

- Add one endpoint (or two if cleaner): serve the data needed by this
  page. Prefer reuse-with-alteration of existing `/api/daily/*` where
  possible (per CLAUDE.md API stability map). Do **not** extend any
  `/api/dashboard/*` route.
- Proposed shape (developer-agent may adjust names): - `GET /api/activity-overview?tz=<IANA>` → JSON with: - `now_iso`: server-computed render time (ISO8601 with tz offset) - `goals`: ordered array of 2 objects: `{ pursuit_id, pursuit_name,
color, committed_seconds, actual_seconds_today, offenders: [{
pursuit_name, seconds }] }` (max 3 offenders per goal) - `strip`: `{ window_start_iso, window_end_iso, lanes: [{
activity_key, activity_display_name, activity_type,
pursuit_id_or_null, segments: [{ start_iso, end_iso }] }] }`
  — segments are **raw** (no 3-minute padding); frontend applies
  `MIN_BLOCK_SECONDS`. Backend must pre-merge segments whose gap
  is ≤ 1 second (arbiter jitter). - `debug`: `{ arbiter_transitions: [...], chrome_dedup_decisions:
[...] }` — populated only when `?debug=1` is on the request, to
  keep the default payload small.
- The hardcoded goals live on the **frontend** in v1 (a constants
  module). The backend resolves Pursuits by id/name as requested. This
  keeps the backend generic for when real goals arrive.
- Don't write anything deeper into the backend than a router file. You
  can write pseudocode for the service layer interface.

### Frontend

- New page at `/activity-overview`. Extend the existing hardcoded
  `activity-overview.html` / React page as the canvas rather than
  starting from scratch.
- Single fetch on mount. Refetch only on full page refresh.
- Constants module owns: `GOAL_PRIMARY`, `GOAL_SECONDARY` (each with
  Pursuit identifier and `committed_seconds`), and `MIN_BLOCK_SECONDS`
  (default 180).

### DB

- No schema changes required. All data is derivable from existing
  Activity / Pursuit / membership tables. Pretend the data is there if it's not.

## Invariants to preserve

- **Backend owns timing.** The frontend does no aggregation beyond
  rendering and applying `MIN_BLOCK_SECONDS`. All `actual_seconds`,
  offender totals, and segment boundaries come from the backend.
- **High-resolution user activity data never leaves the server.** The
  strip payload is per-user-machine, served by the local backend to
  the local dashboard — nothing new is exposed externally.
- **Activity Arbiter is sole authority on what gets logged.** This
  feature reads arbiter output; it does not write activity data.
- **Day boundary = 4:00am local.** Honored by the `actual_seconds`
  rollups.

## Test plan

All Python tests run via `win-pytest`. Dashboard tests run via
`win-npm-test` (WSL → Windows bridge); dashboard under WSL cannot run
builds directly.

### Failing tests to write first (bugfix-style, per CLAUDE.md)

- `activitytracker/tests/api/test_activity_overview_endpoint.py` —
  proves the endpoint exists, returns the documented shape, and
  computes `actual_seconds_today` against the 4am day boundary for
  two known hardcoded goal Pursuits.
- `activitytracker/tests/api/test_activity_overview_strip.py` —
  proves the 120-minute window is computed from `now_iso`, lanes are
  ordered by in-window total desc, and backend-side ≤1s-gap merging
  happens.
- `activitytracker/tests/api/test_activity_overview_offenders.py` —
  proves Idle and Uncategorized are excluded from offenders and that
  at most 3 offenders are returned per goal.
- `activitytracker/tests/api/test_activity_overview_debug.py` —
  proves `?debug=1` adds the debug payload and default omits it.
- Dashboard (vitest): `dashboard/src/pages/ActivityOverview.test.tsx`
  (or local equivalent) — proves headline copy selection matches the
  state rules using COPY.md-permitted strings, that clicking the
  dimmed row swaps saturation, and that a raw 90-second segment
  renders at 180px-equivalent width (or whatever the unit is).

### Integration / end-to-end

- None required beyond the unit/API tests above. The feature is a
  single read-only page.

### What the agent cannot test

- Visual correctness of the saturation effect, block alignment,
  swimlane stacking, and the "now" marker position. `/qa` picks this
  up post-implementation.

## Open questions / developer-agent latitude

- Exact endpoint name/shape — the proposal is a starting point;
  renaming or splitting into two endpoints is fine if it simplifies
  reuse of existing `/api/daily/*` helpers.
- Debug toggle affordance (shift-click a button, keyboard chord, or
  footer link). Constraint: not findable by a casual user.
- Block merge gap tolerance on the frontend (in addition to the
  backend ≤1s pre-merge). Pick a sensible small number; document it.
- Empty-state copy variant from COPY.md.

## Out-of-scope follow-ups

- Real per-Pursuit daily goals as user-configurable data
  (`spec/todo-goals.md`).
- User-adjustable strip window length (30m / 1h / 4h).
- Live-updating strip.
- Hover tooltip on blocks (see `docs/ideas/cut-ideas.md`).
- Whole-day "gap stripe" inside the card.
- Per-weekday goal schedules, sub-Pursuit goals, good/great/exceeded
  bands.
