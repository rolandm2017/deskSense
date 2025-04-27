from surveillance.src.object.classes import ProgramSession
from datetime import datetime, timedelta, timezone
import pytz
from typing import List, Optional

from surveillance.src.object.classes import ChromeSession, ProgramSession
from surveillance.src.util.time_wrappers import UserLocalTime

from surveillance.src.config.definitions import local_time_zone

# Sample ProgramSession objects
# 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️
# 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️ Programs File 🖥️
# Sample ProgramSession objects


#
# -- this is the main place to define timezones
#
est_timezone = "US/Eastern"  # UTC -5 or UTC -4 during daylight saving time

weekly_breakdown_tz = pytz.timezone(est_timezone)

#
# -- do not set timezones for this test outside of the header here
#


march_2_2025 = datetime(2025, 3, 2, tzinfo=weekly_breakdown_tz)
march_3_2025 = datetime(2025, 3, 3, tzinfo=weekly_breakdown_tz)


def add_time_and_tz(base_date, hours=0, minutes=0, seconds=0):
    """Helper function to add hours, minutes, seconds to a base date. Plus a timezone"""
    result_dt = base_date + timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    # Check if datetime is already timezone-aware
    if result_dt.tzinfo is None:
        # It's naive, so localize it with the specified timezone
        result_dt = weekly_breakdown_tz.localize(result_dt)
    
    return result_dt

# grep -o '\.window_title = "[^TEST"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 11

# grep -o '\.domain = "[^"]*"' surveillance/tests/data/weekly_breakdown.py | sort | uniq | wc -l
# 10


# Define the base dates for the last week of Feb
feb_23_2025 = datetime(2025, 2, 23, tzinfo=weekly_breakdown_tz)
feb_24_2025 = datetime(2025, 2, 24, tzinfo=weekly_breakdown_tz)
feb_26_2025 = datetime(2025, 2, 26, tzinfo=weekly_breakdown_tz)

zoom_path = "C:/Program Files/Zoom/Zoom.exe"
zoom_process = "Zoom.exe"

msword_path = "C:/Program Files/Microsoft Office/Office16/WINWORD.EXE"
msword_process = "WINWORD.EXE"


slack_path = "C:/Users/AppData/Local/Slack/Slack.exe"
slack_process = "Slack.exe"

pycharm_path = "C:/Path/to/PyCharm.exe"
pycharm_process = "PyCharm.exe"

chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
chrome_process = "Chrome.exe"

vscode_path = "C:/Program Files/Microsoft VS Code/Code.exe"
vscode_process = "Code.exe"

notion_path = "C:/Path/to/Notion.exe"
notion_process = "Notion.exe"


excel_path = "C:/ProgramFiles/Excel.exe"
excel_process = "Excel.exe"


spotify_path = "C:/Path/to/spotify.exe"
spotify_process = "Spotify.exe"


def programs_feb_23() -> List:
    program_sessions = []

    # Pycharm session
    pycharm_session = ProgramSession()
    pycharm_session.exe_path = pycharm_path
    pycharm_session.process_name = pycharm_process
    pycharm_session.window_title = "Visual Studio CodeTEST"
    pycharm_session.detail = "Initial project setup"
    pycharm_session.start_time = UserLocalTime(
        add_time_and_tz(feb_23_2025, 10, 15, 0))
    pycharm_session.end_time = UserLocalTime(add_time_and_tz(feb_23_2025, 11, 45, 0))
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Notion session
    notion_session = ProgramSession()
    notion_session.exe_path = notion_path
    notion_session.process_name = notion_process
    notion_session.window_title = "NotionTEST"
    notion_session.detail = "Sprint planning documentation"
    notion_session.start_time = UserLocalTime(add_time_and_tz(feb_23_2025, 14, 20, 0))
    notion_session.end_time = UserLocalTime(add_time_and_tz(feb_23_2025, 15, 35, 0))
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    program_sessions.append(notion_session)

    return program_sessions


