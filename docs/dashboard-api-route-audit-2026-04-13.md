# Dashboard API Route Audit - 2026-04-13

Purpose: map the current dashboard-facing routes before moving route handlers
out of `activitytracker/src/activitytracker/server.py`.

## Current frontend callers

`dashboard/src/api/getData.api.ts` is the daily legacy dashboard client:

- `GET /api/dashboard/timeline` - today's peripheral audit rows
  (`mouseRows`, `keyboardRows`).
- `GET /api/dashboard/program/summaries` - today's per-program summary totals.
- `GET /api/dashboard/chrome/summaries` - today's per-domain summary totals.
- It also defines report helpers for `/api/report/*`; those are not part of the
  dashboard redesign.

`dashboard/src/api/weekly.api.ts` is the weekly legacy dashboard client:

- Repeats the daily helpers above.
- `GET /api/dashboard/program/summaries/week` - current-week per-program daily
  summary totals.
- `GET /api/dashboard/chrome/summaries/week` - current-week per-domain daily
  summary totals.
- `GET /api/dashboard/timeline/week` - current-week peripheral timeline rows.
- `GET /api/dashboard/programs/usage/timeline` - current-week raw program
  activity timeline.
- `GET /api/dashboard/breakdown/week/{week_of}` - selected-week productivity
  vs leisure breakdown.
- `GET /api/dashboard/timeline/week/{week_of}` - selected-week peripheral
  timeline rows.
- `GET /api/dashboard/chrome/summaries/week/{week_of}` - selected-week
  per-domain daily summary totals.
- `GET /api/dashboard/programs/usage/timeline/{week_of}` - selected-week raw
  program activity timeline.

The current `Home.tsx` page is not purely daily. It shows today's program and
Chrome summaries, but it also pulls current-week peripheral and program
timelines from `weekly.api.ts`.

## Current backend handlers in server.py

Legacy dashboard reads:

- `GET /api/dashboard/timeline` - uses
  `dashboard_service.peripherals.get_timeline_for_today()`. Conceptually daily
  peripheral presence/audit data.
- `GET /api/dashboard/program/summaries` - uses
  `dashboard_service.get_program_summary()`. Conceptually daily program
  Summary data.
- `GET /api/dashboard/chrome/summaries` - uses
  `dashboard_service.get_chrome_summary()`. Conceptually daily domain Summary
  data.
- `GET /api/dashboard/breakdown/week/{week_of}` - uses
  `dashboard_service.get_weekly_productivity_overview(week_of)`. Conceptually
  weekly category-ish rollup, but still based on hardcoded productive app/site
  lists and Sunday week starts.
- `GET /api/dashboard/program/summaries/week` - uses
  `dashboard_service.get_program_summary_weekly()`. Conceptually current-week
  program Summary data.
- `GET /api/dashboard/chrome/summaries/week` - uses
  `dashboard_service.get_chrome_summary_weekly()`. Conceptually current-week
  domain Summary data.
- `GET /api/dashboard/chrome/summaries/week/{week_of}` - uses
  `dashboard_service.get_previous_week_chrome_summary(week_of)`. Conceptually
  selected-week domain Summary data.
- `GET /api/dashboard/timeline/week` - uses
  `dashboard_service.peripherals.get_current_week_timeline()`. Conceptually
  current-week peripheral audit data.
- `GET /api/dashboard/timeline/week/{week_of}` - uses
  `dashboard_service.peripherals.get_specific_week_timeline(week_of)`.
  Conceptually selected-week peripheral audit data.
- `GET /api/dashboard/programs/usage/timeline` - uses
  `dashboard_service.programs.get_current_week_usage_timeline()`. Conceptually
  current-week raw program Activity timeline.
- `GET /api/dashboard/programs/usage/timeline/{week_of}` - uses
  `dashboard_service.programs.get_usage_timeline_for_week(week_of)`.
  Conceptually selected-week raw program Activity timeline.

Other handlers that were still in `server.py` at audit time:

- `GET /api/report/chrome` - removed during the route extraction. It returned
  `None` and had no callers found in `dashboard/`, `chrome/`, or
  `activitytracker/`. `routes/report_routes.py` still defines `GET /report/chrome`
  under its router prefix.
- `POST /api/chrome/tab` and `POST /api/chrome/ignored` - moved to
  `routes/chrome_routes.py`. Chrome ingest routes, not dashboard reads.
- `GET /api/capture/start` - moved to `routes/capture_routes.py`.

New dashboard/showcase routes already exist in
`activitytracker/src/activitytracker/features/charts_showcase/routes.py`:

- `GET /api/daily/active-idle`
- `GET /api/daily/top-activities`

Those use `Activity` in the product sense: program, website/domain, video, or
video channel usage. They are part of the new `/api/daily/*` direction and
should not be mixed into legacy `/api/dashboard/*` route files.

## Proposed route-module split

Keep `server.py` focused on app construction: lifespan, middleware, exception
handlers, and `app.include_router(...)`.

Move existing legacy dashboard handlers first, without changing behavior:

- `activitytracker/src/activitytracker/routes/dashboard_legacy_routes.py`
  - Router: `APIRouter(prefix="/api/dashboard", tags=["dashboard-legacy"], deprecated=True)`
  - Owns every existing `/api/dashboard/*` route until the dashboard migrates.

Then add new product-facing modules as work lands:

- `activitytracker/src/activitytracker/routes/daily_routes.py`
  - Router: `APIRouter(prefix="/api/daily", tags=["daily"])`
  - Owns stable new daily endpoints from `spec/endpoints.md`.
- `activitytracker/src/activitytracker/routes/weekly_routes.py`
  - Router: `APIRouter(prefix="/api/weekly", tags=["weekly"])`
  - Owns stable new weekly endpoints from `spec/endpoints.md`.

Consider later:

- `activitytracker/src/activitytracker/routes/chrome_routes.py`
  - Owns `POST /api/chrome/tab`, `POST /api/chrome/ignored`, and possibly
    the video router include once the ingest surface is cleaned up.
- `activitytracker/src/activitytracker/routes/capture_routes.py`
  - Owns `GET /api/capture/start` if that route survives.

## Migration notes

- Do not rename `/api/dashboard/*` during the first extraction. First move code,
  run tests, and prove behavior is unchanged.
- Preserve audit capabilities during migration:
  - daily program/domain Summary totals;
  - daily and weekly peripheral active rows;
  - weekly program/domain/video/channel time totals once the new Pursuit-aware
    endpoints exist.
- Existing legacy weekly behavior uses Sunday week starts in several places.
  The new `spec/endpoints.md` target is Monday 4am. Treat that as a semantic
  migration, not just a file move.
- The new `/api/daily/active-idle` endpoint answers a different question from
  the legacy `/api/dashboard/timeline`: active vs idle blocks rather than raw
  mouse/keyboard rows. Keep both concepts distinct until the frontend audit UI
  decides which one it needs.
