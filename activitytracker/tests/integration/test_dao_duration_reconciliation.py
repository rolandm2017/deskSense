from collections import defaultdict
from datetime import datetime, timedelta, timezone

import pytest

from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.time_wrappers import UserLocalTime


def _record_program_session(program_logging, program_summary, session, duration_in_sec):
    program_logging.start_session(session)
    if program_summary.find_todays_entry_for_program(session) is None:
        program_summary.start_session(session)

    full_windows, remainder = divmod(duration_in_sec, 10)
    for _ in range(full_windows):
        program_logging.push_window_ahead_ten_sec(session)
        program_summary.push_window_ahead_ten_sec(session)
    program_summary.add_used_time(session, remainder)

    completed = session.to_completed(
        UserLocalTime(session.start_time.dt + timedelta(seconds=duration_in_sec))
    )
    program_logging.finalize_log(completed)


def _record_chrome_session(chrome_logging, chrome_summary, session, duration_in_sec):
    chrome_logging.start_session(session)
    if chrome_summary.find_todays_entry_for_domain(session) is None:
        chrome_summary.start_session(session)

    full_windows, remainder = divmod(duration_in_sec, 10)
    for _ in range(full_windows):
        chrome_logging.push_window_ahead_ten_sec(session)
        chrome_summary.push_window_ahead_ten_sec(session)
    chrome_summary.add_used_time(session, remainder)

    completed = session.to_completed(
        UserLocalTime(session.start_time.dt + timedelta(seconds=duration_in_sec))
    )
    chrome_logging.finalize_log(completed)


def test_dao_duration_reconciliation_between_logs_and_summaries(regular_session_maker):
    program_logging = ProgramLoggingDao(regular_session_maker)
    chrome_logging = ChromeLoggingDao(regular_session_maker)
    program_summary = ProgramSummaryDao(program_logging, regular_session_maker)
    chrome_summary = ChromeSummaryDao(chrome_logging, regular_session_maker)

    base = datetime(2025, 3, 22, 16, 0, tzinfo=timezone.utc)
    program_cases = [
        (
            ProgramSession(
                exe_path="C:/apps/Code.exe",
                process_name="Code.exe",
                window_title="Visual Studio Code",
                detail="editing tests",
                start_time=UserLocalTime(base),
            ),
            23,
        ),
        (
            ProgramSession(
                exe_path="C:/apps/Postman.exe",
                process_name="Postman.exe",
                window_title="Postman",
                detail="collections",
                start_time=UserLocalTime(base + timedelta(seconds=40)),
            ),
            17,
        ),
        (
            ProgramSession(
                exe_path="C:/apps/Code.exe",
                process_name="Code.exe",
                window_title="Visual Studio Code",
                detail="review",
                start_time=UserLocalTime(base + timedelta(seconds=90)),
            ),
            31,
        ),
    ]
    chrome_cases = [
        (
            ChromeSession(
                domain="chatgpt.com",
                detail="ChatGPT",
                start_time=UserLocalTime(base + timedelta(seconds=130)),
            ),
            19,
        ),
        (
            ChromeSession(
                domain="github.com",
                detail="GitHub",
                start_time=UserLocalTime(base + timedelta(seconds=170)),
            ),
            14,
        ),
        (
            ChromeSession(
                domain="chatgpt.com",
                detail="ChatGPT",
                start_time=UserLocalTime(base + timedelta(seconds=200)),
            ),
            27,
        ),
    ]

    for session, duration in program_cases:
        _record_program_session(program_logging, program_summary, session, duration)
    for session, duration in chrome_cases:
        _record_chrome_session(chrome_logging, chrome_summary, session, duration)

    program_log_totals = defaultdict(float)
    for log in program_logging.read_all():
        program_log_totals[log.exe_path_as_id] += log.duration_in_sec
    program_summary_totals = {
        row.exe_path_as_id: row.hours_spent * SECONDS_PER_HOUR
        for row in program_summary.read_all()
    }

    chrome_log_totals = defaultdict(float)
    for log in chrome_logging.read_all():
        chrome_log_totals[log.domain_name] += log.duration_in_sec
    chrome_summary_totals = {
        row.domain_name: row.hours_spent * SECONDS_PER_HOUR for row in chrome_summary.read_all()
    }

    assert set(program_summary_totals) == set(program_log_totals)
    assert set(chrome_summary_totals) == set(chrome_log_totals)

    for exe_path, log_seconds in program_log_totals.items():
        assert program_summary_totals[exe_path] == pytest.approx(log_seconds)
    for domain, log_seconds in chrome_log_totals.items():
        assert chrome_summary_totals[domain] == pytest.approx(log_seconds)
