from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.object.classes import ChromeSessionData, ProgramSessionData

# Sample ProgramSessionData objects
# 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️
# 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️
# Sample ProgramSessionData objects


march_2_2025 = datetime(2025, 3, 2, tzinfo=timezone.utc)
march_3_2025 = datetime(2025, 3, 3, tzinfo=timezone.utc)


def add_time(base_date, hours=0, minutes=0, seconds=0):
    """Helper function to add hours, minutes, seconds to a base date"""
    return base_date + timedelta(hours=hours, minutes=minutes, seconds=seconds)


# grep -o '\.window_title = "[^"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 11

# grep -o '\.domain = "[^"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 10

unique_programs = 11

# counted manually from Ctrl + F "t_time = add_time(march_2_2"
march_2_program_count = 0


# Sample ProgramSessionData objects
def create_program_session_test_data() -> List:
    program_sessions = []

    # March 2, 2025 sessions

    # VSCode session
    vscode_session = ProgramSessionData()
    vscode_session.window_title = "Visual Studio Code"
    vscode_session.detail = "Working on async SQLAlchemy project"
    vscode_session.start_time = add_time(march_2_2025, 9, 45, 0)
    vscode_session.end_time = add_time(march_2_2025, 10, 15, 0)
    vscode_session.duration = vscode_session.end_time - vscode_session.start_time
    vscode_session.productive = True
    program_sessions.append(vscode_session)

    # Excel session
    excel_session = ProgramSessionData()
    excel_session.window_title = "Microsoft Excel"
    excel_session.detail = "Data analysis for project metrics"
    excel_session.start_time = add_time(march_2_2025, 12, 39, 0)
    excel_session.end_time = add_time(march_2_2025, 13, 27, 0)
    excel_session.duration = excel_session.end_time - excel_session.start_time
    excel_session.productive = True
    program_sessions.append(excel_session)

    # Slack session
    slack_session = ProgramSessionData()
    slack_session.window_title = "Slack"
    slack_session.detail = "Team communication"
    slack_session.start_time = add_time(march_2_2025, 13, 30, 0)
    slack_session.end_time = add_time(march_2_2025, 14, 18, 0)
    slack_session.duration = slack_session.end_time - slack_session.start_time
    slack_session.productive = True
    program_sessions.append(slack_session)

    # Alt-tab session
    alt_tab_session = ProgramSessionData()
    alt_tab_session.window_title = "Alt-tab window"
    alt_tab_session.detail = "Switching between applications"
    alt_tab_session.start_time = add_time(march_2_2025, 14, 20, 0)
    alt_tab_session.end_time = add_time(march_2_2025, 14, 29, 0)
    alt_tab_session.duration = alt_tab_session.end_time - alt_tab_session.start_time
    alt_tab_session.productive = False
    program_sessions.append(alt_tab_session)

    # PyCharm session
    pycharm_session = ProgramSessionData()
    pycharm_session.window_title = "PyCharm"
    pycharm_session.detail = "Database model development"
    pycharm_session.start_time = add_time(march_2_2025, 14, 30, 0)
    pycharm_session.end_time = add_time(march_2_2025, 15, 11, 0)

    # Spotify session
    spotify_session = ProgramSessionData()
    spotify_session.window_title = "Spotify"
    spotify_session.detail = "Background music while working"
    spotify_session.start_time = add_time(march_2_2025, 12, 49, 0)
    spotify_session.end_time = add_time(march_2_2025, 13, 30, 0)
    spotify_session.duration = spotify_session.end_time - spotify_session.start_time
    spotify_session.productive = False  # Background app
    program_sessions.append(spotify_session)

    # March 3, 2025 sessions

    # VSCode session day 2
    vscode_session2 = ProgramSessionData()
    vscode_session2.window_title = "Visual Studio Code"
    vscode_session2.detail = "Test suite development"
    vscode_session2.start_time = add_time(march_3_2025, 12, 0, 0)
    vscode_session2.end_time = add_time(march_3_2025, 12, 30, 0)
    vscode_session2.duration = vscode_session2.end_time - vscode_session2.start_time
    vscode_session2.productive = True
    program_sessions.append(vscode_session2)

    # Zoom session
    zoom_session = ProgramSessionData()
    zoom_session.window_title = "Zoom"
    zoom_session.detail = "Team standups and planning meeting"
    zoom_session.start_time = add_time(march_3_2025, 14, 1, 0)
    zoom_session.end_time = add_time(march_3_2025, 15, 0, 0)
    zoom_session.duration = zoom_session.end_time - zoom_session.start_time
    zoom_session.productive = True
    program_sessions.append(zoom_session)

    # Word session
    word_session = ProgramSessionData()
    word_session.window_title = "Microsoft Word"
    word_session.detail = "Documentation writing"
    word_session.start_time = add_time(march_3_2025, 15, 25, 0)
    word_session.end_time = add_time(march_3_2025, 16, 22, 0)
    word_session.duration = word_session.end_time - word_session.start_time
    word_session.productive = True
    program_sessions.append(word_session)

    # Chrome session
    chrome_session = ProgramSessionData()
    chrome_session.window_title = "Chrome"
    chrome_session.detail = "Web browsing for work research"
    chrome_session.start_time = add_time(march_3_2025, 12, 15, 0)
    chrome_session.end_time = add_time(march_3_2025, 13, 0, 0)
    chrome_session.duration = chrome_session.end_time - chrome_session.start_time
    chrome_session.productive = True
    program_sessions.append(chrome_session)

    # Notion session
    notion_session = ProgramSessionData()
    notion_session.window_title = "Notion"
    notion_session.detail = "Project planning and notes"
    notion_session.start_time = add_time(march_3_2025, 16, 30, 0)
    notion_session.end_time = add_time(march_3_2025, 17, 24, 0)
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    program_sessions.append(notion_session)

    # Slack session day 2
    slack_session2 = ProgramSessionData()
    slack_session2.window_title = "Slack"
    slack_session2.detail = "End of day team updates"
    slack_session2.start_time = add_time(march_3_2025, 17, 50, 0)
    slack_session2.end_time = add_time(march_3_2025, 18, 45, 0)
    slack_session2.duration = slack_session2.end_time - slack_session2.start_time
    slack_session2.productive = True
    program_sessions.append(slack_session2)

    return program_sessions


