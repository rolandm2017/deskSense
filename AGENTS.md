# What this app does

It's a time tracker for desktop. One machine only. The goal is to enable self-management. Let the user audit what they actually did.

## Product context

For the product stance, target users, and core vocabulary (Activity,
Summary, Pursuit, Category, Uncategorized, Idle), see `PRODUCT.md`.
For product decisions and their reasoning, see
`docs/product-decision-log.md`. For deferred / unbuilt areas (auth,
license gating, user scoping, error contracts), see `spec/todo.md`. This
file covers the codebase itself; don't duplicate product content here.

Agents should always read PRODUCT.md to start.

## Some timeline context re: app development

I worked on this app for about five months, around Spring 2025. I quit developing it around May. I have picked development back up in April of 2026. Thus I have an eleven month gap of forgetfulness to overcome. I no longer remember the system in great detail, and numerous rationales for design decisions are lost.

## Environment

You are within WSL.

Use `win-pytest` to run Python tests from WSL. `win-pytest` is a WSL ->
Windows bridge script that runs pytest inside the Windows virtualenv.
Do not run `npm` tests/builds from WSL.

I also recently added: 

`alias git='/mnt/c/Program\ Files/Git/bin/git.exe'` 

So that agents can use Windows 11 git from within WSL. This avoids having to do stuff like
```bash
Ran git --git-dir=/mnt/c/Users/roly/Code/desksense/.git/worktrees/dsTests --work-tree=/mnt/c/
  │ users/roly/code/dstests diff --check -- activitytracker/src/activitytracker/arbiter/
  │ activity_arbiter.py activitytracker/src/activitytracker/arbiter/session_polling.py
```

# How to run the program

## Setup for the activityTracker server

- make a virtual environment
- enter the venv
- run "pip install -r .\windows-requirements.txt"
- OR on linux, run "pip install -r .\requirements.txt

cd C:\Users\roly\Code\desksense\activitytracker
pip install -e .

- populate the virual env. variables

(.desk) PS C:\Users\roly\Code\desksense\activitytracker> python src/activitytracker/server.py

OR for hot reload:

(.desk) PS C:\Users\roly\Code\desksense\activitytracker> uvicorn src.activitytracker.server:app --reload

## Setup for the peripherals

Just run `python src/activitytracker/run_peripherals.py` with the virtual env active

## Setup for Chrome extension

npm install, npm run build.

entrypoint is the src/background.ts file.

## Dashboard

- make an .env file with VITE_API_URL=http://localhost:5173

npm install, npm run dev 

go to localhost:5173

entrypoint: dashboard\src\pages\Home.tsx

# Architecture

## activitytracker

The activitytracker folder is a python server that handles somewhat large amounts of input data from the system. The tracker tracks when you're typing, when you're using your mouse, what program you have in the foreground, how long the window is active.

Everything feeds into a central state machine. The state machine controls a timer making logs into a database. The idea is that the recorder is constantly monitoring what you are doing. 

The polling is also built such that if you turn your machine off without closing the program, worst case scenario is that the time tracker logs five seconds that didn't actually occur. Zero significance.

## chrome

The Chrome folder is a tracker that logs which website you're on and for how long.

There is a pipeline that nullifies tabs you only visit briefly, i.e. when a user presses Ctrl + PgUp or Ctrl + PgDn 10x in 5 sec to change from tab N to tab N - 5. That way there isn't a spam of 20 ms visits for the tracker to process.

## dashboard

