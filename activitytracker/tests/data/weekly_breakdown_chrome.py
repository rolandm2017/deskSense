import pytz
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from activitytracker.object.classes import CompletedChromeSession
from activitytracker.util.time_wrappers import UserLocalTime

from .weekly_breakdown_programs import march_2_2025, march_3_2025, weekly_breakdown_tz

# Sample CompletedChromeSession objects
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# Sample CompletedChromeSession objects


def add_time_and_tz(base_date, hours=0, minutes=0, seconds=0):
    """Helper function to add hours, minutes, seconds to a base date. Plus a timezone"""
    result_dt = base_date + \
        timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # Check if datetime is already timezone-aware
    if result_dt.tzinfo is None:
        # It's naive, so localize it with the specified timezone
        result_dt = weekly_breakdown_tz.localize(result_dt)

    return result_dt


# grep -o '\.window_title = "[^"]*"' activitytracker/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 11

# grep -o '\.domain = "[^TEST"]*"' activitytracker/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 10


# Define the base dates
feb_23_2025 = datetime(2025, 2, 23, tzinfo=timezone.utc)
feb_24_2025 = datetime(2025, 2, 24, tzinfo=timezone.utc)
feb_26_2025 = datetime(2025, 2, 26, tzinfo=timezone.utc)


def chrome_feb_23() -> List[CompletedChromeSession]:
    chrome_sessions = []

    # GitHub session
    github_session = CompletedChromeSession("github.comTEST", "Repository setup and initial commits",
                                            UserLocalTime(
                                                add_time_and_tz(feb_23_2025, 9, 30, 0)),
                                            UserLocalTime(
                                                add_time_and_tz(feb_23_2025, 10, 45, 0)),
                                            productive=True,
                                            duration_for_tests=UserLocalTime(add_time_and_tz(
                                                feb_23_2025, 10, 45, 0)) - UserLocalTime(add_time_and_tz(feb_23_2025, 9, 30, 0)))
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = CompletedChromeSession("stackoverflow.comTEST", "Research on async database access",
                                                   UserLocalTime(
                                                       add_time_and_tz(feb_23_2025, 15, 45, 0)),
                                                   UserLocalTime(
                                                       add_time_and_tz(feb_23_2025, 16, 30, 0)),
                                                   productive=True,
                                                   duration_for_tests=UserLocalTime(add_time_and_tz(
                                                       feb_23_2025, 16, 30, 0)) - UserLocalTime(add_time_and_tz(feb_23_2025, 15, 45, 0)))
    chrome_sessions.append(stackoverflow_session)

    return chrome_sessions


def chrome_feb_24() -> List[CompletedChromeSession]:
    chrome_sessions = []

    # Docs session
    docs_session = CompletedChromeSession("docs.python.orgTEST", "Reviewing SQLAlchemy documentation",
                                          UserLocalTime(
                                              add_time_and_tz(feb_24_2025, 11, 20, 0)),
                                          UserLocalTime(
                                              add_time_and_tz(feb_24_2025, 12, 15, 0)),
                                          productive=True,
                                          duration_for_tests=UserLocalTime(add_time_and_tz(
                                              feb_24_2025, 12, 15, 0)) - UserLocalTime(add_time_and_tz(feb_24_2025, 11, 20, 0)))
    chrome_sessions.append(docs_session)

    # YouTube session
    youtube_session = CompletedChromeSession("youtube.comTEST", "Video tutorial on database optimization",
                                             UserLocalTime(
                                                 add_time_and_tz(feb_24_2025, 16, 0, 0)),
                                             UserLocalTime(
                                                 add_time_and_tz(feb_24_2025, 16, 40, 0)),
                                             productive=True,
                                             duration_for_tests=UserLocalTime(add_time_and_tz(
                                                 feb_24_2025, 16, 40, 0)) - UserLocalTime(add_time_and_tz(feb_24_2025, 16, 0, 0)))
    chrome_sessions.append(youtube_session)

    return chrome_sessions


