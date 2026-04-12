# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeskSense is a personal time-tracking system. It monitors which programs/websites a user spends time on, then displays that data in a dashboard. Single-machine only — no data sync between computers.

Three components:
- **activitytracker/** — Python (FastAPI) backend. Tracks foreground programs, keyboard/mouse activity via a state machine. Owns all timing logic.
- **chrome/** — TypeScript Chrome extension. Reports tab activity (domain, duration) to the backend. Also tracks Netflix/YouTube video watching.
- **dashboard/** — React + TypeScript frontend (Vite). Displays daily/weekly usage charts using d3 and vis-timeline.

## Product context

Before making product-shaped decisions, read in order:
1. `PRODUCT.md` — what the app is, who it's for, core vocabulary
   (Activity, Summary, Pursuit, Category, Uncategorized, Idle).
2. `docs/product-decision-log.md` — ADRs with reasoning behind accepted
   product decisions. Treat as authoritative.
3. `spec/endpoints.md` — current endpoint contract (draft).
4. `spec/todo.md` — deferred decisions and unbuilt areas (auth, licensing,
   user scoping, error contracts).

## API stability map

- **Deprecated (expect to be replaced):** most routes under
  `/api/dashboard/*` in `server.py`. The dashboard redesign (see
  `spec/endpoints.md`) is replacing them with `/api/daily/*` and
  `/api/weekly/*`. Don't build new work on the old routes and don't
  refactor them — they're on their way out. Breaking endpoint changes are
  allowed during this phase. Preferred strategy is reuse-with-alteration
  where practical. Target deprecation window: by end of April 2026.
- **Stable:** peripheral tracking endpoints (keyboard/mouse reports
  under `/api/report/*`). These work well and are expected to stay.
- **In flux:** Chrome extension ingest endpoints (`/api/chrome/*`,
  `/api/chrome/video/*`) — shape may shift as video attribution
  matures, but the purpose is stable.

## Dev Environment Constraints

- Agents run in WSL but npm packages are installed for Windows
- **Agents cannot run npm tests or builds** — they will fail under WSL
- `npm install` must be done outside WSL (in Windows)
- Python tests should be run from WSL via `win-pytest`

This project is developed in WSL but runs on Windows 11. Do not run
`npm install`, `npm run test`, or frontend builds from WSL. Use
`win-pytest` for Python tests.

## Commands

### activitytracker (Python)
```bash
cd activitytracker
pip install -e .                        # install package in editable mode
win-pytest                              # run all tests (WSL -> Windows bridge)
win-pytest tests/path/to/test_file.py
win-pytest tests/path/to/test_file.py::test_name
```

### chrome (TypeScript)
```bash
cd chrome
npm run build          # webpack build
npm run watch          # webpack watch mode
npm run test           # vitest run (all tests)
npm run test:watch     # vitest watch
npm run type-check     # tsc --noEmit
```

### dashboard (React/TypeScript)
```bash
cd dashboard
npm run dev            # vite dev server
npm run build          # tsc + vite build
npm run lint           # eslint
```

## Architecture Notes

### Activity Tracker
- FastAPI server at `activitytracker/src/activitytracker/server.py`
- Central state machine: `arbiter/activity_arbiter.py` and `arbiter/state_machine.py`. The Arbiter's `transition_state` method controls a polling "pulse" that adds time to the current activity.
- Chrome tab deduplication happens in `services/chrome_service.py` (eliminates brief tab visits)
- Peripheral tracking (keyboard/mouse) runs in separate threads: `run_peripherals.py`, `windows_peripherals.py`, `linux_peripherals.py`
- Uses SQLAlchemy with PostgreSQL (`psycopg2-binary`) and Alembic for migrations
- Python formatting: black (line-length 93), isort (profile "black")
- Controller/service split pattern

### Chrome Extension
- Entry point: `src/background.ts` -> `src/backgroundUtil.ts` dispatches between YouTube, Netflix, and regular tab tracking
- Built with webpack, tested with vitest + happy-dom
- `src/api.ts` sends data to the activitytracker backend
- Netflix/YouTube video tracking is complex due to anti-scraping measures on both services

### Dashboard
- React 18 + React Router + Vite
- Entry: `src/App.tsx`, pages at `src/pages/Home.tsx` and `src/pages/Weekly.tsx`
- Styled with Tailwind CSS
- Charts via d3 and vis-timeline

## Invariants

- Backend owns timing logic — the Chrome extension and dashboard are clients only
- High-resolution user activity data never leaves the server
- The Activity Arbiter is the sole authority on what gets logged
- Backend owns user auth

## Testing Pitfalls

The Activity Arbiter integration tests are complex and fragile. They require
long chains of intermediate assertions to trace state machine logic. See
`activitytracker/tests/integration/test_arbiter.py` and
`activitytracker/tests/integration/test_arbiter_after_sleep.py` for examples.
Tread carefully when modifying arbiter behavior.

## Design System
Always read DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag any code that doesn't match DESIGN.md.

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health


## Bugfix guidance for agents

Note that the following instruction only applies to tasks that are specifically about bug fixes. The rule doesn't apply to bugs you encounter while doing developmentw ork.

When fixing a bug, please follow this procedure:

1. Identify the root cause of the bug.
2. Create a test demonstrating the bug in its failure state. That is, when the fix is made, the test should start to pass. So your goal is to write a test that fails, demonstrating the bug.
3. Wait for me to show you the results of the test. You can then implement the fix if the test failed about how you expect.

In this way, the codebase slowly grows protection from regressions.

Again you don't need to follow this rule in the middle of a longer development task. Only follow the rule when I start the chat saying something like, "Hey, let's fix a bug"