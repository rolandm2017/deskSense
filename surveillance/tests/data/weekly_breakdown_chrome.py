from src.object.classes import ChromeSessionData
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.object.classes import ChromeSessionData, ProgramSessionData
from .weekly_breakdown_programs import march_2_2025, march_3_2025

# Sample ChromeSessionData objects
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐 Chrome File 🌐
# Sample ChromeSessionData objects


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
    github_session = ChromeSessionData()
    github_session.domain = "github.comTEST"
    github_session.detail = "Repository setup and initial commits"
    github_session.start_time = add_time(feb_23_2025, 9, 30, 0)
    github_session.end_time = add_time(feb_23_2025, 10, 45, 0)
    github_session.duration = github_session.end_time - github_session.start_time
    github_session.productive = True
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = ChromeSessionData()
    stackoverflow_session.domain = "stackoverflow.comTEST"
    stackoverflow_session.detail = "Research on async database access"
    stackoverflow_session.start_time = add_time(feb_23_2025, 15, 45, 0)
    stackoverflow_session.end_time = add_time(feb_23_2025, 16, 30, 0)
    stackoverflow_session.duration = stackoverflow_session.end_time - \
        stackoverflow_session.start_time
    stackoverflow_session.productive = True
    chrome_sessions.append(stackoverflow_session)

    return chrome_sessions


def chrome_feb_24() -> List:
    chrome_sessions = []

    # Docs session
    docs_session = ChromeSessionData()
    docs_session.domain = "docs.python.orgTEST"
    docs_session.detail = "Reviewing SQLAlchemy documentation"
    docs_session.start_time = add_time(feb_24_2025, 11, 20, 0)
    docs_session.end_time = add_time(feb_24_2025, 12, 15, 0)
    docs_session.duration = docs_session.end_time - docs_session.start_time
    docs_session.productive = True
    chrome_sessions.append(docs_session)

    # YouTube session
    youtube_session = ChromeSessionData()
    youtube_session.domain = "youtube.comTEST"
    youtube_session.detail = "Video tutorial on database optimization"
    youtube_session.start_time = add_time(feb_24_2025, 16, 0, 0)
    youtube_session.end_time = add_time(feb_24_2025, 16, 40, 0)
    youtube_session.duration = youtube_session.end_time - youtube_session.start_time
    youtube_session.productive = True
    chrome_sessions.append(youtube_session)

    return chrome_sessions