def chrome_feb_26() -> List[CompletedChromeSession]:
    chrome_sessions = []

    # GitHub session
    github_session = CompletedChromeSession("github.comTEST", "Code review and PR discussions",
                                            UserLocalTime(
                                                add_time_and_tz(feb_26_2025, 9, 15, 0)),
                                            UserLocalTime(
                                                add_time_and_tz(feb_26_2025, 10, 30, 0)),
                                            productive=True,
                                            duration_for_tests=UserLocalTime(add_time_and_tz(
                                                feb_26_2025, 10, 30, 0)) - UserLocalTime(add_time_and_tz(feb_26_2025, 9, 15, 0)))
    chrome_sessions.append(github_session)

    # ChatGPT session
    chatgpt_session = CompletedChromeSession("chat.openai.comTEST", "Getting help with test data generation",
                                             UserLocalTime(
                                                 add_time_and_tz(feb_26_2025, 14, 0, 0)),
                                             UserLocalTime(
                                                 add_time_and_tz(feb_26_2025, 15, 15, 0)),
                                             productive=True,
                                             duration_for_tests=UserLocalTime(add_time_and_tz(
                                                 feb_26_2025, 15, 15, 0)) - UserLocalTime(add_time_and_tz(feb_26_2025, 14, 0, 0)))
    chrome_sessions.append(chatgpt_session)

    return chrome_sessions


# Count for reference
feb_23_chrome_count = len(chrome_feb_23())
feb_24_chrome_count = len(chrome_feb_24())
feb_26_chrome_count = len(chrome_feb_26())

feb_chrome_count = feb_23_chrome_count + \
    feb_24_chrome_count + feb_26_chrome_count

unique_domains = 10  # in march


def chrome_march_2nd() -> List[CompletedChromeSession]:
    chrome_sessions = []

    # March 2, 2025 sessions

    # GitHub session
    github_session = CompletedChromeSession("github.comTEST", "Pull request review",
                                            UserLocalTime(
                                                add_time_and_tz(march_2_2025, 9, 15, 0)),
                                            UserLocalTime(
                                                add_time_and_tz(march_2_2025, 9, 30, 0)),
                                            productive=True,
                                            duration_for_tests=UserLocalTime(add_time_and_tz(
                                                march_2_2025, 9, 30, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 9, 15, 0)))
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = CompletedChromeSession("stackoverflow.comTEST", "Researching SQLAlchemy async issues",
                                                   UserLocalTime(
                                                       add_time_and_tz(march_2_2025, 11, 5, 0)),
                                                   UserLocalTime(
                                                       add_time_and_tz(march_2_2025, 11, 59, 0)),
                                                   productive=True,
                                                   duration_for_tests=UserLocalTime(add_time_and_tz(
                                                       march_2_2025, 11, 59, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 11, 5, 0)))
    chrome_sessions.append(stackoverflow_session)

    # YouTube session
    youtube_session = CompletedChromeSession("youtube.comTEST", "Python async tutorials",
                                             UserLocalTime(
                                                 add_time_and_tz(march_2_2025, 13, 0, 0)),
                                             UserLocalTime(
                                                 add_time_and_tz(march_2_2025, 13, 30, 0)),
                                             productive=True,
                                             duration_for_tests=UserLocalTime(add_time_and_tz(
                                                 march_2_2025, 13, 30, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 13, 0, 0)))
    chrome_sessions.append(youtube_session)

    # Python docs session
    python_docs_session = CompletedChromeSession("docs.python.orgTEST", "Reading asyncio documentation",
                                                 UserLocalTime(
                                                     add_time_and_tz(march_2_2025, 14, 0, 0)),
                                                 UserLocalTime(
                                                     add_time_and_tz(march_2_2025, 14, 45, 0)),
                                                 productive=True,
                                                 duration_for_tests=UserLocalTime(add_time_and_tz(
                                                     march_2_2025, 14, 45, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 14, 0, 0)))
    chrome_sessions.append(python_docs_session)

    # Gmail session
    gmail_session = CompletedChromeSession("mail.google.comTEST", "Checking work emails",
                                           UserLocalTime(
                                               add_time_and_tz(march_2_2025, 15, 0, 0)),
                                           UserLocalTime(
                                               add_time_and_tz(march_2_2025, 15, 24, 0)),
                                           productive=True,
                                           duration_for_tests=UserLocalTime(add_time_and_tz(
                                               march_2_2025, 15, 24, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 15, 0, 0)))
    chrome_sessions.append(gmail_session)

    # ChatGPT session
    chatgpt_session = CompletedChromeSession("chat.openai.comTEST", "Debugging code issues",
                                             UserLocalTime(
                                                 add_time_and_tz(march_2_2025, 16, 0, 0)),
                                             UserLocalTime(
                                                 add_time_and_tz(march_2_2025, 16, 6, 0)),
                                             productive=True,
                                             duration_for_tests=UserLocalTime(add_time_and_tz(
                                                 march_2_2025, 16, 6, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 16, 0, 0)))
    chrome_sessions.append(chatgpt_session)

    return chrome_sessions


