# Debug_times.py

An attempt to notice where and when the egregious errors in data collection occur.

I spent 4 hours Monday, 8 hours Friday, 3 hours Saturday. A total of 15 hours.

I look at my time in the program. The reported time is 14 hours, 22 hours, 12 hours.

A problem since mid March.

# audit_odd_times.py

The db had end times that were clearly bogus. End times between midnight and 6 am, when the computer is never used.

The script looks for those values. "When the programmer surely wasn't awake"

# audit_sessions.py

A tool for verifying that the summaries match what the logs say, within a specified tolerance.

This is a TODO.
