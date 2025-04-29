# Terms

A window: Probably refers to the duration of time used in the KeepAliveEngine. A session active for 44 seconds uses 4.4 windows. The duration of a window might change later: Check the config file.

Window push: The DAOs adding ten sec to a session's time. Keeps the recorded time close to accurate even if the computer shuts down, the power goes off.

Deductions: When the session is finished, part of the window is consumed, but part of it isn't. The deduction removes the unused part of the window from the entry in the db.

A cycle: The KeepAliveEngine runs for i loops before resetting. A cycle is one group of i loops, from the start of the reset until the next reset.
