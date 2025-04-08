
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import traceback
import asyncio

from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.db.models import DailyProgramSummary, Base
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.dao.queuing.chrome_dao import ChromeDao
from surveillance.src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.services.services import TimezoneService
from surveillance.src.service_dependencies import get_dashboard_service


from surveillance.src.surveillance_manager import FacadeInjector, SurveillanceManager
from surveillance.src.object.classes import ChromeSessionData, ProgramSessionData
from surveillance.src.util.program_tools import separate_window_name_and_detail

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

async def cleanup_test_resources(manager):
    print("Cleaning up test resources...")
    
    # Clean up surveillance manager (this should now properly clean up MessageReceiver)
    try:
        await manager.cleanup()
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

@pytest_asyncio.fixture
async def test_setup_conditions(regular_session):
    # TODO: Test that the DB starts EMPTY!
    logging = ProgramLoggingDao(regular_session)
    logging2 = ChromeLoggingDao(regular_session)
    pro_sum_dao = ProgramSummaryDao(regular_session)
    chro_sum_dao = ChromeSummaryDao(regular_session)
    # vvvv = ChromeSummaryDao()
    

#       oooox
#     oox   oox
#    ox       ox
#   ox         ox
#   ox         ox
#   ox         ox
#    ox       ox
#     oox   oox
#       oooox
# First, events make their way from ProgramTracker to the Arbiter.
# # # #
# Trackers -> Arbiter

