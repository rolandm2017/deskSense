
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import traceback
import asyncio

from datetime import datetime

from dotenv import load_dotenv
import os

from src.arbiter.activity_arbiter import ActivityArbiter
from src.arbiter.activity_recorder import ActivityRecorder
from src.db.models import DailyProgramSummary, Base
from src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

from src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

from src.services.chrome_service import ChromeService
from src.service_dependencies import get_dashboard_service


from src.surveillance_manager import FacadeInjector, SurveillanceManager
from src.object.classes import ChromeSessionData, ProgramSessionData
from src.util.program_tools import separate_window_name_and_detail

from ..mocks.mock_clock import MockClock
from ..data.captures_for_test_data_Chrome import chrome_data
from ..data.captures_for_test_data_programs import program_data


# TODO: Test the program facade to the database,
# and the Chrome service to the database,
# and then after a dozen of those,
# go from the database to the Productivity Summary, leisure:productivity

"""
The ultimate goal of this e2e test is to track down a bug in
get_weekly_productivity_overview
that is yielding like 28 hour days from 8 hours of usage.

The test must start from the facade.

This e2e uses the test database, but the facade all the way to 
the dashboard service endpoint, should be very real data, no breaks except to assert midway through.
"""

@pytest.fixture
def times_from_test_data():
    program_times = [datetime.fromisoformat(d["time"]) for d in program_data]
    chrome_times = [d.startTime for d in chrome_data]
    return program_times, chrome_times

#       oooox
#     oox   oox
#    ox       ox
#   ox         ox
#   ox         ox
#   ox         ox
#    ox       ox
#     oox   oox
#       oooox
#
# First, events are recorded.