def programs_feb_24() -> List:
    program_sessions = []

    # PyCharm session
    pycharm_session = ProgramSession()
    pycharm_session.exe_path = pycharm_path
    pycharm_session.process_name = pycharm_process
    pycharm_session.window_title = "PyCharmTEST"
    pycharm_session.detail = "Refactoring database models"
    pycharm_session.start_time = UserLocalTime(add_time_and_tz(feb_24_2025, 9, 30, 0))
    pycharm_session.end_time = UserLocalTime(add_time_and_tz(feb_24_2025, 11, 15, 0))
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Zoom session
    zoom_session = ProgramSession()
    zoom_session.exe_path = zoom_path
    zoom_session.process_name = zoom_process
    zoom_session.window_title = "ZoomTEST"
    zoom_session.detail = "Weekly team sync"
    zoom_session.start_time = UserLocalTime(add_time_and_tz(feb_24_2025, 13, 0, 0))
    zoom_session.end_time = UserLocalTime(add_time_and_tz(feb_24_2025, 14, 15, 0))
    zoom_session.duration = zoom_session.end_time - zoom_session.start_time
    zoom_session.productive = True
    program_sessions.append(zoom_session)

    return program_sessions


def programs_feb_26() -> List:
    program_sessions = []

    # Visual Studio Code session
    pycharm_session = ProgramSession()
    pycharm_session.exe_path = vscode_path
    pycharm_session.process_name = vscode_process
    pycharm_session.window_title = "Visual Studio CodeTEST"
    pycharm_session.detail = "Implementing new API endpoints"
    pycharm_session.start_time = UserLocalTime(add_time_and_tz(feb_26_2025, 10, 0, 0))
    pycharm_session.end_time = UserLocalTime(add_time_and_tz(feb_26_2025, 12, 30, 0))
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Slack session
    slack_session = ProgramSession()
    slack_session.exe_path = slack_path
    slack_session.process_name = slack_process
    slack_session.window_title = "SlackTEST"
    slack_session.detail = "Project coordination"
    slack_session.start_time = UserLocalTime(add_time_and_tz(feb_26_2025, 15, 45, 0))
    slack_session.end_time = UserLocalTime(add_time_and_tz(feb_26_2025, 16, 20, 0))
    slack_session.duration = slack_session.end_time - slack_session.start_time
    slack_session.productive = True
    program_sessions.append(slack_session)

    return program_sessions


# Count for reference
feb_23_program_count = len(programs_feb_23())
feb_24_program_count = len(programs_feb_24())
feb_26_program_count = len(programs_feb_26())

feb_program_count = feb_23_program_count + \
    feb_24_program_count + feb_26_program_count

unique_programs = 11  # in march

# Sample ProgramSession objects


def programs_march_2nd() -> List:
    # March 2, 2025 sessions
    program_sessions = []

    # Pycharm session
    pycharm_session = ProgramSession()
    pycharm_session.exe_path = vscode_path
    pycharm_session.process_name = vscode_process

    pycharm_session.window_title = "Visual Studio CodeTEST"
    pycharm_session.detail = "Working on async SQLAlchemy project"
    pycharm_session.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 9, 45, 0))
    pycharm_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 10, 15, 0))
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Excel session
    excel_session = ProgramSession()
    excel_session.exe_path = excel_path
    excel_session.process_name = excel_process
    excel_session.window_title = "Microsoft ExcelTEST"
    excel_session.detail = "Data analysis for project metrics"
    excel_session.start_time = UserLocalTime(add_time_and_tz(march_2_2025, 12, 39, 0))
    excel_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 13, 27, 0))
    excel_session.duration = excel_session.end_time - excel_session.start_time
    excel_session.productive = True
    program_sessions.append(excel_session)

    # Slack session
    slack_session = ProgramSession()
    slack_session.exe_path = slack_path
    slack_session.process_name = slack_process
    slack_session.window_title = "SlackTEST"
    slack_session.detail = "Team communication"
    slack_session.start_time = UserLocalTime(add_time_and_tz(march_2_2025, 13, 30, 0))
    slack_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 14, 18, 0))
    slack_session.duration = slack_session.end_time - slack_session.start_time
    slack_session.productive = True
    program_sessions.append(slack_session)

    # Alt-tab session
    alt_tab_session = ProgramSession()
    alt_tab_session.exe_path = "C:/wherever/altTab/lives.exe"
    alt_tab_session.process_name = "lives.exe"
    alt_tab_session.window_title = "Alt-tab windowTEST"
    alt_tab_session.detail = "Switching between applications"
    alt_tab_session.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 14, 20, 0))
    alt_tab_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 14, 29, 0))
    alt_tab_session.duration = alt_tab_session.end_time - alt_tab_session.start_time
    alt_tab_session.productive = False
    program_sessions.append(alt_tab_session)

    # PyCharm session
    pycharm_session = ProgramSession()
    pycharm_session.exe_path = pycharm_path
    pycharm_session.process_name = pycharm_process
    pycharm_session.window_title = "PyCharmTEST"
    pycharm_session.detail = "Database model development"
    pycharm_session.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 14, 30, 0))
    pycharm_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 15, 11, 0))
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    program_sessions.append(pycharm_session)

    # Spotify session
    spotify_session = ProgramSession()
    spotify_session.exe_path = spotify_path
    spotify_session.process_name = spotify_process
    spotify_session.window_title = "SpotifyTEST"
    spotify_session.detail = "Background music while working"
    spotify_session.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 12, 49, 0))
    spotify_session.end_time = UserLocalTime(add_time_and_tz(march_2_2025, 13, 30, 0))
    spotify_session.duration = spotify_session.end_time - spotify_session.start_time
    spotify_session.productive = False  # Background app
    program_sessions.append(spotify_session)

    return program_sessions