@pytest.mark.asyncio
@pytest.mark.skip(reason="temp for other tests")
async def test_tracker_to_arbiter(plain_asm, regular_session, times_from_test_data):

    program_facade = Mock()

    real_program_events = [x["event"] for x in program_data]
    real_chrome_events = chrome_data

    # Test setup
    assert all

    times_for_program_events = [x["time"] for x in program_data]

    program_durations = []

    mock_clock_times = []


    for i in range(0, len(times_for_program_events)):
        if i == len(times_for_program_events) - 1:
            current = datetime.fromisoformat(times_for_program_events[i])
            mock_clock_times.append(current)
            break
        current = datetime.fromisoformat(times_for_program_events[i])
        mock_clock_times.append(current)
        next_event = datetime.fromisoformat(times_for_program_events[i + 1])
        change = next_event - current
        program_durations.append(change)

    mock_clock = MockClock(mock_clock_times)

    class MockProgramFacade:
        def __init__(self):
            self.yield_count = 0  # Initialize the counter
            self.MAX_EVENTS = len(real_program_events)

        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for event in real_program_events:
                self.yield_count += 1
                print(f"Yielding event: {event['window_title']}")
                yield event  # Always yield the event first
            
                # Check if we've reached our limit AFTER yielding
                if self.yield_count >= self.MAX_EVENTS:
                    print(f"Reached max events limit ({self.MAX_EVENTS}), stopping generator")
                    surveillance_manager.program_thread.stop_event.set()  # stop more events from occurring
                    break

    # Then use this object instead of a Mock
    program_facade = MockProgramFacade()

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(
        side_effect=program_facade.listen_for_window_changes)
    program_facade.listen_for_window_changes = spy_on_listen_for_window

    # program_facade.listen_for_window_changes.side_effect = real_program_events

    p, c = times_from_test_data
    all_times = p + c
    testing_num_of_times = all_times + all_times + all_times + all_times
    testing_num_of_times = testing_num_of_times + testing_num_of_times
    
    def choose_program_facade(os):
        return program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade)
    # TODO: async session from the test db
    irrelevant_clock = MockClock(testing_num_of_times)
    activity_arbiter = ActivityArbiter(irrelevant_clock, pulse_interval=1)
    transition_state_mock = Mock()
    activity_arbiter.transition_state = transition_state_mock  # Unhook it so nothing past entry is called

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state
    spy_on_set_chrome_state = Mock(
        side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_chrome_state

    chrome_svc = ChromeService(irrelevant_clock, activity_arbiter)
    surveillance_manager = SurveillanceManager(mock_clock, 
        plain_asm, regular_session, chrome_svc, activity_arbiter, facades)

    program_dao_create_spy = Mock(side_effect=surveillance_manager.program_dao.create)
    surveillance_manager.program_dao.create = program_dao_create_spy

    window_change_spy = Mock(side_effect=surveillance_manager.handle_window_change)
    surveillance_manager.handle_window_change = window_change_spy

    # TODO: make the program facade, like, actually run the events.
    surveillance_manager.start_trackers()

    async def wait_for_events_to_process():
        # Wait for events to be processed
        print("\n++\n++\nWaiting for events to be processed...")
        # Give the events time to propagate through the system
        for _ in range(len(real_chrome_events) + len(real_program_events)):  # Try for up to 10 iterations
            if program_facade.yield_count == 4:
                print(program_facade.yield_count, "stop signal ++ \n ++ \n ++ \n ++")
                break
            await asyncio.sleep(1.7)  # Short sleep between checks ("short")
            # await asyncio.sleep(0.8)  # Short sleep between checks ("short")
            # Check if we have the expected number of calls
            if spy_on_set_program_state.call_count >= len(real_program_events) - 1:
                print(f"Events processed after {_+1} iterations")
                surveillance_manager.program_thread.stop()  # Stop the thread properly
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
        # ### Some stuff about setup
        num_of_events_to_enter_arbiter = len(real_program_events)
        assert program_facade.yield_count == 4, "Facade yielded more or less events than intended"
        
        assert transition_state_mock.call_count == num_of_events_to_enter_arbiter
        assert spy_on_set_chrome_state.call_count == 0
        assert spy_on_set_program_state.call_count == num_of_events_to_enter_arbiter

        # The Program DAO was called with the expected values
        one_left_in_tracker = 1
        assert program_dao_create_spy.call_count == len(real_program_events) - one_left_in_tracker

        # ### Confirm that the ... objects don't change much in their transit
        # from facade to arbiter
        for i in range(0, 4):
            event = real_program_events[i]
            call_to_compare = spy_on_set_program_state.call_args_list[i]
            
            # call_to_compare is a tuple of (args, kwargs)
            args, kwargs = call_to_compare
            print(args[0])
            # TODO: Assert all events have timezones
            
            assert args[0].window_title in event["window_title"]
            if i < 3:
                assert args[0].duration.seconds > 0
            else:
                assert args[0].duration is None  # because it hasn't been set yet
    finally:
        # Run the cleanup
        await cleanup_test_resources(surveillance_manager)

#       oooox
#     oox   oox
#    ox       ox
#   ox         ox
#   ox         ox
#   ox         ox
#    ox       ox
#     oox   oox
#       oooox
# Second, events make their way from ChromeService to the Arbiter.
# # # #
# Chrome Svc -> Arbiter

@pytest.mark.asyncio
@pytest.mark.skip("working on below test")
async def test_chrome_svc_to_arbiter_path(regular_session, plain_asm):
    chrome_events = chrome_data

    chrome_dao = ChromeDao(plain_asm)

    # Spy
    chrome_dao_create_spy = Mock(side_effect=chrome_dao.create)
    chrome_dao.create = chrome_dao_create_spy

    
    t1 = datetime.now()
    irrelevant_clock = MockClock([t1, t1, t1, t1 ,t1, t1, t1, t1, t1])

    activity_arbiter = ActivityArbiter(irrelevant_clock, pulse_interval=1)

    chrome_service = ChromeService(irrelevant_clock, arbiter=activity_arbiter, dao=chrome_dao)

    @chrome_service.event_emitter.on('tab_change')
    def handle_tab_change(tab):
        # Create and schedule the task
        activity_arbiter.set_tab_state(tab)

    timezone_service = TimezoneService()


    
    transition_state_mock = Mock()
    activity_arbiter.transition_state = transition_state_mock  # Unhook it so nothing past entry is called

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    spy_on_set_chrome_state = Mock(
        side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_chrome_state

    session_ready_for_arbiter_spy = Mock(side_effect=chrome_service.handle_session_ready_for_arbiter)
    chrome_service.handle_session_ready_for_arbiter = session_ready_for_arbiter_spy

    user_id = 1

    for tab_change_event in chrome_events:
        # Bypass for test:
        # tz_for_user = timezone_service.get_tz_for_user(
            # user_id)
        # updated_tab_change_event = timezone_service.convert_tab_change_timezone(
            # tab_change_event, tz_for_user)
        # ALSO for the test, bypass the chrome_svc queue, which 
        # (a) is known to work
        # (b) is extremely effortful to circumvent
        # so don't chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        
        # Test setup conditions
        assert isinstance(chrome_service, ChromeService)
        # Act
        chrome_service.log_tab_event(tab_change_event)
    queue_debounce_timer_wait = 1.0  # seconds
    await asyncio.sleep(queue_debounce_timer_wait)

    one_left_in_chrome_svc = 1
    assert chrome_dao_create_spy.call_count == len(chrome_events) - one_left_in_chrome_svc
    assert spy_on_set_chrome_state.call_count == len(chrome_events)
    assert session_ready_for_arbiter_spy.call_count == len(chrome_events)
    assert spy_on_set_program_state.call_count == 0, "Set program state was called in a chrome tabs test!"

    # TODO: Assert all events have timezones
    
    for i in range(0, len(chrome_events)):
        event = chrome_events[i]
        call_to_compare = spy_on_set_chrome_state.call_args_list[i]
        
        # call_to_compare is a tuple of (args, kwargs)
        args, kwargs = call_to_compare

        assert args[0].domain == event.url
        assert args[0].detail == event.tabTitle
        if i < 3:
            assert args[0].duration.seconds > 0
        else:
            assert args[0].duration is None  # because it hasn't been set yet

    #   ox         ox
    #    ox       ox
    #     oox   oox
    #       oooox
    # Then, we check that the events are there as planned.


#  ___________
# |___________| > > >
# |___________|> > > >
# |___________| > > >
# |___________|> > > >
# |___________| > > >
#
# # # # # # # # #
# Arbiter -> DAO Layer

def parse_time_string(time_str):
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

    return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds
        )

def fmt_time_string(s):
    return datetime.fromisoformat(s)

def fmt_time_string_2(s, offset="-07:00"):
    """
    Formats a time string with an optional timezone offset.
    
    Args:
        s (str): A timestamp string
        offset (str, optional): Timezone offset in format like "-07:00" for PST. 
                               Defaults to "-07:00".
    
    Returns:
        datetime: A datetime object with timezone information
    """
    # Check if the string already has timezone info
    if '+' in s or '-' in s and len(s) > 10 and s[-6] in ['+', '-']:
        # String already has timezone info, just parse it directly
        return datetime.fromisoformat(s)
    else:
        # String doesn't have timezone info, append the offset
        return datetime.fromisoformat(f"{s}{offset}")

# Events are from previous tests
program_events = [
    ProgramSessionData(title='Google Chrome', detail='X. It’s what’s happening / X',
        start_time=fmt_time_string("2025-03-22 16:14:50.201399-07:00"),
        end_time=fmt_time_string("2025-03-22 16:15:55.237392-07:00"), duration_for_tests=parse_time_string("0:01:05.035993"), productive=False),
ProgramSessionData(title='My Workspace', detail='dash | Overview',
        start_time=fmt_time_string("2025-03-22 16:15:55.237392-07:00"),
        end_time=fmt_time_string("2025-03-22 16:16:03.374304-07:00"), duration_for_tests=parse_time_string("0:00:08.136912"), productive=False),
ProgramSessionData(title='Visual Studio Code', detail='surveillance_manager.py - deskSense',
        start_time=fmt_time_string("2025-03-22 16:16:03.374304-07:00"),
        end_time=fmt_time_string("2025-03-22 16:16:17.480951-07:00"), duration_for_tests=parse_time_string("0:00:14.106647"), productive=False),
ProgramSessionData(title='Google Chrome', detail='Google',
        start_time=fmt_time_string("2025-03-22 16:16:17.480951-07:00"),
        end_time=None, duration_for_tests=None, productive=False)]

chrome_events = [
    ChromeSessionData(domain='docs.google.com', detail='Google Docs',
            start_time=fmt_time_string("2025-03-22 16:15:02-07:00"),
            end_time=fmt_time_string("2025-03-22 16:15:10-07:00"), duration_for_tests=parse_time_string("0:00:08"), productive=False),
    ChromeSessionData(domain='chatgpt.com', detail='ChatGPT',
            start_time=fmt_time_string("2025-03-22 16:15:10-07:00"),
            end_time=fmt_time_string("2025-03-22 16:15:21-07:00"), duration_for_tests=parse_time_string("0:00:11"), productive=True),
    ChromeSessionData(domain='claude.ai', detail='Claude',
            start_time=fmt_time_string("2025-03-22 16:15:21-07:00"),
            end_time=fmt_time_string("2025-03-22 16:15:30-07:00"), duration_for_tests=parse_time_string("0:00:09"), productive=True),
    ChromeSessionData(domain='chatgpt.com', detail='ChatGPT',
            start_time=fmt_time_string("2025-03-22 16:15:30-07:00"),
            end_time=None, duration_for_tests=None, productive=True)
]

@pytest.mark.asyncio
async def test_arbiter_to_dao_layer(regular_session, plain_asm, times_from_test_data):
    # TODO
    # TODO:    get the events from the prev test, feed it into this one
    # TODO:    
    # TODO

    end_of_prev_test_programs = program_events
    end_of_prev_test_tabs = chrome_events

    program_durations = []

    program_logging_dao = ProgramLoggingDao(regular_session, plain_asm)
    chrome_logging_dao = ChromeLoggingDao(regular_session, plain_asm)

    program_push_spy = Mock(side_effect=program_logging_dao.push_window_ahead_ten_sec)
    program_start_session_spy = Mock(side_effect=program_logging_dao.start_session)
    chrome_push_spy = Mock(side_effect=chrome_logging_dao.push_window_ahead_ten_sec)
    chrome_start_session_spy = Mock(side_effect=chrome_logging_dao.start_session)
    
    program_logging_dao.push_window_ahead_ten_sec = program_push_spy
    program_logging_dao.start_session = program_start_session_spy
    chrome_logging_dao.push_window_ahead_ten_sec = chrome_push_spy
    chrome_logging_dao.start_session = chrome_start_session_spy

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session, plain_asm)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session, plain_asm)
    
    
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
    
    clock = MockClock(testing_num_of_times)

    activity_arbiter = ActivityArbiter(clock, pulse_interval=0.5)

    activity_arbiter.add_summary_dao_listener(activity_recorder)

    notify_of_new_session_spy = Mock(side_effect=activity_arbiter.notify_of_new_session)
    activity_arbiter.notify_of_new_session = notify_of_new_session_spy

    # Create a spy on the notify_summary_dao method
    notify_summary_dao_spy = Mock(
        side_effect=activity_arbiter.notify_summary_dao)
    activity_arbiter.notify_summary_dao = notify_summary_dao_spy

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state
    spy_on_set_tab_state = Mock(
        side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_tab_state

    # FIXME: Using the integrated ProgramTracker is too much complexity and work.
    # FIXME: Solution: test from the beginning of the arbiter.

    print("## ##")
    print("## ## end of test")
    print("## ##")

    # ###
    # ### ### Act
    # ### ##

    # It just so happens that all tab states are after program states
    for event in end_of_prev_test_programs:
        activity_arbiter.set_program_state(event)
    for event in end_of_prev_test_tabs:
        activity_arbiter.set_tab_state(event)

    # ### ### Checkpoint:
    # ### [Arbiter layer]
    # ### The Arbiter's outbound funcs were called with the expected values
    assert spy_on_set_tab_state.call_count == len(end_of_prev_test_tabs)
    num_of_events_to_enter_arbiter = len(end_of_prev_test_programs) + len(end_of_prev_test_tabs)
    assert notify_of_new_session_spy.call_count == num_of_events_to_enter_arbiter
    
    assert spy_on_set_program_state.call_count == len(end_of_prev_test_programs)

    # ### The Arbiter recorded the expected *number* of times
    assert notify_summary_dao_spy.call_count == len(end_of_prev_test_programs)
    # The Arbiter recorded the expected total amount of time
    # TODO
    # The DAOS recorded the expected number of times
    expected_program_call_count = len(end_of_prev_test_programs)
    expected_chrome_call_count = len(end_of_prev_test_tabs)
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
    assert program_push_spy.call_count + program_start_session_spy.call_count == len(end_of_prev_test_programs)

    # The DAOs recorded the expected amount of time
    # Check the arguments that were passed were as expected
    # NOTE:
    # [0][0][0] -> program_session: ProgramSessionData,
    # [0][0][1] -> right_now: datetime
    for i in range(len(end_of_prev_test_programs)):
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
            end_of_prev_test_programs[i]["window_title"])

        assert program_session_arg.window_title == window
        assert program_session_arg.duration == program_durations[i]

    for i in range(len(real_chrome_events)):
        chrome_arg = chrome_summary_spy.call_args_list[i][0][0]
        right_now_arg = chrome_summary_spy.call_args_list[i][0][1]
        assert isinstance(chrome_arg, ChromeSessionData)
        assert isinstance(right_now_arg, datetime)

        assert chrome_arg.domain == real_chrome_events[i].url

    # # Checkpoint:
    # # Dashboard Service reports the right amount of time for get_weekly_productivity_overview
    # dashboard_service = await get_dashboard_service()

    # # Events are from 03-22, a Saturday.
    # # So we need 03-16, the prior Sunday.
    # sunday_the_16th = datetime(2025, 3, 16)
    # time_for_week = dashboard_service.get_weekly_productivity_overview(sunday_the_16th)

    # only_day_in_days = time_for_week[0]
    # production = only_day_in_days["productivity"]
    # leisure = only_day_in_days["leisure"]

    # total_program_time = 3
    # total_chrome_time = 9
    # assert production + leisure == total_program_time + total_chrome_time


# #      /\
# #     //\\
# #    //  \\
# #   //    \\
# #  //      \\
# # /_________\\
# #
# #  #  #  #  #
# # Second, we request the full week of productivity as a summary.
# # #  #  #  #
# # We verify that the total hours are as expected


# #      @@@@@
# #     @@@@@@@
# #    @@@@@@@@@
# #   @@@@@@@@@@@
# #  @@@@@@@@@@@@@
# # @@@@@@@@@@@@@@@
# #      |||||
# #      |||||
# #      |||||
# # ~~~~~~~~~~~~~~

