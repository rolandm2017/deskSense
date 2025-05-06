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

from surveillance.db.models import DailyProgramSummary, ProgramSummaryLog, DomainSummaryLog
from surveillance.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.object.classes import ProgramSession, ChromeSession

from surveillance.util.time_wrappers import UserLocalTime
from surveillance.util.errors import TimezoneUnawareError
from surveillance.util.const import ten_sec_as_pct_of_hour
from surveillance.tz_handling.time_formatting import get_start_of_day_from_ult


from ..helper.truncation import truncate_summaries_and_logs_tables_via_session

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
    assert str(time_with_wrapper.dt.tzinfo) == str(
        some_local_tz), f"Expected both to equal {str(some_local_tz)}"

    assert time_with_wrapper.dt.hour == time_for_test.hour
    assert time_with_wrapper.dt.minute == time_for_test.minute
    assert time_with_wrapper.dt.second == time_for_test.second


# Test day boundary cases specifically
# Test entries at the edges of the day

#
# -- this is the pool of test data, please choose from it
#

# Day before base day
just_before_boundary = create_pycharm_entry(some_local_tz.localize(
    add_time(one_day_before, 23, 59, 59)))  # Just before midnight

# Base day

noon = some_local_tz.localize(add_time(base_day, 12, 0, 0))

late_night_entry = create_pycharm_entry(some_local_tz.localize(
    add_time(base_day, 23, 59, 59)))  # Just before midnight
midnight_entry = create_notion_entry(some_local_tz.localize(
    add_time(base_day, 0, 0, 1)))  # Just after midnight
abs_min_time = create_zoom_entry(
    some_local_tz.localize(add_time(base_day, 0, 0, 0)))
very_early_morning_entry = create_zoom_entry(some_local_tz.localize(add_time(base_day, 3, 0, 1))
                                             )

five_am_ish = create_notion_entry(
    some_local_tz.localize(add_time(base_day, 5, 0, 0)))

seven_am_ish = create_zoom_entry(
    some_local_tz.localize(add_time(base_day, 7, 0, 0)))

afternoon = create_pycharm_entry(
    some_local_tz.localize(add_time(base_day, 15, 0, 15)))

latenight1 = create_zoom_entry(
    some_local_tz.localize(add_time(base_day, 23, 59, 59)))
latenight2 = create_pycharm_entry(
    some_local_tz.localize(add_time(base_day, 23, 59, 59)))

# Just after end of base day

just_after_boundary = create_notion_entry(
    some_local_tz.localize(add_time(one_day_later, 0, 0, 1)))

#
# -- choose test data from the above pool!
#


def write_before_and_after_base_day(summary_dao):
    """Ensures that read_day is more specific than just 'read_all' with an arg."""
    summary_dao.start_session(just_before_boundary)
    summary_dao.start_session(just_after_boundary)


"""
You cannot use a Sqlite db for timezone related tests. 
Sqlite does not store tz info. Only pg does.
"""


@pytest_asyncio.fixture
async def setup_parts(regular_session_maker):
    """
    Only the Program suite is required here, because it's so similar to Chrome.

    This connects to the test db, unless there is an unforseen problem.
    """

    # Get all required DAOs
    program_logging_dao = ProgramLoggingDao(
        regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(regular_session_maker)
    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session_maker)

    return program_logging_dao, program_summary_dao, chrome_logging_dao, regular_session_maker


