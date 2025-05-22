import pytz
from datetime import datetime, timedelta

from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime

timezone_for_test = "Asia/Tokyo"  # UTC +9

tokyo_tz = pytz.timezone(timezone_for_test)


# ## Order:
# Chrome - Claude
# PyCharm
# Chrome - Claude
# Chrome - StackOverflow
# PyCharm
# Ventrilo

# Summary:
# (2) Chrome - Claude
# (2) PyCharm
# (1) Ventrilo
# (1) Chrome - StackOverflow


# ## Chrome
chrome = "Chrome"
stackoverflow = "StackOverflow.com"
claude_ai = "Claude.ai"

# ## Programs
pycharm = "PyCharm"
ventrilo = "Ventrilo"

early_morning = tokyo_tz.localize(datetime(2025, 4, 1, 0, 0, 0))

zero = 0
second_to_last_time_change = 8
final_time_change = second_to_last_time_change + 1
t1 = early_morning + timedelta(minutes=zero)
t2 = early_morning + timedelta(minutes=1)
t3 = early_morning + timedelta(minutes=2, seconds=2)
# the "c" indicates it concludes
t4c = early_morning + timedelta(minutes=2, seconds=49)
# Say it ends at t4
# Computer goes to sleep for 3:10
t5 = early_morning + timedelta(hours=3, minutes=12, seconds=30)
t6 = early_morning + timedelta(hours=3, minutes=13)
t7 = early_morning + timedelta(hours=3, minutes=13, seconds=35)

minutes_between_start_and_2nd_to_last = second_to_last_time_change
minutes_between_start_and_final_time_change = final_time_change

# t4 not included
times_for_system_clock = [t2, t3, t5, t6, t7]

just_before_sleep = tokyo_tz.localize

u1 = t3
u2 = u1 + timedelta(seconds=10)
u3 = u1 + timedelta(seconds=20)
# Final time before the gap to be used to conclude
# the session just before the sleep occurred
u4a = u1 + timedelta(seconds=30)
# t5: just after the sleep event
u5 = t5
u6 = u5 + timedelta(seconds=10)

times_for_status_dao_clock = [
    UserLocalTime(u1),
    UserLocalTime(u2),
    UserLocalTime(u3),
    UserLocalTime(u4a),
    UserLocalTime(u5),
    UserLocalTime(u6),
]

test_events_elapsed_time_in_sec = (t7 - t1).total_seconds()


times_for_system_clock_as_ult = [
    UserLocalTime(t2),
    UserLocalTime(t3),
    UserLocalTime(t4c),
    UserLocalTime(t5),
    UserLocalTime(t6),
    UserLocalTime(t7),
]


pycharm_path = "C:/pycharm.exe"
pycharm_process = "pycharm.exe"

ventrilo_path = "C:/ventrilo.exe"
vent_process = "ventrilo.exe"


# 1. Chrome - Claude
session1 = ChromeSession(
    claude_ai, "Python code refactoring", UserLocalTime(t1), productive=True
)

# 2. Pycharm
session2 = ProgramSession(
    pycharm_path,
    pycharm_process,
    pycharm,
    "main.py - project_tracker",
    UserLocalTime(t2),
    productive=True,
)

# 3. Chrome - Claude
session3 = ChromeSession(
    claude_ai, "Data structure optimization", UserLocalTime(t3), productive=True
)

# 4. Chrome - StackOverflow
session4 = ChromeSession(
    stackoverflow, "Python datetime questions", UserLocalTime(t5), productive=True
)

# 5. Pycharm
session5 = ProgramSession(
    pycharm_path,
    pycharm_process,
    pycharm,
    "utils.py - time formatting functions",
    UserLocalTime(t6),
    productive=True,
)

# 6. Ventrilo
session6 = ProgramSession(
    ventrilo_path,
    vent_process,
    ventrilo,
    "Python Developers - #help-requests",
    UserLocalTime(t7),
    productive=True,
)


# Start by doing a deepcopy so integration test A doesn't influence integration test B
test_sleep_sessions = [
    session1,
    session2,
    session3,
    session4,
    session5,
    session6,
]