# Four duplicate Program session entries
def duplicate_programs_march_2() -> List:
    duplicate_program_sessions = []

    # Duplicate 1: Slack session (with slight time variation)
    slack_session_dup = ProgramSession()
    slack_session_dup.exe_path = slack_path
    slack_session_dup.process_name = slack_process
    slack_session_dup.window_title = "SlackTEST"
    slack_session_dup.detail = "Quick team check-in"
    slack_session_dup.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 15, 0, 0))
    slack_session_dup.end_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 15, 30, 0))
    slack_session_dup.duration = slack_session_dup.end_time - slack_session_dup.start_time
    slack_session_dup.productive = True
    duplicate_program_sessions.append(slack_session_dup)

    # Duplicate 2: PyCharm session (with slight time variation)
    pycharm_session_dup = ProgramSession()
    pycharm_session_dup.exe_path = pycharm_path
    pycharm_session_dup.process_name = pycharm_process
    pycharm_session_dup.window_title = "PyCharmTEST"
    pycharm_session_dup.detail = "Schema improvements"
    pycharm_session_dup.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 18, 50, 0))
    pycharm_session_dup.end_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 19, 15, 0))
    pycharm_session_dup.duration = pycharm_session_dup.end_time - \
        pycharm_session_dup.start_time
    pycharm_session_dup.productive = True
    duplicate_program_sessions.append(pycharm_session_dup)

    # Dupe 3: Spotify session
    spotify_session = ProgramSession()
    spotify_session.exe_path = spotify_path
    spotify_session.process_name = spotify_process
    spotify_session.window_title = "SpotifyTEST"
    spotify_session.detail = "Lively dance session"
    spotify_session.start_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 12, 49, 0))
    spotify_session.end_time = UserLocalTime(
        add_time_and_tz(march_2_2025, 13, 51, 33))
    spotify_session.duration = spotify_session.end_time - spotify_session.start_time
    spotify_session.productive = False  # Background app
    duplicate_program_sessions.append(spotify_session)

    return duplicate_program_sessions


