from datetime import datetime, timedelta

from src.object.classes import ProgramSessionData, ChromeSessionData

from src.util.clock import SystemClock

# ## Order:
# Chrome - Claude
# VSCode
# Chrome - Claude
# Chrome - StackOverflow
# VSCode
# Discord
# Chrome - StackOverflow
# Chrome - Twitter.com
# Discord
# VSCode
# Postman
# Discord
# Chrome - Twitter.com
# Chrome - Claude

# Summary:
# (3) Chrome - Claude
# (3) VSCode
# (3) Discord
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
vscode = "VSCode"
discord = "Discord"

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
session1 = ChromeSessionData()
session1.domain = claude_ai
session1.detail = "Python code refactoring"
session1.start_time = t1
session1.productive = True

# 2. VSCode
session2 = ProgramSessionData()
session2.window_title = vscode
session2.detail = "main.py - project_tracker"
session2.start_time = t2
session2.productive = True

# 3. Chrome - Claude
session3 = ChromeSessionData()
session3.domain = claude_ai
session3.detail = "Data structure optimization"
session3.start_time = t3
session3.productive = True

# 4. Chrome - StackOverflow
session4 = ChromeSessionData()
session4.domain = stackoverflow
session4.detail = "Python datetime questions"
session4.start_time = t4
session4.productive = True

# 5. VSCode
session5 = ProgramSessionData()
session5.window_title = vscode
session5.detail = "utils.py - time formatting functions"
session5.start_time = t5
session5.productive = True

# 6. Discord
session6 = ProgramSessionData()
session6.window_title = discord
session6.detail = "Python Developers - #help-requests"
session6.start_time = t6
session6.productive = True

# 7. Chrome - StackOverflow
session7 = ChromeSessionData()
session7.domain = stackoverflow
session7.detail = "Python class inheritance"
session7.start_time = t7
session7.productive = True

# 8. Chrome - Twitter.com
session8 = ChromeSessionData()
session8.domain = twitter
session8.detail = "Tech news feed"
session8.start_time = t8
session8.productive = False

# 9. Discord
session9 = ProgramSessionData()
session9.window_title = discord
session9.detail = "Python Developers - #off-topic"
session9.start_time = t9
session9.productive = False

# 10. VSCode
session10 = ProgramSessionData()
session10.window_title = vscode
session10.detail = "session_tracker.py - debugging"
session10.start_time = t10
session10.productive = True

# 11. Postman
session11 = ProgramSessionData()
session11.window_title = "Postman"
session11.detail = "API testing - session endpoints"
session11.start_time = t11
session11.productive = True

# 12. Discord
session12 = ProgramSessionData()
session12.window_title = discord
session12.detail = "API Development - #general"
session12.start_time = t12
session12.productive = True

# 13. Chrome - Twitter.com
session13 = ChromeSessionData()
session13.domain = twitter
session13.detail = "Developer threads"
session13.start_time = t13
session13.productive = False

# 14. Chrome - Claude
session14 = ChromeSessionData()
session14.domain = claude_ai
session14.detail = "Code review assistance"
session14.start_time = t14
session14.productive = True

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