def chrome_march_3rd() -> List[CompletedChromeSession]:
    # March 3, 2025 sessions
    chrome_sessions = []

    # GitHub session day 2
    github_session2 = CompletedChromeSession("github.comTEST", "Code review and commits",
                                             UserLocalTime(
                                                 add_time_and_tz(march_3_2025, 9, 0, 0)),
                                             UserLocalTime(
                                                 add_time_and_tz(march_3_2025, 9, 16, 0)),
                                             productive=True,
                                             duration_for_tests=UserLocalTime(add_time_and_tz(
                                                 march_3_2025, 9, 16, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 9, 0, 0)))
    chrome_sessions.append(github_session2)

    # Jira session
    jira_session = CompletedChromeSession("jira.company.comTEST", "Task management and updates",
                                          UserLocalTime(
                                              add_time_and_tz(march_3_2025, 11, 15, 0)),
                                          UserLocalTime(
                                              add_time_and_tz(march_3_2025, 11, 45, 0)),
                                          productive=True,
                                          duration_for_tests=UserLocalTime(add_time_and_tz(
                                              march_3_2025, 11, 45, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 11, 15, 0)))
    chrome_sessions.append(jira_session)

    # AWS console session
    aws_session = CompletedChromeSession("aws.amazon.comTEST", "EC2 instance management",
                                         UserLocalTime(
                                             add_time_and_tz(march_3_2025, 13, 30, 0)),
                                         UserLocalTime(
                                             add_time_and_tz(march_3_2025, 14, 21, 0)),
                                         productive=True,
                                         duration_for_tests=UserLocalTime(add_time_and_tz(
                                             march_3_2025, 14, 21, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 13, 30, 0)))
    chrome_sessions.append(aws_session)

    # Confluence session
    confluence_session = CompletedChromeSession("confluence.company.comTEST", "Documentation updates",
                                                UserLocalTime(
                                                    add_time_and_tz(march_3_2025, 14, 30, 0)),
                                                UserLocalTime(
                                                    add_time_and_tz(march_3_2025, 15, 6, 0)),
                                                productive=True,
                                                duration_for_tests=UserLocalTime(add_time_and_tz(
                                                    march_3_2025, 15, 6, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 14, 30, 0)))
    chrome_sessions.append(confluence_session)

    # YouTube break session
    youtube_break_session = CompletedChromeSession("youtube.comTEST", "Short break watching videos",
                                                   UserLocalTime(
                                                       add_time_and_tz(march_3_2025, 15, 15, 0)),
                                                   UserLocalTime(
                                                       add_time_and_tz(march_3_2025, 15, 33, 0)),
                                                   productive=False,
                                                   duration_for_tests=UserLocalTime(add_time_and_tz(
                                                       march_3_2025, 15, 33, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 15, 15, 0)))
    chrome_sessions.append(youtube_break_session)

    # ChatGPT session day 2
    chatgpt_session2 = CompletedChromeSession("chat.openai.comTEST", "Generating test data",
                                              UserLocalTime(
                                                  add_time_and_tz(march_3_2025, 16, 50, 0)),
                                              UserLocalTime(
                                                  add_time_and_tz(march_3_2025, 17, 24, 0)),
                                              productive=True,
                                              duration_for_tests=UserLocalTime(add_time_and_tz(
                                                  march_3_2025, 17, 24, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 16, 50, 0)))
    chrome_sessions.append(chatgpt_session2)

    return chrome_sessions


