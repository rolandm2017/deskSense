from surveillance.src.object.classes import ChromeSession
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from surveillance.src.object.classes import ChromeSession, ProgramSession
from .weekly_breakdown_programs import march_2_2025, march_3_2025

# Sample ChromeSession objects
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# Sample ChromeSession objects


def add_time(base_date, hours=0, minutes=0, seconds=0):
    """Helper function to add hours, minutes, seconds to a base date"""
    return base_date + timedelta(hours=hours, minutes=minutes, seconds=seconds)


# grep -o '\.window_title = "[^"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 11

# grep -o '\.domain = "[^TEST"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 10


# Define the base dates
feb_23_2025 = datetime(2025, 2, 23, tzinfo=timezone.utc)
feb_24_2025 = datetime(2025, 2, 24, tzinfo=timezone.utc)
feb_26_2025 = datetime(2025, 2, 26, tzinfo=timezone.utc)


def chrome_feb_23() -> List:
    chrome_sessions = []

    # GitHub session
    github_session = ChromeSession("github.comTEST", "Repository setup and initial commits",
                                   add_time(feb_23_2025, 9, 30, 0),
                                   add_time(feb_23_2025, 10, 45, 0),
                                   productive=True,
                                   duration_for_tests=add_time(feb_23_2025, 10, 45, 0) - add_time(feb_23_2025, 9, 30, 0))
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = ChromeSession("stackoverflow.comTEST", "Research on async database access",
                                          add_time(feb_23_2025, 15, 45, 0),
                                          add_time(feb_23_2025, 16, 30, 0),
                                          productive=True,
                                          duration_for_tests=add_time(feb_23_2025, 16, 30, 0) - add_time(feb_23_2025, 15, 45, 0))
    chrome_sessions.append(stackoverflow_session)

    return chrome_sessions


def chrome_feb_24() -> List:
    chrome_sessions = []

    # Docs session
    docs_session = ChromeSession("docs.python.orgTEST", "Reviewing SQLAlchemy documentation",
                                 add_time(feb_24_2025, 11, 20, 0),
                                 add_time(feb_24_2025, 12, 15, 0),
                                 productive=True,
                                 duration_for_tests=add_time(feb_24_2025, 12, 15, 0) - add_time(feb_24_2025, 11, 20, 0))
    chrome_sessions.append(docs_session)

    # YouTube session
    youtube_session = ChromeSession("youtube.comTEST", "Video tutorial on database optimization",
                                    add_time(feb_24_2025, 16, 0, 0),
                                    add_time(feb_24_2025, 16, 40, 0),
                                    productive=True,
                                    duration_for_tests=add_time(feb_24_2025, 16, 40, 0) - add_time(feb_24_2025, 16, 0, 0))
    chrome_sessions.append(youtube_session)

    return chrome_sessions


def chrome_feb_26() -> List:
    chrome_sessions = []

    # GitHub session
    github_session = ChromeSession("github.comTEST", "Code review and PR discussions",
                                   add_time(feb_26_2025, 9, 15, 0),
                                   add_time(feb_26_2025, 10, 30, 0),
                                   productive=True,
                                   duration_for_tests=add_time(feb_26_2025, 10, 30, 0) - add_time(feb_26_2025, 9, 15, 0))
    chrome_sessions.append(github_session)

    # ChatGPT session
    chatgpt_session = ChromeSession("chat.openai.comTEST", "Getting help with test data generation",
                                    add_time(feb_26_2025, 14, 0, 0),
                                    add_time(feb_26_2025, 15, 15, 0),
                                    productive=True,
                                    duration_for_tests=add_time(feb_26_2025, 15, 15, 0) - add_time(feb_26_2025, 14, 0, 0))
    chrome_sessions.append(chatgpt_session)

    return chrome_sessions


# Count for reference
feb_23_chrome_count = len(chrome_feb_23())
feb_24_chrome_count = len(chrome_feb_24())
feb_26_chrome_count = len(chrome_feb_26())

feb_chrome_count = feb_23_chrome_count + \
    feb_24_chrome_count + feb_26_chrome_count

unique_domains = 10  # in march


