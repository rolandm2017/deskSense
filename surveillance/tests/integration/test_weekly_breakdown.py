# tests/integration/test_weekly_breakdown.py

"""
The file is testing this:
@app.get("/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)

But without the hassle of running the server to make a GET request.

The point of the test is to verify precise accuracy with the outcome of adding
sessions into the db. The data should match exactly, and everything should be understood.

"""
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

import pytz
from datetime import datetime, timedelta


from typing import List


from surveillance.src.services.dashboard_service import DashboardService

from surveillance.src.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.db.models import Base, DailyDomainSummary, DailyProgramSummary
from surveillance.src.object.classes import CompletedChromeSession, CompletedProgramSession
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.time_wrappers import UserLocalTime

from ..helper.truncation import truncate_summaries_and_logs_tables_via_session

from ..data.weekly_breakdown_programs import (
    duplicate_programs_march_2, duplicate_programs_march_3rd,
    programs_march_2nd, programs_march_3rd,
    march_2_2025, march_3_2025, feb_23_2025, feb_24_2025, feb_26_2025,
    march_2_program_count, march_3_program_count, unique_programs, feb_program_count,
    programs_feb_23, programs_feb_24, programs_feb_26, weekly_breakdown_tz
)

from ..data.weekly_breakdown_chrome import (
    duplicates_chrome_march_2, duplicates_chrome_march_3rd,
    chrome_march_2nd, chrome_march_3rd,
    march_2_chrome_count, march_3_chrome_count, unique_domains, feb_chrome_count,
    chrome_feb_23, chrome_feb_24, chrome_feb_26
)


from ..mocks.mock_clock import MockClock


# FIXME: Turtle slow test: use in memory db?


@pytest_asyncio.fixture
async def setup_parts(regular_session, async_engine_and_asm):
    """
    Fixture that initializes a DashboardService instance for testing.
    This connects to the test db, unless there is an unforseen problem.
    """
    _, asm = async_engine_and_asm

    session_maker_async: async_sessionmaker = asm

    # Get all required DAOs
    timeline_dao = TimelineEntryDao(session_maker_async)
    program_logging_dao = ProgramLoggingDao(
        regular_session)
    chrome_logging_dao = ChromeLoggingDao(regular_session)
    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session)

    # Create and return the dashboard service
    service = DashboardService(
        timeline_dao=timeline_dao,
        program_summary_dao=program_summary_dao,
        program_logging_dao=program_logging_dao,
        chrome_summary_dao=chrome_summary_dao,
        chrome_logging_dao=chrome_logging_dao
    )

    yield service, program_summary_dao, chrome_summary_dao, regular_session
    # Clean up if needed
    # If your DAOs have close methods, you could call them here


def setup_program_writes_for_group(group_of_test_data, program_summary_dao, must_be_from_month):
    """"""
    for dummy_program_session in group_of_test_data:
        assert isinstance(dummy_program_session, CompletedProgramSession)
        assert isinstance(
            dummy_program_session.end_time, UserLocalTime), "Setup conditions not met"
        assert must_be_from_month == dummy_program_session.end_time.dt.month

        if 'TEST' not in dummy_program_session.window_title:
            raise ValueError("Test setup requires 'TEST' string in all window titles")


        # TODO: method to find if the program already exists for a given date
        session_from_today = program_summary_dao.find_todays_entry_for_program(
            dummy_program_session)
        if session_from_today:
            # A program exists in the db already, so, extend its time
            program_summary_dao.push_window_ahead_ten_sec(dummy_program_session)
        else:
            program_summary_dao.start_session(
                dummy_program_session, dummy_program_session.end_time)


def setup_chrome_writes_for_group(group_of_test_data, chrome_summary_dao, must_be_from_month):
    for dummy_chrome_session in group_of_test_data:
        assert isinstance(dummy_chrome_session, CompletedChromeSession)

        session_from_today = chrome_summary_dao.find_todays_entry_for_domain(
            dummy_chrome_session)
        if session_from_today:
            print(f"Already added: ", dummy_chrome_session.domain)
            chrome_summary_dao.push_window_ahead_ten_sec(dummy_chrome_session)
        else:
            chrome_summary_dao.start_session(
                dummy_chrome_session, dummy_chrome_session.end_time)

        # chrome_summary_dao.create_if_new_else_update(session, right_now_arg)


