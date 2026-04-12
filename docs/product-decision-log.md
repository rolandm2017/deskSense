# Product Decision Log

## minimal template

# ADR-XXX: <Short title>

Status: Proposed | Accepted | Rejected
Date: YYYY-MM-DD

## Context
<What problem or idea led to this decision?>

## Decision
<What are you doing or NOT doing?>

## Why
- <Reason 1>
- <Reason 2>
- <Reason 3>

## Consequences
- <Upside>
- <Downside>

## 🧱 ADR-001: Do not implement predefined app categorization

Status: Accepted
Date: 2026-04-12

Context

We considered automatically categorizing apps (e.g., productive, entertainment, learning, communication) using a predefined list maintained by the app.

Decision

We will not implement a predefined app categorization system.
Users will manually assign categories to apps.

Why
Predefined categories feel non-local → users won’t trust the classifications
Manual tagging aligns better with personal workflows and intent
80/20 rule: users only need to tag a small number of apps anyway
Maintaining a high-quality predefined list would be complex and brittle
Consequences
Slight onboarding friction (users must tag apps themselves)
Higher long-term trust and flexibility
Simpler implementation and fewer edge cases

## 🧱 ADR-002: Target user and product stance

Status: Accepted
Date: 2026-04-12

Context

PRODUCT.md did not name a target user. Clarifying who this is for shapes every feature decision (e.g. invoicing vs. self-reflection).

Decision

