"""
Exists because, sometimes, time x on day y, in <timezone>, 
becomes time a on day y - 1 or y + 1.

It's not enough to just know that: It must also be known exactly.
"""

import pytest_asyncio
import pytest

from sqlalchemy import text

import pytz
from datetime import datetime, timedelta

from typing import List

from surveillance.src.db.models import DailyProgramSummary
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao

from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.errors import TimezoneUnawareError
from surveillance.src.util.const import ten_sec_as_pct_of_hour

from ..data.tzinfo_with_pg import create_notion_entry, create_pycharm_entry, create_zoom_entry

def add_time(base_date, hours=0, minutes=0, seconds=0):
    """Helper function to add hours, minutes, seconds to a base date"""
    return base_date + timedelta(hours=hours, minutes=minutes, seconds=seconds)


one_day_before = datetime(2025, 3, 12)
base_day = datetime(2025, 3, 13)
one_day_later = datetime(2025, 3, 14)

timezone_for_test = "Europe/Berlin"  # UTC +1 or UTC +2

some_local_tz = pytz.timezone(timezone_for_test)

def test_basic_setup():
    """Assumes that even the testing setup will be broken unless tested"""
    time_for_test = add_time(base_day, 5, 6, 7)
    time_with_tz = some_local_tz.localize(time_for_test)
    try:
        time_with_wrapper = UserLocalTime(time_with_tz)
        success = True
    except TimezoneUnawareError as e:
        exception = e
        success = False
    
    assert success, f"Expected no exception but got {exception}"
    
    # Compare by string representation - should contain 'Europe/Berlin'
    assert timezone_for_test in str(time_with_wrapper.dt.tzinfo)
    # Compare timezone names instead of timezone objects
    assert str(time_with_wrapper.dt.tzinfo) == str(some_local_tz), f"Expected both to equal {str(some_local_tz)}"

    assert time_with_wrapper.dt.hour == time_for_test.hour
    assert time_with_wrapper.dt.minute == time_for_test.minute
    assert time_with_wrapper.dt.second == time_for_test.second



# Test day boundary cases specifically
# Test entries at the edges of the day

#
# -- this is the pool of test data, please choose from it
#

# Day before base day

just_before_boundary = create_pycharm_entry(some_local_tz.localize(add_time(one_day_before, 23, 59, 59)))  # Just before midnight

# Base day

noon = some_local_tz.localize(add_time(base_day, 12, 0, 0))

late_night_entry = create_pycharm_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))  # Just before midnight
midnight_entry = create_notion_entry(some_local_tz.localize(add_time(base_day, 0, 0, 1)))  # Just after midnight
abs_min_time = create_zoom_entry(some_local_tz.localize(add_time(base_day, 0, 0, 0))) 
very_early_morning_entry = create_zoom_entry(some_local_tz.localize(add_time(base_day, 3, 0, 1))
)

five_am_ish = create_notion_entry(some_local_tz.localize(add_time(base_day, 5, 0, 0)))

seven_am_ish = create_zoom_entry(some_local_tz.localize(add_time(base_day, 7, 0, 0)))

afternoon = create_pycharm_entry(some_local_tz.localize(add_time(base_day, 15, 0, 15)))

latenight1 =  create_zoom_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))
latenight2 =  create_pycharm_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))

# Just after end of base day

just_after_boundary = create_notion_entry(some_local_tz.localize(add_time(one_day_later, 0, 0, 1)))

#
# -- choose test data from the above pool!
#


def write_before_and_after_base_day(summary_dao):
    """Ensures that read_day is more specific than just 'read_all' with an arg."""
    summary_dao.start_session(just_before_boundary, just_before_boundary.start_time)
    summary_dao.start_session(just_after_boundary, just_after_boundary.start_time)


@pytest_asyncio.fixture
async def setup_parts(db_session_in_mem, mock_async_session_maker):
    """
    Only the Program suite is required here, because it's so similar to Chrome.
    
    This connects to the test db, unless there is an unforseen problem.
    """
    regular_maker = db_session_in_mem
    # Get all required DAOs
    program_logging_dao = ProgramLoggingDao(
        regular_maker)
    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_maker, mock_async_session_maker)
    
    return program_logging_dao, program_summary_dao

