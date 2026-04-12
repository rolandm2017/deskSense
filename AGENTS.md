# What this app does

It's a time tracker for desktop. One machine only. The goal is to enable self-management. Let the user audit what they actually did.

## Some timeline context re: app development

I worked on this app for about five months, around Spring 2025. I quit developing it around May. I have picked development back up in April of 2026. Thus I have an eleven month gap of forgetfulness to overcome. I no longer remember the system in great detail, and numerous rationales for design decisions are lost.

## Environment

This project is developed in WSL but runs on Windows 11. You cannot run `npm install`, `npm run test`, or `pytest` directly from WSL - ask the user to run these commands.

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


**How tracking of time spent per program or domain occurs**

activitytracker/src/activitytracker/arbiter/activity_arbiter.py

activitytracker/src/activitytracker/arbiter/state_machine.py

Activity Arbiter's transition_state method is the big deal here. The Arbiter controls a "pulse" (a polling activity) adding time to the current activity.

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

# How the Chrome extension talks to the backend

API requests are made by the extension and received by the server.py file in activitytracker/src. 

The program does not have documented shared contracts as of yet, but endpoints are inferrable by reading the top thirty lines of chrome\src\api.ts.

# Database setup

The database connection is established in activitytracker\src\activitytracker\db\database.py.

# Data model

There are models that record the individual session of using a program, be it for a ten minute window or a five second window. There is another model that then summarizes how much time was used total that day, per program. This also applies to domains and video content.

There is some naming confusion currently. Fixing it is my #1 to do.

A **ActivityLogBase** exists to record an individual session or activity. 

**DailySummaryBase** is a base class covering hours spent and the data data was gathered, summarized into one float representation of hours spent. This Base extends into a DailyProgramSummary, DailyDomainSummary, DailyVideoSummary. There, the extension exists to specify which website or program was being used, for how long. The DailyVideoSummary covers a question of media categorization. 

In my move to fix the naming confusion, the DailySummary models will keep their names. SummaryLogBase and its child classes will be renamed as Activities.

A **TimelineEntryObj** exists to precompute mouse and keyboard usage. Compresses thousands of events down to a hundred or so. 

**MouseMove** exists to log individual sessions of moving the mouse. **TypingSessions** are instances where the user typed continuously. Both these sessions may be very short. Their data originates in the peripheral trackers.

**PrecomputedTimelineEntry** exists so that graph data can be merged into larger units in advance. This way, the server can send ~1/20th as many entries to the client to be graphed. That is, five usages of the mouse over one minute, two sec long each, punctuated by ten seconds of rest, can be merged into one long unit before sending.

The **SystemStatus** table helps the program track when the machine is actually on or off. Writes occur via polling.

# Dev constraints

- Intended to run on Windows and Linux. 
- npm install must be done outside of WSL
- Agents must assume they are in WSL
- Agents cannot run tests themselves; it'll just break because the npm packages are for Windows.

# Invariants

- Backend owns timing logic.
- High resolution data about what the user did with their time never leaves the server.
- You *really* only need the Internet connection active to prove you're paying for the service, or at least subscribed.
- The backend owns user auth.
- The Activity Arbiter makes decisions about what is and isn't being logged.

# What breaks easily

It's difficult to prove that the Activity Arbiter works properly. A full integration test proving that the routes work, becomes a long series of intermediate checks, to avoid losing the thread several times trying to trace the logic. It is not a simple system. 

To see how complex testing can be, consider: activitytracker\tests\integration\test_arbiter.py

Another peek at how complex testing can be: activitytracker\tests\integration\program_session_path\test_fresh_entries.py

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

## Guidance for Codex and Claude Code agents

When fixing a bug, please follow this procedure:

1. Identify the root cause of the bug.
2. Create a test demonstrating the bug in its failure state. That is, when the fix is made, the test should start to pass. So your goal is to write a test that fails, demonstrating the bug.
3. Wait for me to show you the results of the test. You can then implement the fix if the test failed about how you expect.

In this way, the codebase slowly grows protection from regressions.