@pytest_asyncio.fixture
async def setup_with_populated_db(setup_parts):

    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    service, program_summary_dao, chrome_summary_dao, session_maker = setup_parts

    truncate_summaries_and_logs_tables_via_session(session_maker)

    test_data_feb_programs = programs_feb_23() + programs_feb_24() + \
        programs_feb_26()

    test_data_feb_chrome = chrome_feb_23() + chrome_feb_24() + \
        chrome_feb_26()

    test_data_march_programs = programs_march_2nd() + programs_march_3rd() + \
        duplicate_programs_march_2() + duplicate_programs_march_3rd()

    test_data_march_chrome = chrome_march_2nd() + \
        chrome_march_3rd() + duplicates_chrome_march_2() + \
        duplicates_chrome_march_3rd()

    #
    #
    # starting sessions for the programs and domains from February
    #
    # ## February!! February!
    # ## February!! February!
    # ## February!! February!
    #

    february = 2
    setup_program_writes_for_group(
        test_data_feb_programs, program_summary_dao, february)

    setup_chrome_writes_for_group(
        test_data_feb_chrome, chrome_summary_dao, february)

    assert all(isinstance(s, CompletedProgramSession)
               for s in test_data_feb_programs), "There was a bug in setup"
    assert all(isinstance(s, CompletedChromeSession)
               for s in test_data_feb_chrome), "There was a bug in setup"

    programs_sum = timedelta()
    chrome_sum = timedelta()
    for session in test_data_feb_programs:
        programs_sum = programs_sum + session.duration
    for session in test_data_feb_chrome:
        if session.duration:
            chrome_sum = chrome_sum + session.duration

    #
    # ## #    March    # ## ## ##     March   ## ## ## ##     March    ## ## ##
    #
    # starting sessions for the programs and domains from March
    #
    #
    march = 3
    setup_program_writes_for_group(
        test_data_march_programs, program_summary_dao, march)

    setup_chrome_writes_for_group(
        test_data_march_chrome, chrome_summary_dao, march)

    test_programs_and_domains = {"feb_programs": test_data_feb_programs,
                                 "feb_chrome": test_data_feb_chrome,
                                 "march_programs": test_data_march_programs,
                                 "march_chrome": test_data_march_chrome}

    yield service, program_summary_dao, chrome_summary_dao, test_programs_and_domains