def chrome_march_2nd() -> List:
    chrome_sessions = []

    # March 2, 2025 sessions

    # GitHub session
    github_session = ChromeSession("github.comTEST", "Pull request review",
                                   add_time(march_2_2025, 9, 15, 0),
                                   add_time(march_2_2025, 9, 30, 0),
                                   productive=True,
                                   duration_for_tests=add_time(march_2_2025, 9, 30, 0) - add_time(march_2_2025, 9, 15, 0))
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = ChromeSession("stackoverflow.comTEST", "Researching SQLAlchemy async issues",
                                          add_time(march_2_2025, 11, 5, 0),
                                          add_time(march_2_2025, 11, 59, 0),
                                          productive=True,
                                          duration_for_tests=add_time(march_2_2025, 11, 59, 0) - add_time(march_2_2025, 11, 5, 0))
    chrome_sessions.append(stackoverflow_session)

    # YouTube session
    youtube_session = ChromeSession("youtube.comTEST", "Python async tutorials",
                                    add_time(march_2_2025, 13, 0, 0),
                                    add_time(march_2_2025, 13, 30, 0),
                                    productive=True,
                                    duration_for_tests=add_time(march_2_2025, 13, 30, 0) - add_time(march_2_2025, 13, 0, 0))
    chrome_sessions.append(youtube_session)

    # Python docs session
    python_docs_session = ChromeSession("docs.python.orgTEST", "Reading asyncio documentation",
                                        add_time(march_2_2025, 14, 0, 0),
                                        add_time(march_2_2025, 14, 45, 0),
                                        productive=True,
                                        duration_for_tests=add_time(march_2_2025, 14, 45, 0) - add_time(march_2_2025, 14, 0, 0))
    chrome_sessions.append(python_docs_session)

    # Gmail session
    gmail_session = ChromeSession("mail.google.comTEST", "Checking work emails",
                                  add_time(march_2_2025, 15, 0, 0),
                                  add_time(march_2_2025, 15, 24, 0),
                                  productive=True,
                                  duration_for_tests=add_time(march_2_2025, 15, 24, 0) - add_time(march_2_2025, 15, 0, 0))
    chrome_sessions.append(gmail_session)

    # ChatGPT session
    chatgpt_session = ChromeSession("chat.openai.comTEST", "Debugging code issues",
                                    add_time(march_2_2025, 16, 0, 0),
                                    add_time(march_2_2025, 16, 6, 0),
                                    productive=True,
                                    duration_for_tests=add_time(march_2_2025, 16, 6, 0) - add_time(march_2_2025, 16, 0, 0))
    chrome_sessions.append(chatgpt_session)

    return chrome_sessions


def chrome_march_3rd() -> List:
    # March 3, 2025 sessions
    chrome_sessions = []

    # GitHub session day 2
    github_session2 = ChromeSession("github.comTEST", "Code review and commits",
                                    add_time(march_3_2025, 9, 0, 0),
                                    add_time(march_3_2025, 9, 16, 0),
                                    productive=True,
                                    duration_for_tests=add_time(march_3_2025, 9, 16, 0) - add_time(march_3_2025, 9, 0, 0))
    chrome_sessions.append(github_session2)

    # Jira session
    jira_session = ChromeSession("jira.company.comTEST", "Task management and updates",
                                 add_time(march_3_2025, 11, 15, 0),
                                 add_time(march_3_2025, 11, 45, 0),
                                 productive=True,
                                 duration_for_tests=add_time(march_3_2025, 11, 45, 0) - add_time(march_3_2025, 11, 15, 0))
    chrome_sessions.append(jira_session)

    # AWS console session
    aws_session = ChromeSession("aws.amazon.comTEST", "EC2 instance management",
                                add_time(march_3_2025, 13, 30, 0),
                                add_time(march_3_2025, 14, 21, 0),
                                productive=True,
                                duration_for_tests=add_time(march_3_2025, 14, 21, 0) - add_time(march_3_2025, 13, 30, 0))
    chrome_sessions.append(aws_session)

    # Confluence session
    confluence_session = ChromeSession("confluence.company.comTEST", "Documentation updates",
                                       add_time(march_3_2025, 14, 30, 0),
                                       add_time(march_3_2025, 15, 6, 0),
                                       productive=True,
                                       duration_for_tests=add_time(march_3_2025, 15, 6, 0) - add_time(march_3_2025, 14, 30, 0))
    chrome_sessions.append(confluence_session)

    # YouTube break session
    youtube_break_session = ChromeSession("youtube.comTEST", "Short break watching videos",
                                          add_time(march_3_2025, 15, 15, 0),
                                          add_time(march_3_2025, 15, 33, 0),
                                          productive=False,
                                          duration_for_tests=add_time(march_3_2025, 15, 33, 0) - add_time(march_3_2025, 15, 15, 0))
    chrome_sessions.append(youtube_break_session)

    # ChatGPT session day 2
    chatgpt_session2 = ChromeSession("chat.openai.comTEST", "Generating test data",
                                     add_time(march_3_2025, 16, 50, 0),
                                     add_time(march_3_2025, 17, 24, 0),
                                     productive=True,
                                     duration_for_tests=add_time(march_3_2025, 17, 24, 0) - add_time(march_3_2025, 16, 50, 0))
    chrome_sessions.append(chatgpt_session2)

    return chrome_sessions