def chrome_feb_26() -> List:
    chrome_sessions = []

    # GitHub session
    github_session = ChromeSessionData()
    github_session.domain = "github.comTEST"
    github_session.detail = "Code review and PR discussions"
    github_session.start_time = add_time(feb_26_2025, 9, 15, 0)
    github_session.end_time = add_time(feb_26_2025, 10, 30, 0)
    github_session.duration = github_session.end_time - github_session.start_time
    github_session.productive = True
    chrome_sessions.append(github_session)

    # ChatGPT session
    chatgpt_session = ChromeSessionData()
    chatgpt_session.domain = "chat.openai.comTEST"
    chatgpt_session.detail = "Getting help with test data generation"
    chatgpt_session.start_time = add_time(feb_26_2025, 14, 0, 0)
    chatgpt_session.end_time = add_time(feb_26_2025, 15, 15, 0)
    chatgpt_session.duration = chatgpt_session.end_time - chatgpt_session.start_time
    chatgpt_session.productive = True
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
    github_session = ChromeSessionData()
    github_session.domain = "github.comTEST"
    github_session.detail = "Pull request review"
    github_session.start_time = add_time(march_2_2025, 9, 15, 0)
    github_session.end_time = add_time(march_2_2025, 9, 30, 0)
    github_session.duration = github_session.end_time - github_session.start_time
    github_session.productive = True
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = ChromeSessionData()
    stackoverflow_session.domain = "stackoverflow.comTEST"
    stackoverflow_session.detail = "Researching SQLAlchemy async issues"
    stackoverflow_session.start_time = add_time(march_2_2025, 11, 5, 0)
    stackoverflow_session.end_time = add_time(march_2_2025, 11, 59, 0)
    stackoverflow_session.duration = stackoverflow_session.end_time - \
        stackoverflow_session.start_time
    stackoverflow_session.productive = True
    chrome_sessions.append(stackoverflow_session)

    # YouTube session
    youtube_session = ChromeSessionData()
    youtube_session.domain = "youtube.comTEST"
    youtube_session.detail = "Python async tutorials"
    youtube_session.start_time = add_time(march_2_2025, 13, 0, 0)
    youtube_session.end_time = add_time(march_2_2025, 13, 30, 0)
    youtube_session.duration = youtube_session.end_time - youtube_session.start_time
    youtube_session.productive = True
    chrome_sessions.append(youtube_session)

    # Python docs session
    python_docs_session = ChromeSessionData()
    python_docs_session.domain = "docs.python.orgTEST"
    python_docs_session.detail = "Reading asyncio documentation"
    python_docs_session.start_time = add_time(march_2_2025, 14, 0, 0)
    python_docs_session.end_time = add_time(march_2_2025, 14, 45, 0)
    python_docs_session.duration = python_docs_session.end_time - \
        python_docs_session.start_time
    python_docs_session.productive = True
    chrome_sessions.append(python_docs_session)

    # Gmail session
    gmail_session = ChromeSessionData()
    gmail_session.domain = "mail.google.comTEST"
    gmail_session.detail = "Checking work emails"
    gmail_session.start_time = add_time(march_2_2025, 15, 0, 0)
    gmail_session.end_time = add_time(march_2_2025, 15, 24, 0)
    gmail_session.duration = gmail_session.end_time - gmail_session.start_time
    gmail_session.productive = True
    chrome_sessions.append(gmail_session)

    # ChatGPT session
    chatgpt_session = ChromeSessionData()
    chatgpt_session.domain = "chat.openai.comTEST"
    chatgpt_session.detail = "Debugging code issues"
    chatgpt_session.start_time = add_time(march_2_2025, 16, 0, 0)
    chatgpt_session.end_time = add_time(march_2_2025, 16, 6, 0)
    chatgpt_session.duration = chatgpt_session.end_time - chatgpt_session.start_time
    chatgpt_session.productive = True
    chrome_sessions.append(chatgpt_session)

    return chrome_sessions


def chrome_march_3rd() -> List:
    # March 3, 2025 sessions
    chrome_sessions = []

    # GitHub session day 2
    github_session2 = ChromeSessionData()
    github_session2.domain = "github.comTEST"
    github_session2.detail = "Code review and commits"
    github_session2.start_time = add_time(march_3_2025, 9, 0, 0)
    github_session2.end_time = add_time(march_3_2025, 9, 16, 0)
    github_session2.duration = github_session2.end_time - github_session2.start_time
    github_session2.productive = True
    chrome_sessions.append(github_session2)

    # Jira session
    jira_session = ChromeSessionData()
    jira_session.domain = "jira.company.comTEST"
    jira_session.detail = "Task management and updates"
    jira_session.start_time = add_time(march_3_2025, 11, 15, 0)
    jira_session.end_time = add_time(march_3_2025, 11, 45, 0)
    jira_session.duration = jira_session.end_time - jira_session.start_time
    jira_session.productive = True
    chrome_sessions.append(jira_session)

    # AWS console session
    aws_session = ChromeSessionData()
    aws_session.domain = "aws.amazon.comTEST"
    aws_session.detail = "EC2 instance management"
    aws_session.start_time = add_time(march_3_2025, 13, 30, 0)
    aws_session.end_time = add_time(march_3_2025, 14, 21, 0)
    aws_session.duration = aws_session.end_time - aws_session.start_time
    aws_session.productive = True
    chrome_sessions.append(aws_session)

    # Confluence session
    confluence_session = ChromeSessionData()
    confluence_session.domain = "confluence.company.comTEST"
    confluence_session.detail = "Documentation updates"
    confluence_session.start_time = add_time(march_3_2025, 14, 30, 0)
    confluence_session.end_time = add_time(march_3_2025, 15, 6, 0)
    confluence_session.duration = confluence_session.end_time - \
        confluence_session.start_time
    confluence_session.productive = True
    chrome_sessions.append(confluence_session)

    # YouTube break session
    youtube_break_session = ChromeSessionData()
    youtube_break_session.domain = "youtube.comTEST"
    youtube_break_session.detail = "Short break watching videos"
    youtube_break_session.start_time = add_time(march_3_2025, 15, 15, 0)
    youtube_break_session.end_time = add_time(march_3_2025, 15, 33, 0)
    youtube_break_session.duration = youtube_break_session.end_time - \
        youtube_break_session.start_time
    youtube_break_session.productive = False
    chrome_sessions.append(youtube_break_session)

    # ChatGPT session day 2
    chatgpt_session2 = ChromeSessionData()
    chatgpt_session2.domain = "chat.openai.comTEST"
    chatgpt_session2.detail = "Generating test data"
    chatgpt_session2.start_time = add_time(march_3_2025, 16, 50, 0)
    chatgpt_session2.end_time = add_time(march_3_2025, 17, 24, 0)
    chatgpt_session2.duration = chatgpt_session2.end_time - chatgpt_session2.start_time
    chatgpt_session2.productive = True
    chrome_sessions.append(chatgpt_session2)

    return chrome_sessions