# Four duplicate Program session entries
def create_duplicate_program_sessions() -> List:
    duplicate_program_sessions = []

    # Duplicate 1: VSCode session (with slight time variation)
    vscode_session_dup = ProgramSessionData()
    vscode_session_dup.window_title = "Visual Studio Code"
    vscode_session_dup.detail = "Debugging database connections"
    vscode_session_dup.start_time = add_time(march_3_2025, 15, 40, 0)
    vscode_session_dup.end_time = add_time(march_3_2025, 16, 30, 0)
    vscode_session_dup.duration = vscode_session_dup.end_time - \
        vscode_session_dup.start_time
    vscode_session_dup.productive = True
    duplicate_program_sessions.append(vscode_session_dup)

    # Duplicate 2: Slack session (with slight time variation)
    slack_session_dup = ProgramSessionData()
    slack_session_dup.window_title = "Slack"
    slack_session_dup.detail = "Quick team check-in"
    slack_session_dup.start_time = add_time(march_2_2025, 15, 0, 0)
    slack_session_dup.end_time = add_time(march_2_2025, 15, 30, 0)
    slack_session_dup.duration = slack_session_dup.end_time - slack_session_dup.start_time
    slack_session_dup.productive = True
    duplicate_program_sessions.append(slack_session_dup)

    # Duplicate 3: Chrome program session (with slight time variation)
    chrome_session_dup = ProgramSessionData()
    chrome_session_dup.window_title = "Chrome"
    chrome_session_dup.detail = "Researching SQLAlchemy async features"
    chrome_session_dup.start_time = add_time(march_3_2025, 16, 45, 0)
    chrome_session_dup.end_time = add_time(march_3_2025, 17, 20, 0)
    chrome_session_dup.duration = chrome_session_dup.end_time - \
        chrome_session_dup.start_time
    chrome_session_dup.productive = True
    duplicate_program_sessions.append(chrome_session_dup)

    # Duplicate 4: PyCharm session (with slight time variation)
    pycharm_session_dup = ProgramSessionData()
    pycharm_session_dup.window_title = "PyCharm"
    pycharm_session_dup.detail = "Schema improvements"
    pycharm_session_dup.start_time = add_time(march_2_2025, 18, 50, 0)
    pycharm_session_dup.end_time = add_time(march_2_2025, 19, 15, 0)
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
