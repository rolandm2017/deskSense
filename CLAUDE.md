# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeskSense is a personal time-tracking system. It monitors which programs/websites a user spends time on, then displays that data in a dashboard. Single-machine only — no data sync between computers.

Three components:
- **activitytracker/** — Python (FastAPI) backend. Tracks foreground programs, keyboard/mouse activity via a state machine. Owns all timing logic.
- **chrome/** — TypeScript Chrome extension. Reports tab activity (domain, duration) to the backend. Also tracks Netflix/YouTube video watching.
- **dashboard/** — React + TypeScript frontend (Vite). Displays daily/weekly usage charts using d3 and vis-timeline.

## Dev Environment Constraints

- Agents run in WSL but npm packages are installed for Windows
- **Agents cannot run npm tests or builds** — they will fail under WSL
- `npm install` must be done outside WSL (in Windows)
- Python tests can be run from WSL

## Commands

### activitytracker (Python)
```bash
cd activitytracker
pip install -e .                        # install package in editable mode
pytest                                  # run all tests (pythonpath=src via pytest.ini)
pytest tests/path/to/test_file.py       # run single test file
pytest tests/path/to/test_file.py::test_name  # run single test
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

The Activity Arbiter integration tests are complex and fragile. They require long chains of intermediate assertions to trace state machine logic. See `activitytracker/tests/integration/test_arbiter.py` and `activitytracker/tests/integration/program_session_path/test_fresh_entries.py` for examples. Tread carefully when modifying arbiter behavior.
