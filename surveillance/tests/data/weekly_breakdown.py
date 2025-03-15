from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.object.classes import ChromeSessionData, ProgramSessionData

# Sample ChromeSessionData objects


def create_chrome_session_test_data() -> List:
    chrome_sessions = []

    # March 2, 2025 sessions

    # GitHub session
    github_session = ChromeSessionData()
    github_session.domain = "github.com"
    github_session.detail = "Pull request review"
    github_session.start_time = datetime(
        2025, 3, 2, 9, 15, 0, tzinfo=timezone.utc)
    github_session.end_time = datetime(
        2025, 3, 2, 11, 0, 0, tzinfo=timezone.utc)
    github_session.duration = github_session.end_time - github_session.start_time
    github_session.productive = True
    chrome_sessions.append(github_session)

    # StackOverflow session
    stackoverflow_session = ChromeSessionData()
    stackoverflow_session.domain = "stackoverflow.com"
    stackoverflow_session.detail = "Researching SQLAlchemy async issues"
    stackoverflow_session.start_time = datetime(
        2025, 3, 2, 11, 5, 0, tzinfo=timezone.utc)
    stackoverflow_session.end_time = datetime(
        2025, 3, 2, 11, 59, 0, tzinfo=timezone.utc)
    stackoverflow_session.duration = stackoverflow_session.end_time - \
        stackoverflow_session.start_time
    stackoverflow_session.productive = True
    chrome_sessions.append(stackoverflow_session)

    # YouTube session
    youtube_session = ChromeSessionData()
    youtube_session.domain = "youtube.com"
    youtube_session.detail = "Python async tutorials"
    youtube_session.start_time = datetime(
        2025, 3, 2, 13, 0, 0, tzinfo=timezone.utc)
    youtube_session.end_time = datetime(
        2025, 3, 2, 13, 30, 0, tzinfo=timezone.utc)
    youtube_session.duration = youtube_session.end_time - youtube_session.start_time
    youtube_session.productive = True
    chrome_sessions.append(youtube_session)

    # Python docs session
    python_docs_session = ChromeSessionData()
    python_docs_session.domain = "docs.python.org"
    python_docs_session.detail = "Reading asyncio documentation"
    python_docs_session.start_time = datetime(
        2025, 3, 2, 14, 0, 0, tzinfo=timezone.utc)
    python_docs_session.end_time = datetime(
        2025, 3, 2, 14, 45, 0, tzinfo=timezone.utc)
    python_docs_session.duration = python_docs_session.end_time - \
        python_docs_session.start_time
    python_docs_session.productive = True
    chrome_sessions.append(python_docs_session)

    # Gmail session
    gmail_session = ChromeSessionData()
    gmail_session.domain = "mail.google.com"
    gmail_session.detail = "Checking work emails"
    gmail_session.start_time = datetime(
        2025, 3, 2, 15, 0, 0, tzinfo=timezone.utc)
    gmail_session.end_time = datetime(
        2025, 3, 2, 15, 24, 0, tzinfo=timezone.utc)
    gmail_session.duration = gmail_session.end_time - gmail_session.start_time
    gmail_session.productive = True
    chrome_sessions.append(gmail_session)

    # ChatGPT session
    chatgpt_session = ChromeSessionData()
    chatgpt_session.domain = "chat.openai.com"
    chatgpt_session.detail = "Debugging code issues"
    chatgpt_session.start_time = datetime(
        2025, 3, 2, 16, 0, 0, tzinfo=timezone.utc)
    chatgpt_session.end_time = datetime(
        2025, 3, 2, 17, 6, 0, tzinfo=timezone.utc)
    chatgpt_session.duration = chatgpt_session.end_time - chatgpt_session.start_time
    chatgpt_session.productive = True
    chrome_sessions.append(chatgpt_session)

    # March 3, 2025 sessions

    # GitHub session day 2
    github_session2 = ChromeSessionData()
    github_session2.domain = "github.com"
    github_session2.detail = "Code review and commits"
    github_session2.start_time = datetime(
        2025, 3, 3, 9, 0, 0, tzinfo=timezone.utc)
    github_session2.end_time = datetime(
        2025, 3, 3, 11, 6, 0, tzinfo=timezone.utc)
    github_session2.duration = github_session2.end_time - github_session2.start_time
    github_session2.productive = True
    chrome_sessions.append(github_session2)

    # Jira session
    jira_session = ChromeSessionData()
    jira_session.domain = "jira.company.com"
    jira_session.detail = "Task management and updates"
    jira_session.start_time = datetime(
        2025, 3, 3, 11, 15, 0, tzinfo=timezone.utc)
    jira_session.end_time = datetime(
        2025, 3, 3, 12, 45, 0, tzinfo=timezone.utc)
    jira_session.duration = jira_session.end_time - jira_session.start_time
    jira_session.productive = True
    chrome_sessions.append(jira_session)

    # AWS console session
    aws_session = ChromeSessionData()
    aws_session.domain = "aws.amazon.com"
    aws_session.detail = "EC2 instance management"
    aws_session.start_time = datetime(
        2025, 3, 3, 13, 30, 0, tzinfo=timezone.utc)
    aws_session.end_time = datetime(2025, 3, 3, 14, 21, 0, tzinfo=timezone.utc)
    aws_session.duration = aws_session.end_time - aws_session.start_time
    aws_session.productive = True
    chrome_sessions.append(aws_session)

    # Confluence session
    confluence_session = ChromeSessionData()
    confluence_session.domain = "confluence.company.com"
    confluence_session.detail = "Documentation updates"
    confluence_session.start_time = datetime(
        2025, 3, 3, 14, 30, 0, tzinfo=timezone.utc)
    confluence_session.end_time = datetime(
        2025, 3, 3, 15, 6, 0, tzinfo=timezone.utc)
    confluence_session.duration = confluence_session.end_time - \
        confluence_session.start_time
    confluence_session.productive = True
    chrome_sessions.append(confluence_session)

    # YouTube break session
    youtube_break_session = ChromeSessionData()
    youtube_break_session.domain = "youtube.com"
    youtube_break_session.detail = "Short break watching videos"
    youtube_break_session.start_time = datetime(
        2025, 3, 3, 15, 15, 0, tzinfo=timezone.utc)
    youtube_break_session.end_time = datetime(
        2025, 3, 3, 15, 33, 0, tzinfo=timezone.utc)
    youtube_break_session.duration = youtube_break_session.end_time - \
        youtube_break_session.start_time
    youtube_break_session.productive = False
    chrome_sessions.append(youtube_break_session)

    # ChatGPT session day 2
    chatgpt_session2 = ChromeSessionData()
    chatgpt_session2.domain = "chat.openai.com"
    chatgpt_session2.detail = "Generating test data"
    chatgpt_session2.start_time = datetime(
        2025, 3, 3, 16, 0, 0, tzinfo=timezone.utc)
    chatgpt_session2.end_time = datetime(
        2025, 3, 3, 17, 24, 0, tzinfo=timezone.utc)
    chatgpt_session2.duration = chatgpt_session2.end_time - chatgpt_session2.start_time
    chatgpt_session2.productive = True
    chrome_sessions.append(chatgpt_session2)

    return chrome_sessions


