# Dashboard API Endpoints

Draft contract for the endpoints that replace the showcase mock data.
Each endpoint lists: URL, params, response shape, and which ADR(s) shape it.

Conventions used across all endpoints:
- `date` params are ISO local dates (`YYYY-MM-DD`). The backend interprets them
  against the 4am day boundary (ADR-010), so "2026-04-12" means the window
  04:00 local 2026-04-12 through 04:00 local 2026-04-13.
- `week` params are ISO Monday-start weeks (`GGGG-'W'ww`, e.g. `2026-W15`).
- Durations are returned as integer seconds. UI formats to "2h 15m" (ADR-009).
- The frontend never re-slices time. All bucketing, merging, and category
  attribution happens server-side (ADR-005, ADR-008, CLAUDE.md invariant).
- The "Uncategorized" Pursuit (ADR-006) appears in responses with a stable
  sentinel id (e.g. `"uncategorized"`) so the frontend can style it in greys.

---

## Daily endpoints

### `GET /api/daily/overview?date=YYYY-MM-DD`
Powers the daily header and the stat band.

Response:
```json
{
  "date": "2026-04-12",
  "firstActivity": "2026-04-12T08:42:17",
  "lastActivity": "2026-04-12T22:11:03",
  "trackedSeconds": 31200,
  "productiveSeconds": 12600,
  "activePursuitCount": 3,
  "contextSwitchesPerHour": 7.4,
  "categoryTotals": {
    "productivity": 12600,
    "learning": 4800,
    "entertainment": 3600,
    "communication": 1800,
    "uncategorized": 8400
  }
}
```
Notes:
- `productiveSeconds` = sum of Pursuits whose category is `productivity` (ADR-003).
- `contextSwitchesPerHour` replaces the mock's focus score (ADR-007). Computed
  with the 8s away-threshold (ADR-008).
- `activePursuitCount` counts user-defined Pursuits with ≥ 1s of time today.
  Uncategorized is not counted.
- `categoryTotals.uncategorized` is surfaced so the stat band can honestly show
  "3h uncategorized" before tagging; the four real categories exclude it.

Shapes from: ADR-002, ADR-003, ADR-006, ADR-007, ADR-008, ADR-010.

---

### `GET /api/daily/pursuit-timeline?date=YYYY-MM-DD`
Single-lane timeline showing which Pursuit was active at each moment.

Response:
```json
{
  "date": "2026-04-12",
  "blocks": [
    {
      "start": "2026-04-12T08:42:17",
      "end":   "2026-04-12T10:15:04",
      "pursuitId": "p_copywriting",
      "pursuitName": "Freelance Copywriting",
      "category": "productivity",
      "color": "#4f7cff"
    },
    {
      "start": "2026-04-12T10:15:04",
      "end":   "2026-04-12T10:48:30",
      "pursuitId": "uncategorized",
      "pursuitName": "Uncategorized",
      "category": null,
      "color": null
    }
  ]
}
```
Notes:
- At most one Pursuit is active at a time (ADR-005). Blocks do not overlap.
- Blocks are already the arbiter's decision — the frontend renders them as-is.
- For Uncategorized segments, the frontend derives the grey-shade fill from
  the underlying program/domain mix (see `/api/daily/top-programs` for the
  source data it would use for that styling). Concrete approach TBD during
  implementation — may require a sub-blocks field on Uncategorized entries.

Shapes from: ADR-003, ADR-005, ADR-006, ADR-010.

---

### `GET /api/daily/top-programs?date=YYYY-MM-DD&limit=3`
Swim lanes for the top-N raw programs/domains that day.

Response:
```json
{
  "date": "2026-04-12",
  "lanes": [
    {
      "rank": 1,
      "kind": "program",
      "identifier": "vscode.exe",
      "displayName": "VS Code",
      "totalSeconds": 14400,
      "blocks": [
        { "start": "2026-04-12T08:42:17", "end": "2026-04-12T12:30:00" },
        { "start": "2026-04-12T13:05:00", "end": "2026-04-12T15:00:00" }
      ]
    },
    {
      "rank": 2,
      "kind": "domain",
      "identifier": "youtube.com",
      "displayName": "youtube.com",
      "totalSeconds": 5400,
      "blocks": [ /* ... */ ]
    }
  ]
}
```
Notes:
- `kind` is `"program"` or `"domain"`. Pursuits are not returned here —
  this lane is intentionally raw (ADR-005).
- Blocks within a lane are merged across gaps ≤ 5 minutes (ADR-008).
  The merge is applied ONLY to this endpoint.
- Default `limit` = 3 to match the current dashboard layout.

Shapes from: ADR-005, ADR-008, ADR-010.

---

### `GET /api/daily/pursuit-list?date=YYYY-MM-DD`
Today's Pursuit actuals with pace vs weekly goal.

