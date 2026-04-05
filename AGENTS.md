# What this app does

It's a time tracker for desktop. One machine only. The goal is to enable self-management. Let the user audit what they actually did.

Originally written so I, an easily distracted person, could be like "WTF I thought I spent all day on that, but it only logged four hours? I'm not doing enough."

So emotionally one goal is to reveal: "I'm not doing enough." This is the negative version. But the upside, the positive is that if you do a lot of hours, the logging will make denial impossible. You'll HAVE to accept that you ACTUALLY DID a lot of input that week: a good thing for your psyche.

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

There was some thought that I might sync data between multiple computers. This was problematic. Firstly it's a lot of work to keep data synchronized! Secondly, users do. not. want. data about how they used their computer flowing to some external source. Thirdly, it's an infohazard: I don't want to suffer a hack.

Instead I might aggregate data and synchronize that, but only aggregation, summaries.

# Key entrypoints

## Activitytracker

**The server entrypoint**

Here is how the server communicates with the dashboard client.

activitytracker\src\activitytracker\server.py


**How tracking of time spent per program or domain occurs**

activitytracker\src\activitytracker\arbiter\activity_arbiter.py

activitytracker\src\activitytracker\arbiter\state_machine.py

Activity Arbiter's transition_state method is the big deal here. The Arbiter controls a "pulse" (a polling activity) adding time to the current activity.

**How Chrome tab activity gets recorded**

activitytracker\src\activitytracker\services\chrome_service.py

In this file you can see how the program eliminates tabs that were only visited briefly from being entered as a session.

**Peripheral tracking**

I write this sentence having abandoned this project nine months ago, so I do not recall exactly why the scripts are like this.

I think it's because they'd otherwise be blocking activities. Something like that. It's a thread issue I'm pretty sure.

activitytracker\src\activitytracker\run_peripherals.py
activitytracker\src\activitytracker\windows_peripherals.py
activitytracker\src\activitytracker\linux_peripherals.py

Agents are welcome to tell me why they think I did it this way. I do not remember but a better solution didn't exist afaik.

## Chrome

Chrome exists to tell the program how I use my time in Chrome. Chrome is a big program with many uses. As numerous as the sites on the web. So it's necessary to differentiate between "I am researching for my thesis on Wikipedia.org" vs "I am doomscrolling on Reddit"

The Chrome extension also *tries* to note how long one spends on a Netflix or YouTube video. The task is reprehensibly difficult due to both services being avoidant of scraping (understandably). 

chrome\src\background.ts is the primary entrypoint. 

chrome\src\backgroundUtil.ts also shows branching between YouTube concerns, Netflix concerns, and regular swaps between active tabs.

## Dashboard

The dashboard is very unfinished, only showing daily and weekly usage. It's also quite slow at loading all the data.

dashboard\src\App.tsx  might be the best entrypoint. 

dashboard\src\pages\Home.tsx shows the homepage. 

dashboard\src\pages\Weekly.tsx shows the weekly view.

# Critical flows

Honestly, the biggest deal happens in the background. In the ideal end result, you double click the .exe, a dashboard shows up, and you just click "Close" and it runs in the background in the system tray.

But say you want to check your data, you either double click the exe again, or you open the dashboard from the system tray. There, you can inspect what you've done that day, or that week. You can see if you completed two hours, or five. 

A to-do might be, "can the user set a minimum threshold for themselves, a goal? per day or per week."

So far, I really only am able to inspect my daily and weekly usage. You can see the usage separated per-activity. That is, there's a linear left-to-right display showing which program was active at which time.

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

It's a nightmare, a trip through hell, trying to prove that the Activity Arbiter works properly. A full integration test proving that the routes work, becomes a long series of intermediate checks, to avoid going insane trying to trace the logic. It is not a simple system. 

To see how complex testing can be, consider: activitytracker\tests\integration\test_arbiter.py

and that is not the worst one.

Another peek at how complex testing can be: activitytracker\tests\integration\program_session_path\test_fresh_entries.py

Again that is not the worst one. I just can't find it right now because I am not familiar with the codebase at the moment.

So in short, the path thru the activity tracker is sensitive and prone to breakage.

# Code style / patterns

Controller, service split.

Prefer to write testable code. Take all the low hanging fruit. Pure functions are great.