# Sample ProgramSessionData objects
def create_program_session_test_data() -> List:
    program_sessions = []

    # March 2, 2025 sessions

    # VSCode session
    vscode_session = ProgramSessionData()
    vscode_session.window_title = "Visual Studio Code"
    vscode_session.detail = "Working on async SQLAlchemy project"
    vscode_session.start_time = datetime(
        2025, 3, 2, 9, 0, 0, tzinfo=timezone.utc)
    vscode_session.end_time = datetime(
        2025, 3, 2, 11, 45, 0, tzinfo=timezone.utc)
    vscode_session.duration = vscode_session.end_time - vscode_session.start_time
    vscode_session.productive = True
    program_sessions.append(vscode_session)

    # Excel session
    excel_session = ProgramSessionData()
    excel_session.window_title = "Microsoft Excel"
    excel_session.detail = "Data analysis for project metrics"
    excel_session.start_time = datetime(
        2025, 3, 2, 12, 0, 0, tzinfo=timezone.utc)
    excel_session.end_time = datetime(
        2025, 3, 2, 13, 27, 0, tzinfo=timezone.utc)
    excel_session.duration = excel_session.end_time - excel_session.start_time
    excel_session.productive = True
    program_sessions.append(excel_session)

    # Slack session
    slack_session = ProgramSessionData()
    slack_session.window_title = "Slack"
    slack_session.detail = "Team communication"
    slack_session.start_time = datetime(
        2025, 3, 2, 13, 30, 0, tzinfo=timezone.utc)
    slack_session.end_time = datetime(
        2025, 3, 2, 14, 18, 0, tzinfo=timezone.utc)
    slack_session.duration = slack_session.end_time - slack_session.start_time
    slack_session.productive = True
    program_sessions.append(slack_session)

    # Alt-tab session
    alt_tab_session = ProgramSessionData()
    alt_tab_session.window_title = "Alt-tab window"
    alt_tab_session.detail = "Switching between applications"
    alt_tab_session.start_time = datetime(
        2025, 3, 2, 14, 20, 0, tzinfo=timezone.utc)
    alt_tab_session.end_time = datetime(
        2025, 3, 2, 14, 29, 0, tzinfo=timezone.utc)
    alt_tab_session.duration = alt_tab_session.end_time - alt_tab_session.start_time
    alt_tab_session.productive = False
    program_sessions.append(alt_tab_session)

    # PyCharm session
    pycharm_session = ProgramSessionData()
    pycharm_session.window_title = "PyCharm"
    pycharm_session.detail = "Database model development"
    pycharm_session.start_time = datetime(
        2025, 3, 2, 14, 30, 0, tzinfo=timezone.utc)
    pycharm_session.end_time = datetime(
        2025, 3, 2, 17, 45, 0, tzinfo=timezone.utc)
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Spotify session
    spotify_session = ProgramSessionData()
    spotify_session.window_title = "Spotify"
    spotify_session.detail = "Background music while working"
    spotify_session.start_time = datetime(
        2025, 3, 2, 9, 0, 0, tzinfo=timezone.utc)
    spotify_session.end_time = datetime(
        2025, 3, 2, 13, 30, 0, tzinfo=timezone.utc)
    spotify_session.duration = spotify_session.end_time - spotify_session.start_time
    spotify_session.productive = False  # Background app
    program_sessions.append(spotify_session)

    # March 3, 2025 sessions

    # VSCode session day 2
    vscode_session2 = ProgramSessionData()
    vscode_session2.window_title = "Visual Studio Code"
    vscode_session2.detail = "Test suite development"
    vscode_session2.start_time = datetime(
        2025, 3, 3, 9, 0, 0, tzinfo=timezone.utc)
    vscode_session2.end_time = datetime(
        2025, 3, 3, 12, 30, 0, tzinfo=timezone.utc)
    vscode_session2.duration = vscode_session2.end_time - vscode_session2.start_time
    vscode_session2.productive = True
    program_sessions.append(vscode_session2)

    # Zoom session
    zoom_session = ProgramSessionData()
    zoom_session.window_title = "Zoom"
    zoom_session.detail = "Team standups and planning meeting"
    zoom_session.start_time = datetime(
        2025, 3, 3, 13, 0, 0, tzinfo=timezone.utc)
    zoom_session.end_time = datetime(2025, 3, 3, 15, 0, 0, tzinfo=timezone.utc)
    zoom_session.duration = zoom_session.end_time - zoom_session.start_time
    zoom_session.productive = True
    program_sessions.append(zoom_session)

    # Word session
    word_session = ProgramSessionData()
    word_session.window_title = "Microsoft Word"
    word_session.detail = "Documentation writing"
    word_session.start_time = datetime(
        2025, 3, 3, 15, 10, 0, tzinfo=timezone.utc)
    word_session.end_time = datetime(
        2025, 3, 3, 16, 22, 0, tzinfo=timezone.utc)
    word_session.duration = word_session.end_time - word_session.start_time
    word_session.productive = True
    program_sessions.append(word_session)

    # Chrome session
    chrome_session = ProgramSessionData()
    chrome_session.window_title = "Chrome"
    chrome_session.detail = "Web browsing for work research"
    chrome_session.start_time = datetime(
        2025, 3, 3, 9, 15, 0, tzinfo=timezone.utc)
    chrome_session.end_time = datetime(
        2025, 3, 3, 13, 0, 0, tzinfo=timezone.utc)
    chrome_session.duration = chrome_session.end_time - chrome_session.start_time
    chrome_session.productive = True
    program_sessions.append(chrome_session)

    # Notion session
    notion_session = ProgramSessionData()
    notion_session.window_title = "Notion"
    notion_session.detail = "Project planning and notes"
    notion_session.start_time = datetime(
        2025, 3, 3, 16, 30, 0, tzinfo=timezone.utc)
    notion_session.end_time = datetime(
        2025, 3, 3, 17, 24, 0, tzinfo=timezone.utc)
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    program_sessions.append(notion_session)

    # Slack session day 2
    slack_session2 = ProgramSessionData()
    slack_session2.window_title = "Slack"
    slack_session2.detail = "End of day team updates"
    slack_session2.start_time = datetime(
        2025, 3, 3, 17, 30, 0, tzinfo=timezone.utc)
    slack_session2.end_time = datetime(
        2025, 3, 3, 18, 45, 0, tzinfo=timezone.utc)
    slack_session2.duration = slack_session2.end_time - slack_session2.start_time
    slack_session2.productive = True
    program_sessions.append(slack_session2)

    return program_sessions