The dashboard folder allows the user to view their data. A chart is used to show a beautiful display (under construction right now, but it'll get there) of how they used their time. Let them know they spent n minutes on entertainment this week, k minutes scrolling, v minutes working on their current project.

A later goal is to enable downloading of a nice spreadsheet for the user to view, in case they wish to stock it in a folder somewhere.

# What the project isn't

No cross-machine data sync. Only aggregated summaries may leave the server.

# Key entrypoints

## Activitytracker

Paths are presented with forward slashes as they would appear in Linux.

**The server entrypoint**

Here is how the server communicates with the dashboard client.

activitytracker/src/activitytracker/server.py

NOTE: most routes currently in `server.py` under `/api/dashboard/*` are
done for. The dashboard redesign replaces them with `/api/daily/*` and
`/api/weekly/*` (see `spec/endpoints.md`). Don't build new work on the
old routes. The peripheral report routes (`/api/report/*`) and the
Chrome ingest routes are staying.
Breaking endpoint changes are allowed during this transition. Preferred
strategy is reuse-with-alteration where practical. Target: deprecate most
`/api/dashboard/*` routes by end of April 2026.
For the current route inventory and proposed extraction split, see
`docs/dashboard-api-route-audit-2026-04-13.md`.


**How tracking of time spent per program or domain occurs**

activitytracker/src/activitytracker/arbiter/activity_arbiter.py

activitytracker/src/activitytracker/arbiter/state_machine.py

Activity Arbiter's transition_state method is the big deal here. The Arbiter controls a "pulse" (a polling activity) adding time to the current activity.

The arbiter's session log is continuous and non-overlapping by
construction — at most one Activity is active at a time, and the pulse
guarantees coverage of every tracked second. Endpoints that need a
"what was happening at time T" view (e.g. the Pursuit Timeline) can
read this log directly without gap-stitching logic.

**How Chrome tab activity gets recorded**

activitytracker/src/activitytracker/services/chrome_service.py

In this file you can see how the program eliminates tabs that were only visited briefly from being entered as a session.

**Peripheral tracking**


activitytracker/src/activitytracker/run_peripherals.py
activitytracker/src/activitytracker/windows_peripherals.py
activitytracker/src/activitytracker/linux_peripherals.py


## Chrome

Chrome exists to tell the program how the user uses their time in Chrome. Web browsing divides itself up into numerous subtasks, so it's necessary to track which domain is being used.

The Chrome extension *tries* to note how long one spends on a Netflix or YouTube video. The task is difficult due to both services being avoidant of scraping (understandably). 

chrome\src\background.ts is the primary entrypoint. 

chrome\src\backgroundUtil.ts also shows branching between YouTube concerns, Netflix concerns, and regular swaps between active tabs.

## Dashboard

The dashboard is very unfinished, only showing daily and weekly usage. It's also quite slow at loading all the data.

dashboard\src\App.tsx  might be the best entrypoint. 

dashboard\src\pages\Home.tsx shows the homepage. 

dashboard\src\pages\Weekly.tsx shows the weekly view.

# Critical flows

1. The program detects a program's usage. Activation info is sent to the Arbiter. The arbiter starts counting. This continues until something else displaces the current activity. During the count, database writes occur every pulse. At the conclusion of a session, the program attempts to edit out unused time from the window's final pulse, for precision.

2. Chrome tab changes -> extension debounces -> sends domain + duration to backend -> chrome_service filters brief
  visits -> arbiter logs session

3. "User opens dashboard" -> frontend calls FastAPI endpoints -> queries DB for time ranges -> returns aggregated
  sessions

TODO: document the full source-of-truth attribution pipeline in plain
English (ingest -> arbiter/session boundaries -> pursuit attribution ->
category rollups -> endpoint payloads). This is currently underdefined and
should become a standing architecture section.

# How the Chrome extension talks to the backend

API requests are made by the extension and received by the server.py file in activitytracker/src. 

The program does not have documented shared contracts as of yet, but endpoints are inferrable by reading the top thirty lines of chrome\src\api.ts.

# Database setup

The database connection is established in activitytracker\src\activitytracker\db\database.py.

# Data model

## Three-tier hierarchy

DeskSense has three conceptual tiers. Keep them distinct when reasoning
about a change. Vocabulary definitions live in `PRODUCT.md`; this
section maps them to code.

1. **Activity** — individual session records. One foreground window
   interval, one domain visit, one video watch. `ActivityLogBase` and
   its children (currently still named SummaryLogBase in some places —
   ongoing rename). Raw truth produced by the arbiter and the Chrome
   extension.
2. **Summary** — per-day rollups of Activities, per program / domain /
   video. `DailyProgramSummary`, `DailyDomainSummary`,
   `DailyVideoSummary` all extend `DailySummaryBase` (hours spent on a
   given day as a float). Fast to query; what most dashboard endpoints
   read. The DailySummary names are staying.
3. **Pursuit** — user-defined grouping of Activities tracked under one
   umbrella (see `PRODUCT.md` for the full definition). A Pursuit's
   members are (source_type, identifier) pairs: `program`, `domain`, or
   `video_channel`. Program, domain, and video Activities all feed
   into Pursuits. New table — being designed. See `spec/endpoints.md`
   and ADR-003 / ADR-004.

## Peripheral data (parallel to the hierarchy)

Used for idle detection and activity-density visualizations, not
Pursuit attribution:

- **TimelineEntryObj** — precomputes mouse and keyboard usage.
  Compresses thousands of events down to a hundred or so.
- **MouseMove** — individual sessions of mouse movement.
- **TypingSessions** — instances of continuous typing. Both may be
  very short. Data originates in the peripheral trackers.
- **PrecomputedTimelineEntry** — merges graph units in advance so the
  server sends ~1/20th as many entries to the client.
- **SystemStatus** — tracks when the machine is on/off via polling.

## Naming confusion

Fixing the Activity / Summary naming is the #1 to-do. The DailySummary
models keep their names; SummaryLogBase and its child classes are
being renamed to Activities.

A **TimelineEntryObj** exists to precompute mouse and keyboard usage. Compresses thousands of events down to a hundred or so. 

**MouseMove** exists to log individual sessions of moving the mouse. **TypingSessions** are instances where the user typed continuously. Both these sessions may be very short. Their data originates in the peripheral trackers.

**PrecomputedTimelineEntry** exists so that graph data can be merged into larger units in advance. This way, the server can send ~1/20th as many entries to the client to be graphed. That is, five usages of the mouse over one minute, two sec long each, punctuated by ten seconds of rest, can be merged into one long unit before sending.

The **SystemStatus** table helps the program track when the machine is actually on or off. Writes occur via polling.

# Dev constraints

- Intended to run on Windows and Linux. 
- npm install must be done outside of WSL
- Agents must assume they are in WSL
- Python tests can be run from WSL via `win-pytest`
- Frontend tests/builds should be run from Windows, not WSL

# Invariants

- Backend owns timing logic.
- High resolution data about what the user did with their time never leaves the server.
- You *really* only need the Internet connection active to prove you're paying for the service, or at least subscribed.
- The backend owns user auth.
- The Activity Arbiter makes decisions about what is and isn't being logged.

# What breaks easily

It's difficult to prove that the Activity Arbiter works properly. A full integration test proving that the routes work, becomes a long series of intermediate checks, to avoid losing the thread several times trying to trace the logic. It is not a simple system. 

To see how complex testing can be, consider: activitytracker\tests\integration\test_arbiter.py

Another peek at sensitive flows: activitytracker\tests\integration\test_arbiter_after_sleep.py

So in short, the path thru the activity tracker is sensitive and prone to breakage.

The Chrome extension's efforts to record YouTube and Netflix watch time is also prone to breakage. It's also impossible to write integration tests for these sites as it is equivalent to botting.

# Error handling

What happens when the Chrome extension can't reach the backend? The issue is not handled yet. Expect that it basically breaks for now, probably throwing many errors. 

The program has not yet been shipped to a production build. As such you cannot expect to see runtime errors. 

# Code style / patterns

Controller, service split.

Prefer to write testable code. Take all the low hanging fruit. Pure functions are great.

# What are the project's future goals?

1. Enable a desktop app using Tauri.

2. Enable a user auth gate: require login to use the app.

3. Enhance the dashboard so that users get value from having their system tracked.

# The state of my tests

As of Feb 28 2026, I've had tests that are well well maintained for several ongoing months. Think that 99% of test cases pass. Hence you can trust a test to document how the code works.

Testing philosophy: tests all the way down, within reason. Very high-level
E2E is often out of scope; confidence should come from well-chosen
integration tests plus contract tests.

## Guidance for Codex and Claude Code agents

When fixing a bug, please follow this procedure:

1. Identify the root cause of the bug.
2. Create a test demonstrating the bug in its failure state. That is, when the fix is made, the test should start to pass. So your goal is to write a test that fails, demonstrating the bug.
3. Wait for me to show you the results of the test. You can then implement the fix if the test failed about how you expect.

In this way, the codebase slowly grows protection from regressions.
