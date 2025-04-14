from datetime import datetime, timedelta

from surveillance.src.object.classes import ProgramSessionData, ChromeSessionData

from surveillance.src.util.clock import SystemClock

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
t13 = now + timedelta(minutes=41)
t14 = now + timedelta(minutes=45)

times_for_system_clock = [t2, t3, t4, t5,
                          t6, t7, t8, t9, t10, t11, t12, t13, t14]


# 1. Chrome - Claude
session1 = ChromeSessionData(claude_ai, "Python code refactoring", t1, productive=True)

# 2. Pycharm
session2 = ProgramSessionData(pycharm, "main.py - project_tracker", t2, productive=True)

# 3. Chrome - Claude
session3 = ChromeSessionData(claude_ai, "Data structure optimization", t3, productive=True)

# 4. Chrome - StackOverflow
session4 = ChromeSessionData(stackoverflow, "Python datetime questions", t4, productive=True)

# 5. Pycharm
session5 = ProgramSessionData(pycharm, "utils.py - time formatting functions", t5, productive=True)

# 6. Ventrilo
session6 = ProgramSessionData(ventrilo, "Python Developers - #help-requests", t6, productive=True)

# 7. Chrome - StackOverflow
session7 = ChromeSessionData(stackoverflow, "Python class inheritance", t7, productive=True)

# 8. Chrome - Twitter.com
session8 = ChromeSessionData(twitter, "Tech news feed", t8, productive=False)

# 9. Ventrilo
session9 = ProgramSessionData(ventrilo, "Python Developers - #off-topic", t9, productive=False)

# 10. Pycharm
session10 = ProgramSessionData(pycharm, "session_tracker.py - debugging", t10, productive=True)

# 11. Postman
session11 = ProgramSessionData(postman, "API testing - session endpoints", t11, productive=True)

# 12. Ventrilo
session12 = ProgramSessionData(ventrilo, "API Development - #general", t12, productive=True)

# 13. Chrome - Twitter.com
session13 = ChromeSessionData(twitter, "Developer threads", t13, productive=False)

# 14. Chrome - Claude
session14 = ChromeSessionData(claude_ai, "Code review assistance", t14, productive=True)

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