Response:
```json
{
  "date": "2026-04-12",
  "pursuits": [
    {
      "pursuitId": "p_copywriting",
      "name": "Freelance Copywriting",
      "category": "productivity",
      "color": "#4f7cff",
      "todaySeconds": 7200,
      "weeklyGoalSeconds": 72000,
      "impliedDailyPaceSeconds": 10285,
      "pacePercent": 70.0
    }
  ]
}
```
Notes:
- `pacePercent` = `todaySeconds / (weeklyGoalSeconds / 7) * 100`, capped at 999 for sanity.
- `weeklyGoalSeconds`, `impliedDailyPaceSeconds`, `pacePercent` are null/omitted
  when the Pursuit has no goal set (ADR-009).
- Uncategorized is NOT included in this list — it is a system Pursuit, not a
  user-tracked one (ADR-006).

Shapes from: ADR-003, ADR-006, ADR-009.

---

## Weekly endpoints

### `GET /api/weekly/overview?week=GGGG-Www`
Header band and week-over-week comparison.

Response:
```json
{
  "week": "2026-W15",
  "weekStart": "2026-04-06",
  "weekEnd":   "2026-04-13",
  "totalTrackedSeconds": 180000,
  "productiveSeconds":  72000,
  "dailyAverageSeconds": 25714,
  "previousWeek": {
    "totalTrackedSeconds": 162000,
    "productiveSeconds":  60000,
    "deltaProductiveSeconds": 12000
  }
}
```
Notes:
- Week boundaries use the 4am Monday rule (ADR-010).
- `previousWeek` omitted if there is no data for the prior week.

Shapes from: ADR-002, ADR-003, ADR-010.

---

### `GET /api/weekly/daily-breakdown?week=GGGG-Www`
Stacked day-by-day category totals for the weekly breakdown chart.

Response:
```json
{
  "week": "2026-W15",
  "days": [
    {
      "date": "2026-04-06",
      "categoryTotals": {
        "productivity": 10800,
        "learning": 3600,
        "entertainment": 1800,
        "communication": 900,
        "uncategorized": 4500
      }
    }
    /* ... 7 entries ... */
  ]
}
```
Shapes from: ADR-003, ADR-006, ADR-010.

---

### `GET /api/weekly/trend?weeks=12`
Productive-seconds-only trend for the trend chart.

Response:
```json
{
  "weeks": [
    { "week": "2026-W04", "weekStart": "2026-01-19", "productiveSeconds": 58000 },
    { "week": "2026-W05", "weekStart": "2026-01-26", "productiveSeconds": 62000 }
    /* ... 12 entries, oldest first ... */
  ]
}
```
Notes:
- `weeks` query param defaults to 12 (ADR-011). Max capped at 104 (two-year retention, ADR-011).
- One request, 12 rollups. Do NOT implement by looping `/weekly/overview`.

Shapes from: ADR-011.

---

### `GET /api/weekly/pursuit-scoreboard?week=GGGG-Www`
Per-Pursuit weekly actuals, goal progress, and delta vs previous week.

Response:
```json
{
  "week": "2026-W15",
  "pursuits": [
    {
      "pursuitId": "p_copywriting",
      "name": "Freelance Copywriting",
      "category": "productivity",
      "color": "#4f7cff",
      "actualSeconds": 52000,
      "weeklyGoalSeconds": 72000,
      "goalPercent": 72.2,
      "previousWeekSeconds": 48000,
      "deltaSeconds": 4000
    }
  ]
}
```
Notes:
- Goal fields null/omitted when Pursuit has no goal (ADR-009).
- `previousWeekSeconds` null when no prior-week data exists for this Pursuit.
- Uncategorized is excluded, same rationale as the daily list.

Shapes from: ADR-003, ADR-006, ADR-009, ADR-010.

---

## Pursuit management endpoints

These power the Pursuit setup UI (not in the showcase yet, but needed before
any of the dashboards become meaningful).

### `GET /api/pursuits`
List all user-defined Pursuits with membership and goals.

Response:
```json
{
  "pursuits": [
    {
      "pursuitId": "p_copywriting",
      "name": "Freelance Copywriting",
      "category": "productivity",
      "color": "#4f7cff",
      "weeklyGoalSeconds": 72000,
      "members": [
        { "sourceType": "program", "identifier": "word.exe", "displayName": "Word" },
        { "sourceType": "domain",  "identifier": "docs.google.com", "displayName": "docs.google.com" }
      ]
    }
  ]
}
```

### `POST /api/pursuits`
Create a new Pursuit.

Body:
```json
{
  "name": "Language Learning",
  "category": "learning",
  "color": "#b066ff",
  "weeklyGoalSeconds": 36000
}
```

### `PATCH /api/pursuits/{pursuitId}`
Update name, category, color, or goal. `null` goal removes it.