DeskSense is a self-management and accountability tool, not a billing tool.
Target users: students tracking study habits, knowledge workers auditing distraction, people running personal deep-work or habit experiments.
Explicit non-goal: freelancer invoicing / client billing (Toggl's territory).

Why
Originating motivation was the author's own question: "how much time am I wasting vs. using well?" and replacing manual tracking of second-language immersion.
Keeps the product generally usable without drifting into invoice/export/client-report feature creep.

Consequences
Features like per-client rates, exportable invoices, and rounding-to-billable-increment are out of scope.
UX can prioritize introspection and comparison-to-self (week vs. last week, goal vs. actual) over external reporting.

## 🧱 ADR-003: "Activity" data model (container of members)

Status: Accepted
Date: 2026-04-12

Context

The showcase dashboard shows user-defined groupings (called "Project" in the mock, "Activity" in product language). Need to pin the data model before writing endpoints.

Decision

An Activity is a user-defined container with:
- name, color, category (exactly one of: productivity, learning, entertainment, communication)
- optional daily/weekly goal seconds
- a list of members, each identified by (source_type, identifier), e.g. (program, "vscode.exe"), (domain, "docs.google.com"), (video_channel, "...").

Rules:
- One member → one Activity (no overlap, for v1). Chrome-style ambiguity is handled by tagging specific domains, not the browser itself.
- An Activity maps to exactly one Category. No double-counting across categories.
- Time not covered by any Activity rolls up as "Uncategorized" and is not counted in any category bucket.

Why
Keeps attribution math unambiguous and avoids per-program special cases.
One new table drives every view (timeline, swim lanes, category breakdown, scoreboard).
Category-on-Activity (not per-block) matches the user's mental model: "my copywriting work is productive."

Consequences
Cannot express "VSCode is sometimes Freelance, sometimes Studying" without splitting by domain or project folder. Accepted tradeoff for v1.
Naming conflict: "activity" is already used in the backend to mean a session of app use (ActivityLog). Resolved in ADR-004.

## 🧱 ADR-004: Name the user-defined grouping "Pursuit"

Status: Accepted
Date: 2026-04-12

Context

The showcase mock called user-defined groupings "Project." That word implies billable/deliverable work, conflicting with ADR-002's self-management stance. "Activity" is taken by existing backend code (ActivityLog, ProgramActivityLog, activity_arbiter).

Decision

The user-defined grouping is called a **Pursuit**.
UI copy, API routes, and new backend types use "pursuit" consistently.
Category names read naturally: "Language Learning is a learning pursuit."

Why
Distinctive — no collision with existing "activity" or "project" code concepts.
Carries the product stance: "what are you pursuing with your time?"
Greppable without false positives.

Consequences
Dashboard copy changes: "Daily project list" → "Daily pursuit list," etc.
New table: pursuits. New endpoints: /pursuits, /pursuits/{id}/members.
Mock data variable names (projectName, etc.) should be renamed during the wiring work to avoid drift.

## 🧱 ADR-005: Dashboard vertical hierarchy — Pursuit Timeline above Top Programs/Websites

Status: Accepted
Date: 2026-04-12

Context

The showcase mock has a single-lane "Daily activity timeline" above a multi-lane "Top programs swim lanes." Both names conflicted with the new Pursuit vocabulary and the underlying data model was unclear.

Decision

Two distinct components, stacked coarse-to-medium:

1. **Pursuit Timeline** (renamed from "Daily activity timeline"). Single lane. Shows which Pursuit was active at each moment. By definition only one Pursuit is active at a time. Backed by the arbiter's session log joined against Pursuit membership. Empty until the user has defined Pursuits.

2. **Top Programs / Websites** (renamed from "Top programs swim lanes"). Three lanes. Top 3 raw programs or domains by total time that day, independent of Pursuits. Each lane's blocks merge sessions of the same program/domain across short gaps so the visual tells a story rather than showing rapid churn.

Why
Hierarchy guides the eye: coarse pursuit story at top, medium program/domain detail below.
Top Programs works on day one with no tagging — the product has value before onboarding.
Pursuit Timeline rewards tagging — it materialises as the user defines Pursuits.
Independent data sources mean one component failing or empty does not hide the other.

Consequences
Need a gap-merging threshold for the Top Programs lanes (pending decision).
Need a first-run empty state for Pursuit Timeline (resolved in ADR-006).
Two endpoints, not one: /daily/pursuit-timeline and /daily/top-programs.

## 🧱 ADR-006: "Uncategorized" as an implicit system Pursuit

Status: Accepted
Date: 2026-04-12

Context

The Pursuit Timeline is empty on day one because the user has not yet defined any Pursuits. Need a first-run experience that is not visually inert and does not require special-case empty-state code.

Decision

Uncategorized is an implicit, always-present, system-owned Pursuit. Every tracked second that is not covered by a user-defined Pursuit is attributed to it. It always renders in the Pursuit Timeline.

Rules:
- Not user-editable: cannot be deleted, renamed, or recolored.
- No goal (daily or weekly).
- No explicit category assignment — Uncategorized time is not counted in any of the four category totals.
- Rendered in neutral grey. Within its timeline segment, individual programs/domains are distinguished by different shades of grayscale or very faint colors so the chart remains readable.

Why
The endpoint never has to handle "no data" — every tracked second is attributed somewhere. The Pursuit Timeline always populates.
Visibly rewards tagging: Uncategorized shrinks as the user defines real Pursuits. Tight feedback loop.
No layout shift when the first real Pursuit is created — the component was already rendering.
Aligns with ADR-003's "time not covered by any Pursuit is Uncategorized."

Consequences
Need a stable ordering so that different grey shades consistently represent the same programs day-to-day (e.g. deterministic by program name hash).
Category totals must continue to exclude Uncategorized time — the stat band can legitimately read "4h tracked, 1h productive, 3h uncategorized" on day one.

## 🧱 ADR-007: Replace "Focus Score" with raw context-switch rate

Status: Accepted
Date: 2026-04-12

Context

The showcase mock displays a "Focus Score" number in the daily stat band. A composite score is aesthetically clean but risks being theater — users can't tell what it rewards or punishes, and it would need tuning to feel meaningful.

Decision

Drop the "Focus Score" concept. Replace that stat-band slot with **context switches per hour** (or per minute — see pending definition), shown as a raw number with units.

Why
Honest and mechanically clear. The user can reason about what moves the number.
Works on day one without Pursuit tagging or goals.
Aligns with the self-management stance (ADR-002) — target users are auditing their own focus patterns, not chasing a gamified number.
Avoids the need to tune a composite formula before the data is even wired up.

Consequences
Need a concrete definition of "context switch" (pending — likely a foreground program change, possibly with a minimum-duration filter to ignore sub-second blips).
Stat band visual needs to accommodate a unit-bearing number rather than a bare integer — minor design adjustment.

## 🧱 ADR-008: Context switch definition and Top Programs block-merging

Status: Accepted
Date: 2026-04-12

Context

Two timing thresholds both touch the arbiter and both shape visual/statistical output. Defining them together because they share the "how aggressively do we smooth noise" question.

Decision

**Context switch (for the stat band metric):**
A context switch is counted when the foreground program changes — OR when the foreground is a browser and the tracked domain changes — and the new thing remains foreground for more than 8 seconds. Brief away-switches of 8 seconds or less do not count.
(Note: the existing codebase already implements a similar away-switch filter at roughly 3s. This ADR raises it to 8s; actual location of the current constant to be confirmed during implementation.)

**Top Programs / Websites block-merging:**
Within a single lane, same-program/same-domain sessions separated by a gap of ≤ 5 minutes are rendered as one merged block. This merging is applied only to the swim-lane visual. The underlying session log and the context-switch count use raw session boundaries.

Both thresholds are backend-owned constants, computed by the arbiter / post-processing service before the data reaches the frontend. The frontend does not re-slice time.

Why
8s away-threshold for switches: filters trivial alt-tabs (reading a Slack ping, glancing at a timer) while still catching genuine app-hopping.
5min lane-merge: conventional "brief interruption" threshold from focus research; matches the author's intuition that swim lanes should tell a readable story rather than show rapid churn.
Backend ownership: preserves CLAUDE.md's invariant that the arbiter owns timing decisions.
Not user-configurable: resist adding settings until users ask.

Consequences
Two constants live in config/, not in the UI.
The 5min merge is a rendering decision applied by the Top Programs endpoint only; other endpoints (session logs, Pursuit Timeline, context-switch count) keep raw boundaries.
Need to find and align the existing 3s away-filter with the new 8s value during implementation.

## 🧱 ADR-009: Pursuit goals — weekly only, with a daily "pace" indicator

Status: Accepted
Date: 2026-04-12

Context

The showcase mock shows goal progress in both the daily pursuit list and the weekly pursuit scoreboard, implying two different goal periods. Need to decide whether goals are daily, weekly, both, or deferred.

Decision

A Pursuit has a single optional goal field: `weekly_goal_seconds`. No separate daily goal.

The daily pursuit list renders a **pace indicator**, not a daily goal bar:
- Computed as `today_actual / (weekly_goal / 7)`.
- Honest framing: "you're at 80% of today's pace toward your weekly goal."
- UI can surface the implicit daily share as a helper line ("about 2h 15m/day").

UI unit convention: hours + minutes ("20h 30m"), collapsing to "20h" when minutes are 0. Stored as seconds in the DB.

Why
Matches the self-management stance (ADR-002). Students and deep-work experimenters plan in weeks, not days; daily goals make weekends weird and create guilt on sick days.
The scoreboard's "delta vs last week" framing is inherently weekly.
One field per Pursuit, not two. Less schema, less UI, less setup decision-fatigue.
Pace framing keeps the daily progress bar meaningful without forcing users to answer a question they don't have an opinion on ("do I care about this Monday specifically?").

Consequences
No per-weekday customization — a user who deliberately studies 5h on weekdays and 0h on weekends sees a skewed pace indicator on weekend days. Accepted; revisit only if users complain.
A Pursuit with no weekly goal shows actuals only, no progress bar, no pace indicator. Goal is opt-in.

## 🧱 ADR-010: Day boundary at 4am local; week starts Monday

Status: Accepted
Date: 2026-04-12

Context

Every daily endpoint references "the selected day," but calendar midnight bisects late-night sessions — a common gotcha that silently corrupts time-tracking dashboards. The target users (ADR-002) include deep-work experimenters and students who routinely work past midnight.

Decision

- A "day" runs from 4:00am local time to 4:00am the next local day. Sessions starting at 2am belong to the *previous* dashboard day.
- A "week" is ISO-style: Monday 4:00am through Monday 4:00am the following week.
- Both boundaries are hardcoded. Not user-configurable.
- Backend owns the bucketing. The frontend passes a date; the query layer translates it into the correct 4am-anchored window.

UI copy requirement: the date picker (and any place showing "today") must include one line or tooltip explaining that days start at 4am, so a user opening the app at 2am Tuesday does not mistake Monday's data for a bug.

Why
Matches how late-night workers actually reason about their day.
4am is standard in time-tracking tools (RescueTime, Toggl, most sleep apps) — almost no one starts work at 4am, so the boundary never bisects a real session.
Monday-start week matches most target users' planning cadence.
Hardcoded preserves ADR-009-era stance of resisting settings until users ask.

Consequences
Every date-bounded query must use the 4am shift, not a naive `DATE()` comparison. Helper function needed in the query layer.
Date picker UI must carry the "days start at 4am" explanatory line once.
DST transitions on the 4am boundary are an edge case — the 4am local wall-clock rule still holds; the underlying UTC offset shifts twice a year. Revisit only if it causes visible artifacts.

## 🧱 ADR-011: Weekly trend chart scope and right-rail deferral

Status: Accepted
Date: 2026-04-12

Context

The weekly trend chart and the right rail are the lowest-priority items in spec/todo.md. Need to pin scope before endpoint design so we don't over-build.

Decision

**Weekly trend chart:**
- Displays 12 weeks of history by default.
- Y-axis: productive seconds only (sum of time in Pursuits whose category is `productivity`). Stacked-by-category visuals already live in the daily breakdown chart.
- Served by one dedicated aggregation endpoint that returns all 12 rollups in a single response. Do not loop the weekly overview endpoint.
- Data retention: the database keeps at least **two years** of history regardless of what the chart renders, so users can look back across longer spans as the app matures.

**Right rail:**
- Stays mocked / static in v1. Not wired against real data.
- Revisit after daily and weekly endpoints are stable and there is enough accumulated real usage to define "peak focus window," "largest idle gap," "notable trend changes," and similar derived insights.

**Platform reminder (surfaced during this discussion, not strictly an ADR but worth logging):**
DeskSense is desktop/laptop only. It will never run on a phone. Internet is used solely for license/payment verification; all tracking and data storage is local. Dashboard design decisions do not need to accommodate mobile viewports.

Why
12 weeks fits a semester — long enough for seasonal patterns, short enough to stay readable on desktop screens.
Two-year retention is cheap (summary tables are small) and gives users a reason to stay with the product across years.
One aggregation endpoint avoids the performance footgun the spec explicitly calls out.
Right rail deferred because each insight is both a small endpoint AND a small editorial decision; neither is worth committing to before real data is flowing.

Consequences
Aggregation query runs over up to ~84 daily rollups per request. Expected to be trivially fast against summary tables.
Retention policy must be explicit in DB maintenance / migration scripts — no aggressive pruning.
Right rail will drift visually from reality for a while. Acceptable for a pre-release product.