# Four duplicate Chrome session entries
def create_duplicate_chrome_sessions() -> List:
    duplicate_chrome_sessions = []

    # Duplicate 1: GitHub session (with slight time variation)
    github_session_dup = ChromeSessionData()
    github_session_dup.domain = "github.com"
    github_session_dup.detail = "Repository browsing"
    github_session_dup.start_time = datetime(
        2025, 3, 3, 14, 0, 0, tzinfo=timezone.utc)
    github_session_dup.end_time = datetime(
        2025, 3, 3, 14, 45, 0, tzinfo=timezone.utc)
    github_session_dup.duration = github_session_dup.end_time - \
        github_session_dup.start_time
    github_session_dup.productive = True
    duplicate_chrome_sessions.append(github_session_dup)

    # Duplicate 2: YouTube session (with slight time variation)
    youtube_session_dup = ChromeSessionData()
    youtube_session_dup.domain = "youtube.com"
    youtube_session_dup.detail = "Watching programming tutorials"
    youtube_session_dup.start_time = datetime(
        2025, 3, 3, 16, 0, 0, tzinfo=timezone.utc)
    youtube_session_dup.end_time = datetime(
        2025, 3, 3, 16, 45, 0, tzinfo=timezone.utc)
    youtube_session_dup.duration = youtube_session_dup.end_time - \
        youtube_session_dup.start_time
    youtube_session_dup.productive = True
    duplicate_chrome_sessions.append(youtube_session_dup)

    # Duplicate 3: ChatGPT session (with slight time variation)
    chatgpt_session_dup = ChromeSessionData()
    chatgpt_session_dup.domain = "chat.openai.com"
    chatgpt_session_dup.detail = "Asking for coding help"
    chatgpt_session_dup.start_time = datetime(
        2025, 3, 2, 15, 30, 0, tzinfo=timezone.utc)
    chatgpt_session_dup.end_time = datetime(
        2025, 3, 2, 16, 15, 0, tzinfo=timezone.utc)
    chatgpt_session_dup.duration = chatgpt_session_dup.end_time - \
        chatgpt_session_dup.start_time
    chatgpt_session_dup.productive = True
    duplicate_chrome_sessions.append(chatgpt_session_dup)

    # Duplicate 4: StackOverflow session (with slight time variation)
    stackoverflow_session_dup = ChromeSessionData()
    stackoverflow_session_dup.domain = "stackoverflow.com"
    stackoverflow_session_dup.detail = "Finding solutions to SQLAlchemy issues"
    stackoverflow_session_dup.start_time = datetime(
        2025, 3, 2, 16, 30, 0, tzinfo=timezone.utc)
    stackoverflow_session_dup.end_time = datetime(
        2025, 3, 2, 17, 15, 0, tzinfo=timezone.utc)
    stackoverflow_session_dup.duration = stackoverflow_session_dup.end_time - \
        stackoverflow_session_dup.start_time
    stackoverflow_session_dup.productive = True
    duplicate_chrome_sessions.append(stackoverflow_session_dup)

    return duplicate_chrome_sessions


