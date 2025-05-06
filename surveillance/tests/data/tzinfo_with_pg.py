import pytz
from datetime import datetime, timedelta

from typing import List


from surveillance.object.classes import CompletedProgramSession
from surveillance.util.time_wrappers import UserLocalTime
from surveillance.util.errors import TimezoneUnawareError

notion_path = "C:/Path/to/Notion.exe"
notion_process = "Notion.exe"

zoom_path = "C:/Program Files/Zoom/Zoom.exe"
zoom_process = "Zoom.exe"

pycharm_path = "C:/Path/to/PyCharm.exe"
pycharm_process = "PyCharm.exe"


def create_pycharm_entry(dt):
    window_start = UserLocalTime(dt)
    window_end = UserLocalTime(dt + timedelta(minutes=3))
    pycharm_session = CompletedProgramSession()
    pycharm_session.exe_path = pycharm_path
    pycharm_session.process_name = pycharm_process
    pycharm_session.window_title = "PyCharmTEST"
    pycharm_session.detail = "Refactoring database models"
    pycharm_session.start_time = window_start
    pycharm_session.end_time = window_end
    pycharm_session.duration = pycharm_session.end_time - pycharm_session.start_time
    pycharm_session.productive = True
    return pycharm_session


def create_zoom_entry(dt):
    window_start = UserLocalTime(dt)
    window_end = UserLocalTime(dt + timedelta(minutes=3))
    zoom_session = CompletedProgramSession()
    zoom_session.exe_path = zoom_path
    zoom_session.process_name = zoom_process
    zoom_session.window_title = "ZoomTEST"
    zoom_session.detail = "Weekly team sync"
    zoom_session.start_time = window_start
    zoom_session.end_time = window_end
    zoom_session.duration = zoom_session.end_time - zoom_session.start_time
    zoom_session.productive = True
    return zoom_session


def create_notion_entry(dt):
    window_start = UserLocalTime(dt)
    window_end = UserLocalTime(dt + timedelta(minutes=3))
    notion_session = CompletedProgramSession()
    notion_session.exe_path = notion_path
    notion_session.process_name = notion_process
    notion_session.window_title = "NotionTEST"
    notion_session.detail = "Sprint planning documentation"
    notion_session.start_time = window_start
    notion_session.end_time = window_end
    notion_session.duration = notion_session.end_time - notion_session.start_time
    notion_session.productive = True
    return notion_session