@pytest.mark.asyncio
async def test_recording_and_reading_sessions(plain_asm, shutdown_session_maker, times_from_test_data):

    program_facade = Mock()

    real_program_events = [x["event"] for x in program_data]
    real_chrome_events = chrome_data

    times_for_program_events = [x["time"] for x in program_data]

    program_durations = []

    for i in range(0, len(times_for_program_events)):
        if i == len(times_for_program_events) - 1:
            break
        current = datetime.fromisoformat(times_for_program_events[i])
        next_event = datetime.fromisoformat(times_for_program_events[i + 1])
        change = next_event - current
        program_durations.append(change)

    class MockProgramFacade:
        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for event in real_program_events:
                # print(f"Yielding event: {event['window_title']}")
                yield event

    # Then use this object instead of a Mock
    program_facade = MockProgramFacade()

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(
        side_effect=program_facade.listen_for_window_changes)
    program_facade.listen_for_window_changes = spy_on_listen_for_window

    # # Verify it works by trying to get one event
    # try:
    #     print("Testing mock listen_for_window_changes:")
    #     generator = program_facade.listen_for_window_changes()
    #     print(f"Got generator: {generator}")
    #     # Don't actually pull an event yet as that would consume it
    # except Exception as e:
    #     print(f"Error setting up mock: {e}")

    # program_facade.listen_for_window_changes.side_effect = real_program_events

    program_logging_dao = ProgramLoggingDao(plain_asm)
    chrome_logging_dao = ChromeLoggingDao(plain_asm)

    program_push_spy = Mock(side_effect=program_logging_dao.push_window_ahead_ten_sec)
    program_start_session_spy = Mock(side_effect=program_logging_dao.start_session)
    chrome_push_spy = Mock(side_effect=chrome_logging_dao.push_window_ahead_ten_sec)
    chrome_start_session_spy = Mock(side_effect=chrome_logging_dao.start_session)
    
    program_logging_dao.push_window_ahead_ten_sec = program_push_spy
    program_logging_dao.start_session = program_start_session_spy
    chrome_logging_dao.push_window_ahead_ten_sec = chrome_push_spy
    chrome_logging_dao.start_session = chrome_start_session_spy

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, plain_asm)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, plain_asm)
    
    
    # Create spies on the DAOs' create_if_new_else_update methods
    program_summary_spy = Mock(
        side_effect=program_summary_dao.create_if_new_else_update)
    program_summary_dao.create_if_new_else_update = program_summary_spy

    chrome_summary_spy = Mock(
        side_effect=chrome_summary_dao.create_if_new_else_update)
    chrome_summary_dao.create_if_new_else_update = chrome_summary_spy

    p, c = times_from_test_data
    all_times = p + c
    testing_num_of_times = all_times + all_times + all_times + all_times
    testing_num_of_times = testing_num_of_times + testing_num_of_times
    clock_again = MockClock([])

    activity_recorder = ActivityRecorder(
        clock_again,  program_logging_dao, chrome_logging_dao, program_summary_dao, chrome_summary_dao)
    
    # update_or_create_spy = AsyncMock(side_effect=activity_recorder.update_or_create_log)
    # activity_recorder.update_or_create_log = update_or_create_spy

    # spy on logging dao methods
    
    # assert total_of_calls == len(real_program_events)  # something like that
    
    def choose_program_facade(os):
        return program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade)
    # TODO: async session from the test db
    clock = MockClock(testing_num_of_times)
    activity_arbiter = ActivityArbiter(clock, pulse_interval=0.2)

    activity_arbiter.add_summary_dao_listener(activity_recorder)

    notify_create_session_spy = Mock(side_effect=activity_arbiter.notify_of_new_session)
    activity_arbiter.notify_of_new_session = notify_create_session_spy

    # Create a spy on the notify_summary_dao method
    notify_summary_dao_spy = Mock(
        side_effect=activity_arbiter.notify_summary_dao)
    activity_arbiter.notify_summary_dao = notify_summary_dao_spy

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    chrome_svc = ChromeService(clock, activity_arbiter)
    surveillance_manager = SurveillanceManager(
        plain_asm, shutdown_session_maker, chrome_svc, activity_arbiter, facades)

    create_spy = Mock(side_effect=surveillance_manager.program_dao.create)
    surveillance_manager.program_dao.create = create_spy

    window_change_spy = Mock(side_effect=surveillance_manager.handle_window_change)
    surveillance_manager.handle_window_change = window_change_spy

    # TODO: make the program facade, like, actually run the events.
    surveillance_manager.start_trackers()

    async def wait_for_events_to_process():
        # Wait for events to be processed
        print("Waiting for events to be processed...")
        # Give the events time to propagate through the system
        for _ in range(len(real_chrome_events) + len(real_program_events)):  # Try for up to 10 iterations
            await asyncio.sleep(1.2)  # Short sleep between checks ("short")
            # Check if we have the expected number of calls
            if spy_on_set_program_state.call_count >= len(real_program_events) - 1:
                print(f"Events processed after {_+1} iterations")
                break

        # print(f"Final counts after waiting:")
        # print(f"Program facade called: {program_facade.listen_for_window_changes.call_count if hasattr(program_facade.listen_for_window_changes, 'call_count') else 'unknown'} times")
        # print(f"Setting program state called: {spy_on_set_program_state.call_count} times")
        # print(f"Window change handler called: {window_change_spy.call_count} times")

    await wait_for_events_to_process()

    print("## ##")
    print("## ## end of test")
    print("## ##")

    try:
        print(f"Program facade called: {spy_on_listen_for_window.call_count} times")
        print(f"Setting program state called: {spy_on_set_program_state.call_count} times")
        print(f"Window change handler called: {window_change_spy.call_count} times")
        # ### ### Checkpoint:
        # ### [Arbiter layer]
        # ### The Arbiter was called with the expected values
        num_of_events_to_enter_arbiter = len(real_program_events)
        final_event_left_hanging = 1
        assert spy_on_set_program_state.call_count == num_of_events_to_enter_arbiter
        assert notify_create_session_spy.call_count == num_of_events_to_enter_arbiter
        # The Program DAO was called with the expected values
        assert create_spy.call_count == num_of_events_to_enter_arbiter - final_event_left_hanging

        # ### The Arbiter recorded the expected *number* of times
        assert notify_summary_dao_spy.call_count == len(real_program_events)
        # The Arbiter recorded the expected total amount of time
        # TODO
        # The DAOS recorded the expected number of times
        expected_program_call_count = len(real_program_events)
        expected_chrome_call_count = len(real_chrome_events)
        assert program_summary_spy.call_count > 0
        assert chrome_summary_spy.call_count > 0

        assert program_summary_spy.call_count == expected_program_call_count
        assert chrome_summary_spy.call_count == expected_chrome_call_count
        # ### [Recorder layer] 
        # #
        # # The Recorder had its methods called the expected num of times,
        # assert update_or_create_spy.call_count == len(real_program_events)
        # for call in update_or_create_spy.call_args_list:
        #     args, kwargs = call
        #     # Check if the first argument is of type Foo
        #     assert isinstance(args[0], ProgramLoggingDao), f"Expected ProgramLoggingDao but got {type(args[0])}"
        #     assert isinstance(args[1], ProgramSessionData), f"Expected ProgramSessionData but got {type(args[0])}"
        
        # and the DAOs too
        assert program_push_spy.call_count + program_start_session_spy.call_count == len(real_program_events)

        # The DAOs recorded the expected amount of time
        # Check the arguments that were passed were as expected
        # NOTE:
        # [0][0][0] -> program_session: ProgramSessionData,
        # [0][0][1] -> right_now: datetime
        for i in range(len(real_program_events)):
            program_session_arg = program_summary_spy.call_args_list[i][0][0]
            right_now_arg = program_summary_spy.call_args_list[i][0][1]
            assert isinstance(program_session_arg, ProgramSessionData)
            assert isinstance(right_now_arg, datetime)

            # Transformation happens in the ProgramTracker:
            # detail, window = separate_window_name_and_detail(
            #     window_change_dict["window_title"])
            # new_session.window_title = window
            # new_session.detail = detail

            detail, window = separate_window_name_and_detail(
                real_program_events[i]["window_title"])

            assert program_session_arg.window_title == window
            assert program_session_arg.duration == program_durations[i]

        for i in range(len(real_chrome_events)):
            chrome_arg = chrome_summary_spy.call_args_list[i][0][0]
            right_now_arg = chrome_summary_spy.call_args_list[i][0][1]
            assert isinstance(chrome_arg, ChromeSessionData)
            assert isinstance(right_now_arg, datetime)

            assert chrome_arg.domain == real_chrome_events[i].url

        # Checkpoint:
        # Dashboard Service reports the right amount of time for get_weekly_productivity_overview
        dashboard_service = await get_dashboard_service()

        # Events are from 03-22, a Saturday.
        # So we need 03-16, the prior Sunday.
        sunday_the_16th = datetime(2025, 3, 16)
        time_for_week = dashboard_service.get_weekly_productivity_overview(sunday_the_16th)

        only_day_in_days = time_for_week[0]
        production = only_day_in_days["productivity"]
        leisure = only_day_in_days["leisure"]

        total_program_time = 3
        total_chrome_time = 9
        assert production + leisure == total_program_time + total_chrome_time

    finally:
        async def cleanup_test_resources():
            print("Cleaning up test resources...")
            
            # Clean up surveillance manager (this should now properly clean up MessageReceiver)
            try:
                await surveillance_manager.cleanup()
            except Exception as e:
                print(f"Error during surveillance_manager cleanup: {e}")
                traceback.print_exc()
            
            # Allow some time for all resources to be properly cleaned up
            await asyncio.sleep(0.5)
            
            # Ensure all asyncio tasks are properly awaited or cancelled
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if tasks:
                print(f"Cancelling {len(tasks)} remaining tasks...")
                for task in tasks:
                    if not task.done():
                        task.cancel()
                
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=1.0)
                except asyncio.TimeoutError:
                    print("Some tasks did not complete in time during test cleanup")
            
            print("Test resources cleanup completed")

        # Run the cleanup
        await cleanup_test_resources()

    #   ox         ox
    #    ox       ox
    #     oox   oox
    #       oooox
    # Then, we check that the events are there as planned.

#      /\
#     //\\
#    //  \\
#   //    \\
#  //      \\
# /_________\\
#
#  #  #  #  #
# Second, we request the full week of productivity as a summary.
# #  #  #  #
# We verify that the total hours are as expected


#      @@@@@
#     @@@@@@@
#    @@@@@@@@@
#   @@@@@@@@@@@
#  @@@@@@@@@@@@@
# @@@@@@@@@@@@@@@
#      |||||
#      |||||
#      |||||
# ~~~~~~~~~~~~~~