@pytest.mark.asyncio
async def test_read_all(setup_with_populated_db):
    """This test is mostly testing setup conditions for other tests."""
    _, program_summary_dao, chrome_summary_dao, test_programs_and_domains = setup_with_populated_db

    feb_vals_from_db = []
    march_2_vals_from_db = []
    march_3rd_vals_from_db = []

    all_programs_for_verification = program_summary_dao.read_all()

    # FIXME: another date conversion issue. it APPEARS to be written on 03-01 even though
    # it was wrote on march 2 or 3. Because PST -> UTC or vice versa causes days to change
    print(len(all_programs_for_verification), "vvv")

    just_retrieved_program_names_from_db = [
        x.program_name for x in all_programs_for_verification]

    print("just_retrieved_program_names:",
          just_retrieved_program_names_from_db)

    test_programs = test_programs_and_domains["feb_programs"] + \
        test_programs_and_domains["march_programs"]
    
    for dummy_data in test_programs:
        assert dummy_data.window_title in just_retrieved_program_names_from_db, "A program was missing"

    march_1 = 1  # because of postgres
    march_2 = 2  # because of postgres

    def sort_programs_by_date():    
        for v in all_programs_for_verification:
            if v.gathering_date.month == 2:
                feb_vals_from_db.append(v)
            elif v.gathering_date.month == 3 and v.gathering_date.day == march_1:
                march_2_vals_from_db.append(v)
            elif v.gathering_date.month == 3 and v.gathering_date.day == march_2:
                march_3rd_vals_from_db.append(v)

    sort_programs_by_date()

    # -- Compare to the per-day retrievals:


        # MISSING:

    # ProgramSession(window_title='SpotifyTEST', detail='Background music while working',
    #         start_time=UserLocalTime(2025-03-02 12:49:00+00:00),
    #         end_time=UserLocalTime(2025-03-02 13:30:00+00:00), duration=0:41:00, productive=False)

    print("\n\n\nDEBUG: Timestamps for feb_vals_from_db:")
    for v in feb_vals_from_db:
        print(f"Program: {v.program_name}, Date: {v.gathering_date}, TZ Info: {v.gathering_date.tzinfo}")

    print("\nDEBUG: Timestamps for march_2_vals_from_db:")
    for v in march_2_vals_from_db:
        print(f"Program: {v.program_name}, Date: {v.gathering_date}, TZ Info: {v.gathering_date.tzinfo}")

    print("\nDEBUG: Timestamps for march_3rd_vals_from_db:")
    for v in march_3rd_vals_from_db:
        print(f"Program: {v.program_name}, Date: {v.gathering_date}, TZ Info: {v.gathering_date.tzinfo}")


    # for k in test_programs_and_domains["feb_programs"]:
    #     print(k, "\n")

    print("## from the db")
    # for k in march_3rd_vals_from_db:
    #     print(k, "\n")

    def assert_day_has_only_unique_strings(days_vals):
        """ Function says 'So they're all, like, uniques.' 
            Only makes sense if you run it on a single day.
        """
        
        exe_paths_from_db_entries = [
            x.exe_path_as_id for x in days_vals]
        assert len(set(exe_paths_from_db_entries)) == len(
            exe_paths_from_db_entries), "Array contains duplicate strings"
        
    # FIXME: In the above func, vsCode is in there twice for feb_vals_from_db

    # feb_23_read_by_day = program_summary_dao.read_day(UserLocalTime(feb_23_2025)),
    # feb_24_read_by_day = program_summary_dao.read_day(UserLocalTime(feb_24_2025)),
    # feb_26_read_by_day = program_summary_dao.read_day(UserLocalTime(feb_26_2025))
                       

    assert len(
        feb_vals_from_db) == feb_program_count, "Count did not match expected, February"
    
    # NOTE that "assert_has_only_unique_strings(feb_vals_from_db)" is nonsense!
    # The feb vals span multiple days, so of course there are duplicates.

    march_2_entries = program_summary_dao.read_day(
        UserLocalTime(march_2_2025))    

    assert len(
        march_2_vals_from_db) == march_2_program_count, "Count did not match expected, for March 2"
    assert_day_has_only_unique_strings(march_2_vals_from_db)
    
    
    march_3_entries = program_summary_dao.read_day(
        UserLocalTime(march_3_2025))
    
    assert len(
        march_3rd_vals_from_db) == march_3_program_count, "Count did not match expected, for March 3rd"
    assert_day_has_only_unique_strings(march_3rd_vals_from_db)


    # Do a simple check that the total programs retrieved
    # matches the number of programs entered
    # NOTE: So, a program is being recorded into the same place it was before
    # i.e., Code.exe shows up 3 times, it gets added to the same row. Working as intended
    total_count_of_unique_programs = feb_program_count + \
        march_2_program_count + march_3_program_count

    assert len(all_programs_for_verification) == total_count_of_unique_programs, "A program must have not been added, or 'all' means something differnt"

 
    """
    --
    -- Chrome section
    -- 
    """

    feb_vals_chrome = []

    chrome_march2_vals = []
    chrome_march_3rd_vals = []

    all_domains_for_verify = chrome_summary_dao.read_all()

    print(len(all_domains_for_verify), "vvv")

    def sort_by_date():    
        for v in all_domains_for_verify:
            if v.gathering_date.month == 2:
                feb_vals_chrome.append(v)
            elif v.gathering_date.month == 3 and v.gathering_date.day == march_1:
                chrome_march2_vals.append(v)
            elif v.gathering_date.month == 3 and v.gathering_date.day == march_2:
                chrome_march_3rd_vals.append(v)

    sort_by_date()


    assert len(feb_vals_chrome) == feb_chrome_count
    assert len(
        chrome_march2_vals) == march_2_chrome_count, "A Chrome entry was missing"
    assert len(
        chrome_march_3rd_vals) == march_3_chrome_count, "A Chrome entry was missing"
    