# Four duplicate Chrome session entries
def duplicates_chrome_march_2() -> List:
    duplicate_chrome_sessions = []

    # Duplicate 1: ChatGPT session (with slight time variation)
    chatgpt_session_dup = ChromeSession("chat.openai.comTEST", "Asking for coding help",
                                        add_time(march_2_2025, 15, 30, 0),
                                        add_time(march_2_2025, 16, 15, 0),
                                        productive=True,
                                        duration_for_tests=add_time(march_2_2025, 16, 15, 0) - add_time(march_2_2025, 15, 30, 0))
    duplicate_chrome_sessions.append(chatgpt_session_dup)

    # Duplicate 2: StackOverflow session (with slight time variation)
    stackoverflow_session_dup = ChromeSession("stackoverflow.comTEST", "Finding solutions to SQLAlchemy issues",
                                              add_time(
                                                  march_2_2025, 16, 30, 0),
                                              add_time(
                                                  march_2_2025, 17, 15, 0),
                                              productive=True,
                                              duration_for_tests=add_time(march_2_2025, 17, 15, 0) - add_time(march_2_2025, 16, 30, 0))
    duplicate_chrome_sessions.append(stackoverflow_session_dup)

    return duplicate_chrome_sessions


def duplicates_chrome_march_3rd() -> List:
    duplicate_chrome_sessions = []

    # Duplicate 3: GitHub session (with slight time variation)
    github_session_dup = ChromeSession("github.comTEST", "Repository browsing",
                                       add_time(march_3_2025, 14, 0, 0),
                                       add_time(march_3_2025, 14, 45, 0),
                                       productive=True,
                                       duration_for_tests=add_time(march_3_2025, 14, 45, 0) - add_time(march_3_2025, 14, 0, 0))
    duplicate_chrome_sessions.append(github_session_dup)

    # Duplicate 4: YouTube session (with slight time variation)
    youtube_session_dup = ChromeSession("youtube.comTEST", "Watching programming tutorials",
                                        add_time(march_3_2025, 16, 0, 0),
                                        add_time(march_3_2025, 16, 45, 0),
                                        productive=True,
                                        duration_for_tests=add_time(march_3_2025, 16, 45, 0) - add_time(march_3_2025, 16, 0, 0))
    duplicate_chrome_sessions.append(youtube_session_dup)

    return duplicate_chrome_sessions


unique_domains = 10  # in march

# counted manually from Ctrl + F "t_time = add_time(march_2_2"
march_2_chrome_count = len(chrome_march_2nd())
march_3_chrome_count = len(chrome_march_3rd())


# Example usage:
#
# chrome_sessions = create_chrome_session_test_data()
# program_sessions = create_program_session_test_data()
#
# print(f"Generated {len(chrome_sessions)} Chrome sessions")
# print(f"Generated {len(program_sessions)} Program sessions")
#
# # Example of how you might use these with your DAOs:
# async def test_chrome_summary_dao():
#     # Set up test dependencies like session_maker, logging_dao, etc.
#     chrome_logging_dao = MockChromeLoggingDao()
#     session_maker = get_test_session_maker()
#     chrome_dao = ChromeSummaryDao(chrome_logging_dao, session_maker)
#
#     # Current test time - use a fixed time for deterministic tests
#     now = datetime(2025, 3, 3, 19, 0, 0, tzinfo=timezone.utc)
#
#     # Process all test chrome sessions
#     for session in chrome_sessions:
#         await chrome_dao.create_if_new_else_update(session, now)
#
#     # Then assert expected state in database
#     # ...