def test_away_from_edge_cases(setup_parts):
    """Away from edge cases, meaning, 11 am, 3 pm, 6 pm."""
    logging_dao, summary_dao = setup_parts

    seven_am_ish = create_zoom_entry(some_local_tz.localize(add_time(base_day, 7, 0, 0)))
    afternoon = create_pycharm_entry(some_local_tz.localize(add_time(base_day, 15, 0, 15)))

    test_inputs = [seven_am_ish, afternoon]
    
    paths_for_asserting = [x.exe_path for x in test_inputs]
    # Test setup conditions - all unique programs
    assert len(set(paths_for_asserting)) == len(paths_for_asserting)
    # Write
    summary_dao.start_session(seven_am_ish, seven_am_ish.start_time)
    summary_dao.start_session(afternoon, afternoon.start_time)

    write_before_and_after_base_day(summary_dao)
    
    # Gather by day
    print(f"reading values for day: {test_inputs[0].start_time}")
    all_for_day: List[DailyProgramSummary] = summary_dao.read_day(test_inputs[0].start_time)

    assert isinstance(all_for_day[0], DailyProgramSummary)

    # Check the val came back out
    assert len(all_for_day) == len(test_inputs)

    for i in range(0, len(test_inputs)):
        assert all_for_day[i].exe_path_as_id in paths_for_asserting
        assert all_for_day[i].hours_spent == 0

    assert len(all_for_day) == len(test_inputs)


def test_on_twelve_ish_am_boundary(setup_parts):
    logging_dao, summary_dao = setup_parts

    late_night_entry = create_pycharm_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))  # Just before midnight
    midnight_entry = create_notion_entry(some_local_tz.localize(add_time(base_day, 0, 0, 1)))  # Just after midnight
    abs_min_time = create_zoom_entry(some_local_tz.localize(add_time(base_day, 0, 0, 0))) 

    test_inputs = [late_night_entry, midnight_entry, abs_min_time]
    
    paths_for_asserting = [x.exe_path for x in test_inputs]

    # Test setup conditions - all unique programs
    assert len(set(paths_for_asserting)) == len(paths_for_asserting)
    # Write
    summary_dao.start_session(late_night_entry, late_night_entry.start_time)
    summary_dao.start_session(midnight_entry, midnight_entry.start_time)
    summary_dao.start_session(abs_min_time, abs_min_time.start_time)

    write_before_and_after_base_day(summary_dao)

    # Gather by day
    print(f"reading values for day: {test_inputs[0].start_time}")
    all_for_day: List[DailyProgramSummary] = summary_dao.read_day(test_inputs[0].start_time)

    assert isinstance(all_for_day[0], DailyProgramSummary)

    # Check the val came back out
    assert len(all_for_day) == len(test_inputs)

    for i in range(0, len(test_inputs)):
        assert all_for_day[i].exe_path_as_id in paths_for_asserting
        assert all_for_day[i].hours_spent == 0

    assert len(all_for_day) == len(test_inputs)


def test_on_eleven_ish_pm_boundary(setup_parts):
    logging_dao, summary_dao = setup_parts

    latenight1 =  create_zoom_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))
    latenight2 =  create_pycharm_entry(some_local_tz.localize(add_time(base_day, 23, 59, 59)))

    edge_case_micros = 999999  # HEY, LISTEN! Max value possible.
    latenight2.start_time.dt.replace(microsecond=edge_case_micros)

    test_inputs = [latenight1, latenight2]
    
    paths_for_asserting = [x.exe_path for x in test_inputs]
    # Test setup conditions - all unique programs
    assert len(set(paths_for_asserting)) == len(paths_for_asserting)
    
    # Write
    summary_dao.start_session(latenight1, latenight1.start_time)
    summary_dao.start_session(latenight2, latenight2.start_time)

    write_before_and_after_base_day(summary_dao)

    # Gather by day
    print(f"reading values for day: {test_inputs[0].start_time}")
    all_for_day: List[DailyProgramSummary] = summary_dao.read_day(test_inputs[0].start_time)

    assert isinstance(all_for_day[0], DailyProgramSummary)

    # Check the val came back out
    assert len(all_for_day) == len(test_inputs)

    for i in range(0, len(test_inputs)):
        assert all_for_day[i].exe_path_as_id in paths_for_asserting
        assert all_for_day[i].hours_spent == 0

    assert len(all_for_day) == len(test_inputs)