@pytest.mark.asyncio
async def test_reading_individual_days(setup_with_populated_db):
    _, program_summary_dao, chrome_summary_dao, _ = setup_with_populated_db

    test_day_3 = UserLocalTime(march_3_2025 + timedelta(days=1))

    march_2_2025_ult = UserLocalTime(march_2_2025 + timedelta(minutes=43))

    # NOTE that this date is in the test data for sure! it's circular.

    daily_program_summaries: List[DailyProgramSummary] = program_summary_dao.read_day(
        march_2_2025_ult)
    daily_chrome_summaries: List[DailyDomainSummary] = chrome_summary_dao.read_day(
        march_2_2025_ult)

    print(len(daily_program_summaries), march_2_program_count)
    assert len(daily_program_summaries) == march_2_program_count
    assert len(daily_chrome_summaries) == march_2_chrome_count

    # ### Assert that the expected programs, domains are all in there

    # ### Continue asserting that expected domains, programs are all in there

    march_3_modified = UserLocalTime(
        march_3_2025 + timedelta(hours=1, minutes=9, seconds=33))

    daily_program_summaries_2: List[DailyProgramSummary] = program_summary_dao.read_day(
        march_3_modified)
    daily_chrome_summaries_2: List[DailyDomainSummary] = chrome_summary_dao.read_day(
        march_3_modified)

    assert len(
        daily_program_summaries_2) == march_3_program_count, "A program session didn't load"
    assert len(
        daily_chrome_summaries_2) == march_3_chrome_count, "A Chrome session didn't load"

    count_of_march_2 = march_2_program_count + march_2_chrome_count
    count_of_march_3 = march_3_program_count + march_3_chrome_count

    assert len(daily_program_summaries) + \
        len(daily_chrome_summaries) == count_of_march_2
    assert len(daily_program_summaries_2) + \
        len(daily_chrome_summaries_2) == count_of_march_3

    zero_pop_day_programs: List[DailyProgramSummary] = program_summary_dao.read_day(
        test_day_3)
    zero_pop_day_chrome: List[DailyDomainSummary] = chrome_summary_dao.read_day(
        test_day_3)

    assert len(zero_pop_day_programs) + len(zero_pop_day_chrome) == 0


@pytest.mark.asyncio
async def test_week_of_feb_23(setup_with_populated_db):
    service, _, _, _ = setup_with_populated_db
    dashboard_service = service

    feb_23_2025_dt =weekly_breakdown_tz.localize(datetime(2025, 2, 23))  # Year, Month, Day
    # ### ###
    # # Check the test data to see what's in here
    # ### ###
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(UserLocalTime(feb_23_2025_dt))

    assert all(isinstance(d, dict)
               for d in weeks_overview), "Expected types not found"
    assert all(
        "day" in d and "productivity" in d and "leisure" in d for d in weeks_overview), "Expected keys not found"

    # Assert that no  day has more than 16 hours of recorded time
    sums = [d["productivity"] + d["leisure"] for d in weeks_overview]
    assert all(
        x < 16 for x in sums), "Some day had 16 hours or more of time recorded"


@pytest.mark.asyncio
async def test_week_of_march_2(setup_with_populated_db):
    dashboard_service = setup_with_populated_db[0]
    march_2_2025_dt = weekly_breakdown_tz.localize(datetime(2025, 3, 2))  # Year, Month, Day

    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(UserLocalTime(march_2_2025_dt))

    assert all(isinstance(d, dict)
               for d in weeks_overview), "Expected types not found"
    assert all(
        "day" in d and "productivity" in d and "leisure" in d for d in weeks_overview), "Expected keys not found"

    # Assert that no  day has more than 24 hours of recorded time
    sums = [d["productivity"] + d["leisure"] for d in weeks_overview]
    assert all(
        x < 16 for x in sums), "Some day had 16 hours or more of time recorded"