### `DELETE /api/pursuits/{pursuitId}`
Delete a Pursuit. Its members revert to Uncategorized.

### `POST /api/pursuits/{pursuitId}/members`
Add a member. Body: `{ "sourceType": "program", "identifier": "mpv.exe" }`.
Fails with 409 if this identifier is already a member of another Pursuit
(ADR-003: one member → one Pursuit).

### `DELETE /api/pursuits/{pursuitId}/members/{sourceType}/{identifier}`
Remove a member; it returns to Uncategorized.

Shapes from: ADR-003, ADR-004, ADR-006, ADR-009.

---

### `GET /api/pursuits/untagged?limit=20`
Top unlabeled programs and domains by total time across the last 30 days,
used by the Pursuit setup UI to help users bulk-tag their heaviest unlabeled
apps (the 80/20 tagging approach from ADR-001).

Response:
```json
{
  "candidates": [
    { "sourceType": "program", "identifier": "vscode.exe", "displayName": "VS Code", "last30dSeconds": 145000 },
    { "sourceType": "domain",  "identifier": "github.com", "displayName": "github.com", "last30dSeconds": 32000 }
  ]
}
```
Shapes from: ADR-001.

---

## Implementation ordering

Suggested wiring order (mirrors spec/todo.md priorities, updated for ADRs):

1. `GET /api/daily/overview` — smallest visible win; proves the 4am date
   handling end-to-end (ADR-010).
2. `GET /api/pursuits` + CRUD — must exist before any Pursuit-attributed
   endpoint returns interesting data. Build the setup UI early; dogfood tagging.
3. `GET /api/pursuits/untagged` — powers the bulk-tagging flow.
4. `GET /api/daily/pursuit-timeline` — core product promise.
5. `GET /api/daily/top-programs` — works with raw data; no Pursuit dependency.
6. `GET /api/daily/pursuit-list` — pace indicator.
7. `GET /api/weekly/overview` + `/weekly/daily-breakdown`.
8. `GET /api/weekly/pursuit-scoreboard`.
9. `GET /api/weekly/trend`.
10. Right rail — deferred (ADR-011).

---

## Open implementation questions

Not product decisions — flagged for the engineering plan phase:

- Identifier normalization. `VSCode.exe` vs `vscode.exe` vs `Code.exe` — pick a
  canonical form per platform and apply it on ingest.
- Domain scope. Is `docs.google.com` distinct from `drive.google.com` for
  Pursuit membership, or do we normalize to apex domains? Leaning: full
  hostname, because the user's mental model distinguishes them.
- Where Pursuit category totals for the stat band are computed: at query time
  from the Pursuit table join, or materialised in a daily rollup table?
  Leaning: query time for v1, rollup table only if it proves slow.
- Whether the Pursuit Timeline endpoint returns "sub-blocks" for Uncategorized
  segments so the frontend can render grey-shaded internals, or whether that
  styling data comes from a separate call. Affects payload size.

---

## TODO Tracker (Added 2026-04-12)

Open items that need explicit decisions before endpoint implementation is
considered stable:

- TODO: Day/week boundary migration plan.
  Current production behavior is still Sunday+midnight in multiple places.
  Define how historical data and comparisons migrate to Monday+4am.

- TODO: Canonical `idle` vs `uncategorized` semantics.
  Decide whether `idle` remains a category in the new dashboard model or is
  fully replaced by system-owned Uncategorized behavior.

- TODO: Pursuit data model + schema.
  Specify tables/fields/constraints/indexes for pursuits and memberships,
  including one-member-to-one-pursuit enforcement and delete behavior.

- TODO: Write the attribution pipeline in plain English.
  Document raw logs -> session boundaries -> pursuit attribution ->
  category totals -> endpoint payload flow so endpoint ownership is clear.

- TODO: Context-switch threshold constant and config ownership.
  Choose final threshold value, add it to backend config, and note exactly
  which event stream computes `contextSwitchesPerHour`.

- TODO: Frontend adapter contract for showcase components.
  Define mapping from backend timestamps/seconds to component props
  (`startHour`, `endHour`, labels, durations, and category keys).

- TODO: Endpoint coexistence/cutover plan.
  Document which existing `/api/dashboard/*` endpoints are reused, which are
  replaced, and expected deprecation window.

- TODO: Error and empty-state response contract.
  Define status codes and payload shape for: invalid date/week params,
  timezone mismatch, missing pursuit, conflict on member assignment, and
  no-data windows.

- TODO: Performance budgets and payload-size limits.
  Add target p95 latency and rough payload size ceilings per endpoint
  (daily overview/timeline/top-programs and weekly rollups).

- TODO: Endpoint test acceptance criteria.
  List minimum integration tests required before wiring each endpoint to UI.

- Resolved here: weekly and daily endpoints will use query params.
  This spec already follows that (`?date=...`, `?week=...`, `?weeks=...`).