# Four duplicate Chrome session entries
def duplicates_chrome_march_2() -> List[CompletedChromeSession]:
    duplicate_chrome_sessions = []

    # Duplicate 1: ChatGPT session (with slight time variation)
    chatgpt_session_dup = CompletedChromeSession("chat.openai.comTEST", "Asking for coding help",
                                                 UserLocalTime(
                                                     add_time_and_tz(march_2_2025, 15, 30, 0)),
                                                 UserLocalTime(
                                                     add_time_and_tz(march_2_2025, 16, 15, 0)),
                                                 productive=True,
                                                 duration_for_tests=UserLocalTime(add_time_and_tz(
                                                     march_2_2025, 16, 15, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 15, 30, 0)))
    duplicate_chrome_sessions.append(chatgpt_session_dup)

    # Duplicate 2: StackOverflow session (with slight time variation)
    stackoverflow_session_dup = CompletedChromeSession("stackoverflow.comTEST", "Finding solutions to SQLAlchemy issues",
                                                       UserLocalTime(add_time_and_tz(
                                                           march_2_2025, 16, 30, 0)),
                                                       UserLocalTime(add_time_and_tz(
                                                           march_2_2025, 17, 15, 0)),
                                                       productive=True,
                                                       duration_for_tests=UserLocalTime(add_time_and_tz(
                                                           march_2_2025, 17, 15, 0)) - UserLocalTime(add_time_and_tz(march_2_2025, 16, 30, 0)))
    duplicate_chrome_sessions.append(stackoverflow_session_dup)

    return duplicate_chrome_sessions


def duplicates_chrome_march_3rd() -> List[CompletedChromeSession]:
    duplicate_chrome_sessions = []

    # Duplicate 3: GitHub session (with slight time variation)
    github_session_dup = CompletedChromeSession("github.comTEST", "Repository browsing",
                                                UserLocalTime(
                                                    add_time_and_tz(march_3_2025, 14, 0, 0)),
                                                UserLocalTime(
                                                    add_time_and_tz(march_3_2025, 14, 45, 0)),
                                                productive=True,
                                                duration_for_tests=UserLocalTime(add_time_and_tz(
                                                    march_3_2025, 14, 45, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 14, 0, 0)))
    duplicate_chrome_sessions.append(github_session_dup)

    # Duplicate 4: YouTube session (with slight time variation)
    youtube_session_dup = CompletedChromeSession("youtube.comTEST", "Watching programming tutorials",
                                                 UserLocalTime(
                                                     add_time_and_tz(march_3_2025, 16, 0, 0)),
                                                 UserLocalTime(
                                                     add_time_and_tz(march_3_2025, 16, 45, 0)),
                                                 productive=True,
                                                 duration_for_tests=UserLocalTime(add_time_and_tz(
                                                     march_3_2025, 16, 45, 0)) - UserLocalTime(add_time_and_tz(march_3_2025, 16, 0, 0)))
    duplicate_chrome_sessions.append(youtube_session_dup)

    return duplicate_chrome_sessions


unique_domains = 10  # in march

# counted manually from Ctrl + F "t_time = add_time_and_tz(march_2_2"
march_2_chrome_count = len(chrome_march_2nd())
march_3_chrome_count = len(chrome_march_3rd())
