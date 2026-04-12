# Frontend TODO: Replace Showcase Mock Data

The charts showcase currently lives as a static React conversion of `desksense-charts-v2.html`. It
         uses hardcoded values so the visual design can stabilize before live data is wired in.

This file tracks which frontend features need to start reading actual backend data instead of the t
         yped mock module in `dashboard/src/features/charts-showcase/data/mockShowcaseData.ts`.

## Current Static Areas

- Daily header: date label, first activity time, last activity time.
- Daily stat band: tracked today, productive time, active project count, focus score.
- Daily activity timeline: full-day categorized activity blocks.
- Top programs swim lanes: program or program-group timelines across the day.
- Daily category breakdown: productivity, learning, communication, entertainment, idle totals.
- Daily project list: project names, actual time, goal time, and goal progress.
- Weekly header: week number and date range.
- Weekly stat band: total tracked, productive time, daily average, comparison to last week.
- Weekly daily breakdown chart: stacked day-by-day category totals.
- Weekly trend chart: productive hours across recent weeks.
- Weekly project scoreboard: project actuals, goals, progress, and delta versus previous week.
- Right rail: reading summary, project notes, category legend, and observation snippets.

## Data Wiring Priorities

1. Daily header and daily stat band.
   These are the simplest visible wins. They need a date range query for the selected day and derived totals from existing daily summaries.

2. Daily activity timeline.
   This is the most important chart because it expresses the core product promise: what the user actually did over the day. It should use backend-owned timing decisions, not frontend reconstruction
         from unrelated summaries.

3. Daily category breakdown.
   This should be derived from the same category assignment system used by the daily timeline. The
         frontend should receive category totals rather than reclassifying raw sessions.

4. Weekly stacked breakdown chart.
   This is the weekly equivalent of the daily category totals. It can likely be backed by a weekly
         summary endpoint before the more detailed daily timeline is perfect.

5. Weekly stat band.
   This depends on weekly totals and previous-week comparison. It should be wired near the weekly stacked chart because the same response can probably serve both.

6. Top programs swim lanes.
   This needs a deliberate contract. The mock now treats these as user-meaningful groups, not merely executable names. Decide whether the backend returns raw programs, grouped programs, or explicit
         “activity clusters.”

7. Project list and project scoreboard.
   These require project/category mapping and goal metadata. If project goals do not exist in the backend yet, keep the UI hardcoded until the data model is clearer.

8. Weekly trend chart.
   This needs a multi-week endpoint or a loop over weekly summary endpoints. Prefer a dedicated aggregated endpoint so the dashboard does not become slow.

9. Right rail.
   The rail can stay partly static longest. Eventually it should read from derived insights: peak focus window, largest idle gap, strongest category, project deltas, and notable trend changes.

## Likely API Contracts Needed

### Daily Overview

Returns data for one local date.

Needed fields:

- `date`
- `firstActivity`
- `lastActivity`
- `trackedSeconds`
- `productiveSeconds`
- `activeProjectCount`
- `focusScore`
- `categoryTotals`

### Daily Timeline

Returns already-decided activity blocks for one local date.

Needed fields per block:

- `start`
- `end`
- `label`
- `category`
- `sourceType`, such as program, domain, video, idle, or peripheral-derived
- optional `projectName`

Important constraint: the frontend should not independently decide whether time is productive, idle, entertainment, or learning. The backend arbiter/category layer should own that.

### Top Program Or Activity Lanes

Returns swim-lane groups for the selected day.

Needed fields per lane:

- `rank`
- `name`
- `totalSeconds`
- `blocks`

Needed fields per block:

- `start`
- `end`
- `label`
- `category`

Open question: should these lanes represent raw programs, domains, project groups, or backend-defined clusters?

### Weekly Overview

Returns one week of summarized usage.

Needed fields:

- `weekStart`
- `weekEnd`
- `weekNumber`
- `totalTrackedSeconds`
- `productiveSeconds`
- `dailyAverageSeconds`
Needed fields per week:

- `weekLabel`
- `weekStart`
- `productiveSeconds`

### Project Goals

Returns daily and weekly progress against goals.

Needed fields:

- `projectName`
- `actualSeconds`
- `goalSeconds`
- `color`
- optional `deltaSeconds`
- optional `period`

Open question: should project goal metadata live in the backend database, a local config file, or frontend-only settings until the product model settles?

## Frontend Refactor Notes

- Keep the showcase components presentational. They should accept typed props and should not fetch directly.
- Add route/page containers later that fetch data and adapt API responses into the presentational component props.
- Keep mock data available for visual regression and design iteration.
- Preserve the route-backed daily/weekly structure because future date and range params should live in the URL.
- Preserve the entrance animations when swapping from mock data to fetched data.
- Avoid reconstructing high-resolution activity meaning in the frontend. The backend owns timing logic and classification decisions.

## Suggested First Implementation Slice

Start with a real-data daily overview slice:

1. Add or identify an endpoint for the selected day overview.
2. Create a frontend API function that returns a typed daily overview object.
3. Build a small container around the showcase daily page that replaces only the daily header and stat band with real values.
4. Leave the detailed charts mocked until the overview path is stable.
5. Then wire the daily activity timeline from a backend-owned timeline endpoint.

This keeps the first migration small while proving the route, loading, date selection, and formatting path.