def programs_march_3rd() -> List:
    # March 3, 2025 sessions
    program_sessions = []

    # Pycharm session day 2
    pycharm_session2 = ProgramSession()
    pycharm_session2.exe_path = vscode_path
    pycharm_session2.process_name = vscode_process
    pycharm_session2.window_title = "Visual Studio CodeTEST"
    pycharm_session2.detail = "Test suite development"
    pycharm_session2.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 12, 0, 0))
    pycharm_session2.end_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 12, 30, 0))
    pycharm_session2.duration = pycharm_session2.end_time - pycharm_session2.start_time
    pycharm_session2.productive = True
    program_sessions.append(pycharm_session2)

    # Zoom session
    zoom_session = ProgramSession()
    zoom_session.exe_path = zoom_path
    zoom_session.process_name = zoom_process
    zoom_session.window_title = "ZoomTEST"
    zoom_session.detail = "Team standups and planning meeting"
    zoom_session.start_time = UserLocalTime(add_time_and_tz(march_3_2025, 14, 1, 0))
    zoom_session.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 15, 0, 0))
    zoom_session.duration = zoom_session.end_time - zoom_session.start_time
    zoom_session.productive = True
    program_sessions.append(zoom_session)

    # Word session
    word_session = ProgramSession()
    word_session.exe_path = msword_path
    word_session.process_name = msword_process
    word_session.window_title = "Microsoft WordTEST"
    word_session.detail = "Documentation writing"
    word_session.start_time = UserLocalTime(add_time_and_tz(march_3_2025, 15, 25, 0))
    word_session.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 16, 22, 0))
    word_session.duration = word_session.end_time - word_session.start_time
    word_session.productive = True
    program_sessions.append(word_session)

    # Chrome session
    chrome_session = ProgramSession()
    chrome_session.exe_path = chrome_path
    chrome_session.process_name = chrome_process
    chrome_session.window_title = "ChromeTEST"
    chrome_session.detail = "Web browsing for work research"
    chrome_session.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 12, 15, 0))
    chrome_session.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 13, 0, 0))
    chrome_session.duration = chrome_session.end_time - chrome_session.start_time
    chrome_session.productive = True
    program_sessions.append(chrome_session)

    # Notion session
    notion_session = ProgramSession()
    notion_session.exe_path = notion_path
    notion_session.process_name = notion_process
    notion_session.window_title = "NotionTEST"
    notion_session.detail = "Project planning and notes"
    notion_session.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 16, 30, 0))
    notion_session.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 17, 24, 0))
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    program_sessions.append(notion_session)

    # Slack session day 2
    slack_session2 = ProgramSession()
    slack_session2.exe_path = slack_path
    slack_session2.process_name = slack_process
    slack_session2.window_title = "SlackTEST"
    slack_session2.detail = "End of day team updates"
    slack_session2.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 17, 50, 0))
    slack_session2.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 18, 45, 0))
    slack_session2.duration = slack_session2.end_time - slack_session2.start_time
    slack_session2.productive = True
    program_sessions.append(slack_session2)

    return program_sessions


def duplicate_programs_march_3rd() -> List:
    duplicate_program_sessions = []

    # Duplicate 4: Chrome program session (with slight time variation)
    chrome_session_dup = ProgramSession()
    chrome_session_dup.exe_path = chrome_path
    chrome_session_dup.process_name = chrome_process
    chrome_session_dup.window_title = "ChromeTEST"
    chrome_session_dup.detail = "Researching SQLAlchemy async features"
    chrome_session_dup.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 16, 45, 0))
    chrome_session_dup.end_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 17, 20, 0))
    chrome_session_dup.duration = chrome_session_dup.end_time - \
        chrome_session_dup.start_time
    chrome_session_dup.productive = True
    duplicate_program_sessions.append(chrome_session_dup)

    # Duplicate 5: Pycharm session (with slight time variation)
    pycharm_session_dup = ProgramSession()
    pycharm_session_dup.exe_path = vscode_path
    pycharm_session_dup.process_name = vscode_process
    pycharm_session_dup.window_title = "Visual Studio CodeTEST"
    pycharm_session_dup.detail = "Debugging database connections"
    pycharm_session_dup.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 15, 40, 0))
    pycharm_session_dup.end_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 16, 30, 0))
    pycharm_session_dup.duration = pycharm_session_dup.end_time - \
        pycharm_session_dup.start_time
    pycharm_session_dup.productive = True
    duplicate_program_sessions.append(pycharm_session_dup)

    # Dupe 6: Notion session
    notion_session = ProgramSession()
    notion_session.exe_path = notion_path
    notion_session.process_name = notion_process
    notion_session.window_title = "NotionTEST"
    notion_session.detail = "Project planning and notes"
    notion_session.start_time = UserLocalTime(
        add_time_and_tz(march_3_2025, 16, 30, 0))
    notion_session.end_time = UserLocalTime(add_time_and_tz(march_3_2025, 17, 27, 0))
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    duplicate_program_sessions.append(notion_session)

    return duplicate_program_sessions


# counted manually from Ctrl + F "t_time = add_time_and_tz(march_2_2"
march_2_program_count = len(programs_march_2nd())
march_3_program_count = len(programs_march_3rd())
