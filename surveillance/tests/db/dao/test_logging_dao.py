import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta


from src.arbiter.activity_recorder import ActivityRecorder

from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.chrome_summary_dao import ChromeSummaryDao
from src.db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao

from src.object.classes import ProgramSessionData, ChromeSessionData

from src.util.errors import ImpossibleToGetHereError


# TODO:
# if logging_dao.find_session(session):
#     print("weeeee 64ru")
#     await logging_dao.push_window_ahead_ten_sec(session)
# else:
#     print(" vvvvvvvvvvvvvvvv Here 66ru")
#     await logging_dao.start_session(session)


def test_find_session():
    program_dao = ProgramLoggingDao()
    queue_item_mock_program = AsyncMock()
    program_dao.queue_item = queue_item_mock_program
    chrome_dao = ChromeLoggingDao()
    queue_item_mock_chrome = AsyncMock()
    chrome_dao.queue_item = queue_item_mock_chrome

    # Arrange (still)
    program_dao.start_session(test_program_session)
    chrome_dao.start_session(test_chrome_session)

    # Act
    found = program_dao.find_session(session)
    found = chrome_dao.find_session(session)



def test_push_window_ahead():
    pass

def test_start_session():
    pass


def nonexistent_session():
    session = ChromeSessionData()
    session.domain = "github.com"
    session.detail = "DeepSeek Chat Repository"
    session.start_time = datetime(2025, 1, 1, 1, 0, 0, 0)  # almost certainly doesn't exist
    session.end_time = datetime(2025, 1, 1, 1, 0, 0, 1)
    session.duration = timedelta(minutes=1)
    session.productive = True
    return session


def test_push_window_error():
    program_dao = ProgramLoggingDao()
    chrome_dao = ChromeLoggingDao()
    with pytest.raises(ImpossibleToGetHereError):
        program_dao.push_window_ahead_ten_sec(nonexistent_session())
    with pytest.raises(ImpossibleToGetHereError):
        chrome_dao.push_window_ahead_ten_sec(nonexistent_session())


def test_finalize_log_error():
    program_dao = ProgramLoggingDao()
    chrome_dao = ChromeLoggingDao()


    with pytest.raises(ImpossibleToGetHereError):
        program_dao.finalize_log(nonexistent_session())
    with pytest.raises(ImpossibleToGetHereError):
        chrome_dao.finalize_log(nonexistent_session())