class TestSummaryDaoWithTzInfo:

    def test_away_from_edge_cases(self, setup_parts):
        """Away from edge cases, meaning, 11 am, 3 pm, 6 pm."""
        logging_dao, summary_dao, _, regular_session_maker = setup_parts

        seven_am_ish = create_zoom_entry(
            some_local_tz.localize(add_time(base_day, 7, 0, 0)))
        afternoon = create_pycharm_entry(
            some_local_tz.localize(add_time(base_day, 15, 0, 15)))

        test_inputs = [seven_am_ish, afternoon]

        paths_for_asserting = [x.exe_path for x in test_inputs]
        # Test setup conditions - all unique programs
        assert len(set(paths_for_asserting)) == len(paths_for_asserting)
        try:
            # Write
            summary_dao.start_session(seven_am_ish)
            summary_dao.start_session(afternoon)

            write_before_and_after_base_day(summary_dao)

            # Gather by day
            print(f"reading values for day: {test_inputs[0].start_time}")
            all_for_day: List[DailyProgramSummary] = summary_dao.read_day(
                test_inputs[0].start_time)

            assert isinstance(all_for_day[0], DailyProgramSummary)

            # Check the val came back out
            assert len(all_for_day) == len(test_inputs)

            for i in range(0, len(test_inputs)):
                assert all_for_day[i].exe_path_as_id in paths_for_asserting
                assert all_for_day[i].hours_spent == 0

            assert len(all_for_day) == len(test_inputs)
        finally:
            truncate_summaries_and_logs_tables_via_session(
                regular_session_maker)

    def test_on_twelve_ish_am_boundary(self, setup_parts):
        logging_dao, summary_dao, _, regular_session_maker = setup_parts

        late_night_entry = create_pycharm_entry(some_local_tz.localize(
            add_time(base_day, 23, 59, 59)))  # Just before midnight
        midnight_entry = create_notion_entry(some_local_tz.localize(
            add_time(base_day, 0, 0, 1)))  # Just after midnight
        abs_min_time = create_zoom_entry(
            some_local_tz.localize(add_time(base_day, 0, 0, 0)))

        test_inputs = [late_night_entry, midnight_entry, abs_min_time]

        paths_for_asserting = [x.exe_path for x in test_inputs]

        # Test setup conditions - all unique programs
        assert len(set(paths_for_asserting)) == len(paths_for_asserting)
        try:
            # Write
            summary_dao.start_session(late_night_entry)
            summary_dao.start_session(midnight_entry)
            summary_dao.start_session(abs_min_time)

            write_before_and_after_base_day(summary_dao)

            # Gather by day
            print(f"reading values for day: {test_inputs[0].start_time}")
            all_for_day: List[DailyProgramSummary] = summary_dao.read_day(
                test_inputs[0].start_time)

            assert isinstance(all_for_day[0], DailyProgramSummary)

            # Check the val came back out
            assert len(all_for_day) == len(test_inputs)

            for i in range(0, len(test_inputs)):
                assert all_for_day[i].exe_path_as_id in paths_for_asserting
                assert all_for_day[i].hours_spent == 0

            assert len(all_for_day) == len(test_inputs)
        finally:
            truncate_summaries_and_logs_tables_via_session(
                regular_session_maker)

    def test_on_eleven_ish_pm_boundary(self, setup_parts):
        logging_dao, summary_dao, _, session_maker = setup_parts

        latenight1 = create_zoom_entry(
            some_local_tz.localize(add_time(base_day, 23, 59, 59)))
        latenight2 = create_pycharm_entry(
            some_local_tz.localize(add_time(base_day, 23, 59, 59)))

        edge_case_micros = 999999  # HEY, LISTEN! Max value possible.
        latenight2.start_time.dt.replace(microsecond=edge_case_micros)

        test_inputs = [latenight1, latenight2]

        paths_for_asserting = [x.exe_path for x in test_inputs]
        # Test setup conditions - all unique programs
        assert len(set(paths_for_asserting)) == len(paths_for_asserting)

        try:
            # Write
            summary_dao.start_session(latenight1)
            summary_dao.start_session(latenight2)

            write_before_and_after_base_day(summary_dao)

            # Gather by day
            print(f"reading values for day: {test_inputs[0].start_time}")
            all_for_day: List[DailyProgramSummary] = summary_dao.read_day(
                test_inputs[0].start_time)

            assert isinstance(all_for_day[0], DailyProgramSummary)

            # Check the val came back out
            assert len(all_for_day) == len(test_inputs)

            for i in range(0, len(test_inputs)):
                assert all_for_day[i].exe_path_as_id in paths_for_asserting
                assert all_for_day[i].hours_spent == 0

            assert len(all_for_day) == len(test_inputs)
        finally:
            truncate_summaries_and_logs_tables_via_session(session_maker)

    def test_EST_tz(self, setup_parts):
        logging_dao, summary_dao, _, session_maker = setup_parts
        # Cook the test data so that 2 will be in the read_day func, and 2 won't be.
        # Assert that the retrieved values match in all two of day and hour.

        # Eastern Standard Time (EST)
        # UTC -4 or -5 depending on month
        est_tz = pytz.timezone("America/New_York")

        test_day = 24
        invalid1 = datetime(2025, 4, test_day - 1, 23, 55, 55)
        t1 = datetime(2025, 4, test_day, 0, 0, 1)
        t2 = datetime(2025, 4, test_day, 23, 59, 55)
        invalid2 = datetime(2025, 4, test_day + 1, 0, 3, 0)

        outside_of_range_1 = est_tz.localize(invalid1)
        outside_of_range_2 = est_tz.localize(invalid2)
        very_start_of_day = est_tz.localize(t1)
        just_before_end_of_day = est_tz.localize(t2)

        # Test setup conditions
        assert very_start_of_day.hour == t1.hour
        assert just_before_end_of_day.hour == t2.hour

        # Check the timezone name
        assert str(very_start_of_day.tzinfo) == "America/New_York"
        assert str(just_before_end_of_day.tzinfo) == "America/New_York"

        # Don't want the test to depend on what time of year it is. EST has Daylight Savings
        assert very_start_of_day.utcoffset() == timedelta(
            hours=-4) or very_start_of_day.utcoffset() == timedelta(hours=-5)
        assert just_before_end_of_day.utcoffset() == timedelta(
            hours=-4) or just_before_end_of_day.utcoffset() == timedelta(hours=-5)
        # FIXME: you didnt complete this test
        invalid_exe = "C:/Adobe/Photoshop.exe"
        invalid_process = "Photoshop.exe"
        invalid_session1 = ProgramSession(
            invalid_exe, invalid_process, "Adobe Photoshop", "picture4_final5_final.jpg", UserLocalTime(outside_of_range_1))
        invalid_session2 = ProgramSession(
            invalid_exe, invalid_process, "Adobe Photoshop", "picture4_final5_final2.jpg", UserLocalTime(outside_of_range_2))

        session1_dt_as_ult = UserLocalTime(very_start_of_day)
        session2_dt_as_ult = UserLocalTime(just_before_end_of_day)
        target_exe_path = "C:/ProgramFiles/pour.exe"
        target_process_name = "pour.exe"
        session1 = ProgramSession(
            target_exe_path, target_process_name, "Pour", "Beer pour", session1_dt_as_ult)
        session2 = ProgramSession(
            target_exe_path, target_process_name, "Pour", "Sprite pour", session2_dt_as_ult)

        # Do the writes
        try:
            summary_dao.start_session(invalid_session1)
            summary_dao.start_session(invalid_session2)

            summary_dao.start_session(session1)
            summary_dao.push_window_ahead_ten_sec(session1)
            summary_dao.push_window_ahead_ten_sec(session2)

            # Read by day
            days_entries = summary_dao.read_day(session1_dt_as_ult)

            # Check that you got the intended valuesa
            entry_one = days_entries[0]

            assert entry_one.exe_path_as_id == target_exe_path
            assert entry_one.process_name == target_process_name

            # Check that they match the original datetime's day. (hh:mm:ss isn't saved)
            assert entry_one.gathering_date_local.day == very_start_of_day.day
            assert entry_one.gathering_date_local.day == just_before_end_of_day.day
        finally:
            truncate_summaries_and_logs_tables_via_session(session_maker)

    def test_asia_tokyo_tz(self, setup_parts):
        logging_dao, summary_dao, _, session_maker = setup_parts
        # Cook the test data so that 2 will be in the read_day func, and 2 won't be.
        # Assert that the retrieved values match in all two of day and hour.

        # Asia/Tokyo
        tokyo_tz = pytz.timezone("Asia/Tokyo")  # UTC +9

        test_day = 24
        invalid1 = datetime(2025, 4, test_day - 1, 23, 55, 55)
        t1 = datetime(2025, 4, test_day, 0, 0, 1)
        t2 = datetime(2025, 4, test_day, 23, 59, 55)
        invalid2 = datetime(2025, 4, test_day + 1, 0, 3, 0)

        outside_of_range_1 = tokyo_tz.localize(invalid1)
        outside_of_range_2 = tokyo_tz.localize(invalid2)
        very_start_of_day = tokyo_tz.localize(t1)
        just_before_end_of_day = tokyo_tz.localize(t2)

        # Test setup conditions
        assert very_start_of_day.hour == t1.hour
        assert just_before_end_of_day.hour == t2.hour

        # Check the timezone name
        assert str(very_start_of_day.tzinfo) == 'Asia/Tokyo'
        assert str(just_before_end_of_day.tzinfo) == 'Asia/Tokyo'

        assert very_start_of_day.utcoffset() == timedelta(hours=9)
        assert just_before_end_of_day.utcoffset() == timedelta(hours=9)

        invalid_exe = "C:/Adobe/Photoshop.exe"
        invalid_process = "Photoshop.exe"
        invalid_session1 = ProgramSession(
            invalid_exe, invalid_process, "", "", UserLocalTime(outside_of_range_1))
        invalid_session2 = ProgramSession(
            invalid_exe, invalid_process, "", "", UserLocalTime(outside_of_range_2))

        session1_dt_as_ult = UserLocalTime(very_start_of_day)
        session2_dt_as_ult = UserLocalTime(just_before_end_of_day)
        target_exe_path = "C:/ProgramFiles/pour.exe"
        target_process_name = "pour.exe"
        session1 = ProgramSession(
            target_exe_path, target_process_name, "", "", session1_dt_as_ult)
        session2 = ProgramSession(
            target_exe_path, target_process_name, "", "", session2_dt_as_ult)

        try:
            # Do the writes
            summary_dao.start_session(invalid_session1)
            summary_dao.start_session(invalid_session2)

            summary_dao.start_session(session1)
            summary_dao.push_window_ahead_ten_sec(session1)
            summary_dao.push_window_ahead_ten_sec(session2)

            # Read by day
            days_entries = summary_dao.read_day(session1_dt_as_ult)

            # Check that you got the intended valuesa
            assert len(days_entries) == 1
            entry_one = days_entries[0]

            assert entry_one.exe_path_as_id == target_exe_path
            assert entry_one.process_name == target_process_name

            # Check that they match the original datetime's day. (hh:mm:ss isn't saved)
            assert entry_one.gathering_date_local.day == very_start_of_day.day
            assert entry_one.gathering_date_local.day == just_before_end_of_day.day
        finally:
            truncate_summaries_and_logs_tables_via_session(session_maker)

# class TestLoggingDaoWithTzInfo:
#     # TODO
#     def test_foo(self):
#         pass