# Four duplicate Chrome session entries
def duplicates_chrome_march_2() -> List:
    duplicate_chrome_sessions = []

    # Duplicate 1: ChatGPT session (with slight time variation)
    chatgpt_session_dup = ChromeSessionData()
    chatgpt_session_dup.domain = "chat.openai.comTEST"
    chatgpt_session_dup.detail = "Asking for coding help"
    chatgpt_session_dup.start_time = add_time(march_2_2025, 15, 30, 0)
    chatgpt_session_dup.end_time = add_time(march_2_2025, 16, 15, 0)
    chatgpt_session_dup.duration = chatgpt_session_dup.end_time - \
        chatgpt_session_dup.start_time
    chatgpt_session_dup.productive = True
    duplicate_chrome_sessions.append(chatgpt_session_dup)

    # Duplicate 2: StackOverflow session (with slight time variation)
    stackoverflow_session_dup = ChromeSessionData()
    stackoverflow_session_dup.domain = "stackoverflow.comTEST"
    stackoverflow_session_dup.detail = "Finding solutions to SQLAlchemy issues"
    stackoverflow_session_dup.start_time = add_time(march_2_2025, 16, 30, 0)
    stackoverflow_session_dup.end_time = add_time(march_2_2025, 17, 15, 0)
    stackoverflow_session_dup.duration = stackoverflow_session_dup.end_time - \
        stackoverflow_session_dup.start_time
    stackoverflow_session_dup.productive = True
    duplicate_chrome_sessions.append(stackoverflow_session_dup)

    return duplicate_chrome_sessions


def duplicates_chrome_march_3rd() -> List:
    duplicate_chrome_sessions = []

    # Duplicate 3: GitHub session (with slight time variation)
    github_session_dup = ChromeSessionData()
    github_session_dup.domain = "github.comTEST"
    github_session_dup.detail = "Repository browsing"
    github_session_dup.start_time = add_time(march_3_2025, 14, 0, 0)
    github_session_dup.end_time = add_time(march_3_2025, 14, 45, 0)
    github_session_dup.duration = github_session_dup.end_time - \
        github_session_dup.start_time
    github_session_dup.productive = True
    duplicate_chrome_sessions.append(github_session_dup)

    # Duplicate 4: YouTube session (with slight time variation)
    youtube_session_dup = ChromeSessionData()
    youtube_session_dup.domain = "youtube.comTEST"
    youtube_session_dup.detail = "Watching programming tutorials"
    youtube_session_dup.start_time = add_time(march_3_2025, 16, 0, 0)
    youtube_session_dup.end_time = add_time(march_3_2025, 16, 45, 0)
    youtube_session_dup.duration = youtube_session_dup.end_time - \
        youtube_session_dup.start_time
    youtube_session_dup.productive = True
    duplicate_chrome_sessions.append(youtube_session_dup)

    return duplicate_chrome_sessions


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
