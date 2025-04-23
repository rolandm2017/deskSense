from datetime import datetime, timedelta

from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime

# ## Order:
# Chrome - Claude
# PyCharm
# Chrome - Claude
# Chrome - StackOverflow
# PyCharm
# Ventrilo
# Chrome - StackOverflow
# Chrome - Twitter.com
# Ventrilo
# PyCharm
# Postman
# Ventrilo
# Chrome - Twitter.com
# Chrome - Claude

# Summary:
# (3) Chrome - Claude
# (3) PyCharm
# (3) Ventrilo
# (2) Chrome - StackOverflow
# (2) Chrome - Twitter.com
# (1) Postman

system_clock = SystemClock()

# ## Chrome
chrome = "Chrome"
stackoverflow = "StackOverflow.com"
twitter = "Twitter"
claude_ai = "Claude.ai"
twitter = "Twitter.com"

# ## Programs
postman = "Postman"
pycharm = "PyCharm"
ventrilo = "Ventrilo"

dt = datetime(2025, 1, 25, 15, 5)

now = system_clock.now()

zero = 0
second_to_last_time_change = 41
final_time_change = 41 + 4
t1 = now + timedelta(minutes=zero)
t2 = now + timedelta(minutes=3)
t3 = now + timedelta(minutes=8)
t4 = now + timedelta(minutes=10)
t5 = now + timedelta(minutes=14)
t6 = now + timedelta(minutes=20)
t7 = now + timedelta(minutes=25)
t8 = now + timedelta(minutes=31)
t9 = now + timedelta(minutes=32)
t10 = now + timedelta(minutes=33)
t11 = now + timedelta(minutes=36)
t12 = now + timedelta(minutes=38)
t13 = now + timedelta(minutes=second_to_last_time_change)
t14 = now + timedelta(minutes=final_time_change)

# see t1 vs t13. t14 is left in the Arbiter, unfinished
difference_between_start_and_2nd_to_last = second_to_last_time_change

times_for_system_clock = [t2, t3, t4, t5,
                          t6, t7, t8, t9, t10, t11, t12, t13, t14]

# times_for_system_clock = [UserLocalTime(t2), UserLocalTime(t3), UserLocalTime(t4), UserLocalTime(t5),
#                           UserLocalTime(t6), UserLocalTime(
#                               t7), UserLocalTime(t8), UserLocalTime(t9),
#                           UserLocalTime(t10), UserLocalTime(
#                               t11), UserLocalTime(t12), UserLocalTime(t13),
#                           UserLocalTime(t14)]


pycharm_path = "C:/pycharm.exe"
pycharm_process = "pycharm.exe"
ventrilo_path = "C:/ventrilo.exe"
vent_process = "ventrilo.exe"


# 1. Chrome - Claude
session1 = ChromeSession(
    claude_ai, "Python code refactoring", UserLocalTime(t1), productive=True)

# 2. Pycharm
session2 = ProgramSession(pycharm_path, pycharm_process,
                          pycharm, "main.py - project_tracker", UserLocalTime(t2), productive=True)

# 3. Chrome - Claude
session3 = ChromeSession(
    claude_ai, "Data structure optimization", UserLocalTime(t3), productive=True)

# 4. Chrome - StackOverflow
session4 = ChromeSession(
    stackoverflow, "Python datetime questions", UserLocalTime(t4), productive=True)

# 5. Pycharm
session5 = ProgramSession(pycharm_path, pycharm_process,
                          pycharm, "utils.py - time formatting functions", UserLocalTime(t5), productive=True)

# 6. Ventrilo
session6 = ProgramSession(ventrilo_path, vent_process,
                          ventrilo, "Python Developers - #help-requests", UserLocalTime(t6), productive=True)

# 7. Chrome - StackOverflow
session7 = ChromeSession(
    stackoverflow, "Python class inheritance", UserLocalTime(t7), productive=True)

# 8. Chrome - Twitter.com
session8 = ChromeSession(twitter, "Tech news feed",
                         UserLocalTime(t8), productive=False)

# 9. Ventrilo
session9 = ProgramSession(ventrilo_path, vent_process,
                          ventrilo, "Python Developers - #off-topic", UserLocalTime(t9), productive=False)

# 10. Pycharm
session10 = ProgramSession(pycharm_path, pycharm_process,
                           pycharm, "session_tracker.py - debugging", UserLocalTime(t10), productive=True)

# 11. Postman
session11 = ProgramSession("C:/Postman.exe", "Postman.exe",
                           postman, "API testing - session endpoints", UserLocalTime(t11), productive=True)

# 12. Ventrilo
session12 = ProgramSession(ventrilo_path, vent_process,
                           ventrilo, "API Development - #general", UserLocalTime(t12), productive=True)

# 13. Chrome - Twitter.com
session13 = ChromeSession(twitter, "Developer threads",
                          UserLocalTime(t13), productive=False)

# 14. Chrome - Claude
session14 = ChromeSession(
    claude_ai, "Code review assistance", UserLocalTime(t14), productive=True)

test_sessions = [session1,
                 session2,
                 session3,
                 session4,
                 session5,
                 session6,
                 session7,
                 session8,
                 session9,
                 session10,
                 session11,
                 session12,
                 session13,
                 session14,
                 ]
