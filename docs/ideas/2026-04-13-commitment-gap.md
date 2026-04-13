---
date: 2026-04-13
status: draft
mode: SELECTIVE
---

# The Commitment Gap — hour-resolution activity audit

## What it is

A new dashboard page (lives at `/activity-overview`, extending the existing
`activity-overview.html`) that answers a single question: *"I said I'd do X
today. What did I actually do?"*

Two stacked components on one screen:

1. **Commitment Gap card** at the top. Per committed Pursuit, shows
   `committed` vs. `actual` vs. `top 2–3 offenders` — the Pursuits that ate
   the missing time. A plain-English headline summarizes the verdict in one
   sentence. An inline gap stripe shows *when in the day* the committed time
   actually landed.
2. **Hour-resolution timeline** below. 24 hourly chips, each colored by the
   dominant Pursuit of that hour. Hover any chip → tooltip with top 3
   activities in that hour. Click → expand to the raw Activity receipts. A
   thin "now" marker indicates the current local hour. Shift-click (or dev
   toggle) reveals raw arbiter state transitions + Chrome dedup decisions for
   debug use.

For v1 the committed goal(s) are **hardcoded** — real per-Pursuit daily goals
are tracked separately in `spec/todo-goals.md` and land afterwards.

## Why it's cool

The same artifact is honest-mirror for the mindful user *and* forensic tool
for the developer. A language learner sees "you committed to 2h of
immersion; you did 1h 10m; YouTube ate 38m of it" — no shame pie, just the
arithmetic. The developer sees every tracker's raw output attributed to a
specific hour, at last auditable.

Most trackers show pie charts of how you spent time. This one shows the
*gap between intention and reality* and hands you the receipts to explain
it.

## Who I'd show it to

- **Primary: me, the language learner.** At 5pm, glancing at the dashboard:
  "I'm 50m behind on immersion — I'll make it up tonight."
- Secondarily: a friend who's quietly dissatisfied with their time use and
  would respond to an honest mirror rather than a dashboard of vanity stats.

## Closest existing thing

- **Inside DeskSense:** the existing daily Pursuit Timeline (ADR-005) shows
  *what was active*; this shows *what was committed vs. what was active*.
  Different axis. The existing `activity-overview.html` gives the 24h
  horizontal band; this adds hour chips, goal framing, and expand-to-
  receipts.
- **Outside:** RescueTime's daily report shows categories and a "productivity
  score." It doesn't have user-defined commitments or hour-drill-in to raw
  activities. Toggl is invoicing-shaped and out of scope per `PRODUCT.md`.

## Stretch lenses applied

- **10x version:** N/A — didn't apply. The idea is already pointed at a
  single coherent release; 10x would drift into notifications, streaks, and
  coaching, which is out of scope for this quarter.
- **Platonic ideal:** user opens the page and reads one sentence in plain
  English that tells them how the day is going vs. what they committed to.
  Everything else on the page exists to answer "why" when they want to know
  why. The hour chips expand to raw receipts so the mindful user and the
  developer share the same drill-in.
- **Delight list:**
  1. Plain-English headline sentence ("You're behind by 50m").
  2. Hover-to-receipt tooltip on hour chips (no click needed for 80% case).
  3. Gap stripe inside the Commitment Gap card showing *when* the committed
     time actually happened.
  4. Thin "now" marker on the hour timeline at current local time.
  5. Shift-click debug toggle revealing raw arbiter + Chrome dedup
     decisions per hour.

## Three-month dream state

```
TODAY (2026-04-13)        ->   THIS IDEA              ->   2026-07-13
Daily Pursuit Timeline         Hour-resolution audit        Commitment Gap + hour
(single lane, 24h) exists.     page with hardcoded goal     timeline shipped on real
Hardcoded activity-            + hour chips + expand-       per-Pursuit daily goals
overview.html. No goal         to-receipts. Lives at        (todo-goals.md landed).
meter. No hour drill-in.       /activity-overview.          Plain-English headline live.
No debug affordance.           Debug toggle behind shift.   Used daily by me.
```

## Scope decisions

| # | Proposal                                                    | Decision | Why |
|---|-------------------------------------------------------------|----------|-----|
| 1 | MVP A: hour timeline + Commitment Gap card, hardcoded goal  | IN       | Fastest path to something usable *this week*; debug value lands immediately. |
| 2 | MVP B: build per-Pursuit daily goals first                  | DEFERRED | Spun out to `spec/todo-goals.md`. Avoids blocking the hour-audit value on a data-model change. |
| 3 | Plain-English headline sentence                             | IN       | Cheap, high clarity. The "platonic ideal" in one line. |
| 4 | Hover-to-receipt tooltip on hour chips                      | IN       | Covers the 80% glance case without requiring a click. |
| 5 | Gap stripe inside the Commitment Gap card                   | IN       | Shows day shape (front-loaded vs. not started) at a glance. |
| 6 | "Now" marker on hour timeline                               | IN       | Trivial, high orientation value. |
| 7 | Shift-click debug toggle on hour chips                      | IN       | Solves the original developer problem on the same screen with zero UX tax. |
| 8 | Notifications / streaks / coaching                          | SKIPPED  | Out of scope; would drift away from single-release target. |

## In scope for first ship

- Page at `/activity-overview` extending existing hardcoded example.
- Commitment Gap card: 1–2 hardcoded goals (committed seconds), real actual
  seconds from backend, top 2–3 offenders, plain-English headline sentence,
  inline gap stripe.
- Hour timeline: 24 hour chips colored by dominant Pursuit, hover tooltip
  showing top 3 activities per hour, click-to-expand to raw Activity rows,
  "now" marker at current local hour.
- Shift-click debug overlay showing raw arbiter state transitions and
  Chrome tab dedup decisions for the selected hour.
- Backend endpoint(s) to power the above — reuse-with-alteration from
  existing `/api/daily/*` where practical (per API stability map).

## Deferred / follow-ups

- Per-Pursuit daily goals as real user-configurable data — tracked in
  `spec/todo-goals.md`.
- Self-defined "what good looks like" bands (good / great / exceeded) — a
  v2 elaboration once daily goals exist.
- Per-weekday schedules (different weekday vs. weekend targets).
- Sub-Pursuit goals (goal on one YouTube channel or one Netflix title
  rather than whole Pursuit).

## Open questions

- Day boundary for the hour timeline: 4am local (per `PRODUCT.md` day
  rule) or midnight local? The 4am rule implies hours 4→28, not 0→24.
- "Dominant Pursuit per hour" tie-break rule when two Pursuits are close
  (e.g. 29m vs. 28m in a 60m window).
- Does the debug overlay need auth-gating, or is the app single-user
  enough that shift-click is fine?
- Where does the headline sentence template live — backend-rendered string
  or frontend-composed from numbers?

## Next step

Sketch the `/activity-overview` page layout: Commitment Gap card + 24 hour
chips + expand-to-receipts interaction, using the existing hardcoded
`activity-overview.html` as the starting canvas. Hardcode one goal (e.g.
"2h immersion") and real hour-bucketed data from the backend. Ship a
working prototype to yourself before wiring any new config.