# Four duplicate Program session entries
def create_duplicate_program_sessions() -> List:
    duplicate_program_sessions = []

    # Duplicate 1: VSCode session (with slight time variation)
    vscode_session_dup = ProgramSessionData()
    vscode_session_dup.window_title = "Visual Studio Code"
    vscode_session_dup.detail = "Debugging database connections"
    vscode_session_dup.start_time = datetime(
        2025, 3, 3, 15, 0, 0, tzinfo=timezone.utc)
    vscode_session_dup.end_time = datetime(
        2025, 3, 3, 16, 30, 0, tzinfo=timezone.utc)
    vscode_session_dup.duration = vscode_session_dup.end_time - \
        vscode_session_dup.start_time
    vscode_session_dup.productive = True
    duplicate_program_sessions.append(vscode_session_dup)

    # Duplicate 2: Slack session (with slight time variation)
    slack_session_dup = ProgramSessionData()
    slack_session_dup.window_title = "Slack"
    slack_session_dup.detail = "Quick team check-in"
    slack_session_dup.start_time = datetime(
        2025, 3, 2, 15, 0, 0, tzinfo=timezone.utc)
    slack_session_dup.end_time = datetime(
        2025, 3, 2, 15, 30, 0, tzinfo=timezone.utc)
    slack_session_dup.duration = slack_session_dup.end_time - slack_session_dup.start_time
    slack_session_dup.productive = True
    duplicate_program_sessions.append(slack_session_dup)

    # Duplicate 3: Chrome program session (with slight time variation)
    chrome_session_dup = ProgramSessionData()
    chrome_session_dup.window_title = "Chrome"
    chrome_session_dup.detail = "Researching SQLAlchemy async features"
    chrome_session_dup.start_time = datetime(
        2025, 3, 3, 16, 45, 0, tzinfo=timezone.utc)
    chrome_session_dup.end_time = datetime(
        2025, 3, 3, 18, 0, 0, tzinfo=timezone.utc)
    chrome_session_dup.duration = chrome_session_dup.end_time - \
        chrome_session_dup.start_time
    chrome_session_dup.productive = True
    duplicate_program_sessions.append(chrome_session_dup)

    # Duplicate 4: PyCharm session (with slight time variation)
    pycharm_session_dup = ProgramSessionData()
    pycharm_session_dup.window_title = "PyCharm"
    pycharm_session_dup.detail = "Schema improvements"
    pycharm_session_dup.start_time = datetime(
        2025, 3, 2, 18, 0, 0, tzinfo=timezone.utc)
    pycharm_session_dup.end_time = datetime(
        2025, 3, 2, 19, 15, 0, tzinfo=timezone.utc)
    pycharm_session_dup.duration = pycharm_session_dup.end_time - \
        pycharm_session_dup.start_time
    pycharm_session_dup.productive = True
    duplicate_program_sessions.append(pycharm_session_dup)

    return duplicate_program_sessions


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
