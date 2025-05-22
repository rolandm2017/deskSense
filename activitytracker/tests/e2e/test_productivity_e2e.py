import traceback

import pytest_asyncio

import pytest
from unittest.mock import Mock

import asyncio

import pytz
from datetime import datetime, timedelta

from typing import cast

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.config.definitions import imported_local_tz_str, window_push_length
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.facade.facade_singletons import (
    get_keyboard_facade_instance,
    get_mouse_facade_instance,
)
from activitytracker.object.classes import (
    ChromeSession,
    ProgramSession,
    TabChangeEventWithLtz,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.services.tiny_services import TimezoneService
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.tz_handling.time_formatting import convert_to_utc
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.program_tools import separate_window_name_and_detail
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.captures_for_test_data_Chrome import chrome_data
from ..data.captures_for_test_data_programs import program_data
from ..helper.confirm_chronology import get_durations_from_test_data
from ..mocks.mock_clock import MockClock, UserLocalTimeMockClock
from ..mocks.mock_engine_container import MockEngineContainer
from ..mocks.mock_message_receiver import MockMessageReceiver

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


some_local_tz = pytz.timezone(imported_local_tz_str)


@pytest.fixture
def times_from_test_data():
    program_times = [datetime.fromisoformat(d["time"]) for d in program_data]
    chrome_times = [d.startTime for d in chrome_data]
    return program_times, chrome_times


async def cleanup_test_resources(manager):
    print("Cleaning up test resources...")

    # Clean up activitytracker manager (this should now properly clean up
    # MessageReceiver)
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
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=1.0
            )
        except asyncio.TimeoutError:
            print("Some tasks did not complete in time during test cleanup")

    print("Test resources cleanup completed")


@pytest_asyncio.fixture
async def test_setup_conditions(regular_session_maker, plain_asm):
    program_logging = ProgramLoggingDao(regular_session_maker)
    chrome_logging = ChromeLoggingDao(regular_session_maker)
    program_summaries_dao = ProgramSummaryDao(program_logging, regular_session_maker)
    chrome_summaries_dao = ChromeSummaryDao(chrome_logging, regular_session_maker)

    p_logs = program_logging.read_all()
    ch_logs = chrome_logging.read_all()
    pro_sum = program_summaries_dao.read_all()
    chrome_summaries = chrome_summaries_dao.read_all()

    assert len(p_logs) == 0, "An important table was not empty"
    assert len(ch_logs) == 0, "An important table was not empty"
    assert len(pro_sum) == 0, "An important table was not empty"
    assert len(chrome_summaries) == 0, "An important table was not empty"

    # vvvv = ChromeSummaryDao()


# #       1111
# #      11111
# #         11
# #         11
# #         11
# #         11
# #         11
# #     111111111
# # First, events make their way from ProgramTracker to the Arbiter.
# # # # #
# # Trackers -> Arbiter


# FIXME: integrate with the 3rd test
@pytest.mark.asyncio
async def test_program_tracker_to_arbiter(
    plain_asm, regular_session_maker, times_from_test_data
):

    real_program_events = [x["event"] for x in program_data]

    times_for_program_events = [x["time"] for x in program_data]

    mock_clock_times = []

    for i in range(0, len(times_for_program_events)):
        current = datetime.fromisoformat(times_for_program_events[i])
        mock_clock_times.append(UserLocalTime(current))

    for v in mock_clock_times:
        assert isinstance(v, UserLocalTime)

    mock_clock = UserLocalTimeMockClock(mock_clock_times)

    class MockProgramFacade:
        def __init__(self):
            self.yield_count = 0  # Initialize the counter
            self.MAX_EVENTS = len(real_program_events)

        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for program_event in real_program_events:
                self.yield_count += 1
                print(f"Yielding event: {program_event['window_title']}")
                yield program_event  # Always yield the event first

                # Check if we've reached our limit AFTER yielding
                if self.yield_count >= self.MAX_EVENTS:
                    print(
                        f"Reached max events limit ({
                            self.MAX_EVENTS}), stopping generator"
                    )
                    # stop more events from occurring
                    surveillance_manager.program_thread.stop_event.set()
                    break

    # Then use this object instead of a Mock
    program_facade = MockProgramFacade()

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(side_effect=program_facade.listen_for_window_changes)
    program_facade.listen_for_window_changes = spy_on_listen_for_window

    p, c = times_from_test_data
    all_times = p + c
    testing_num_of_times = all_times + all_times + all_times + all_times
    testing_num_of_times = testing_num_of_times + testing_num_of_times

    def choose_program_facade(current_os):
        return program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade
    )

    mock_user_facing_clock = MockClock(testing_num_of_times)

    durations = times_from_test_data[0]

    container = MockEngineContainer(durations)

    sys_status_dao = SystemStatusDao(
        cast(UserFacingClock, mock_user_facing_clock), 10, regular_session_maker
    )

    activity_arbiter = ActivityArbiter(mock_user_facing_clock, sys_status_dao, container)
    transition_state_mock = Mock()
    # Unhook it so nothing past entry is called
    activity_arbiter.transition_state = transition_state_mock

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state
    spy_on_set_chrome_state = Mock(side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_chrome_state

    mock_message_receiver = MockMessageReceiver()

    chrome_svc = ChromeService(mock_user_facing_clock, activity_arbiter)
    surveillance_manager = SurveillanceManager(
        cast(UserFacingClock, mock_clock),
        plain_asm,
        regular_session_maker,
        chrome_svc,
        activity_arbiter,
        facades,
        mock_message_receiver,
        sys_status_dao,
        True,
    )

    window_change_spy = Mock(
        side_effect=surveillance_manager.program_tracker.window_change_handler
    )
    surveillance_manager.program_tracker.window_change_handler = window_change_spy

    # --
    # -- Act (1)
    # --

    surveillance_manager.start_trackers()

    async def wait_for_events_to_process():
        # Wait for events to be processed
        print("\n++\n++\nWaiting for events to be processed...")
        # Give the events time to propagate through the system
        # Try for up to 10 iterations
        for _ in range(len(real_program_events)):
            if program_facade.yield_count == len(real_program_events):
                print(program_facade.yield_count, "stop signal ++ \n ++ \n ++ \n ++")
                break
            await asyncio.sleep(1.7)  # Short sleep between checks ("short")
            # await asyncio.sleep(0.8)  # Short sleep between checks ("short")
            # Check if we have the expected number of calls
            if spy_on_set_program_state.call_count >= len(real_program_events) - 1:
                print(f"Events processed after {_+1} iterations")
                surveillance_manager.program_thread.stop()  # Stop the thread properly
                break

    await wait_for_events_to_process()

    print("## ##")
    print("## ## end of test")
    print("## ##")

    try:
        # ### Some stuff about setup
        num_of_events_to_enter_arbiter = len(real_program_events)
        assert (
            spy_on_listen_for_window.call_count == 1
        ), "Listen for window changes was supposed to run once"
        assert (
            program_facade.yield_count == num_of_events_to_enter_arbiter
        ), "Facade yielded more or less events than intended"

        assert (
            window_change_spy.call_count == num_of_events_to_enter_arbiter
        ), "Window change wasn't called once per new program"

        for i in range(0, num_of_events_to_enter_arbiter):
            call_to_compare = window_change_spy.call_args_list[i]

            args, _ = call_to_compare

            assert isinstance(args[0], ProgramSession)
            assert isinstance(args[0].start_time, UserLocalTime)
            assert isinstance(args[0].start_time.dt, datetime)
            assert args[0].end_time is None

        for i in range(0, 4):
            call_to_compare = spy_on_set_program_state.call_args_list[i]

            args, _ = call_to_compare

            assert isinstance(args[0], ProgramSession)
            assert isinstance(args[0].start_time, UserLocalTime)
            assert isinstance(args[0].start_time.dt, datetime)
            assert args[0].end_time is None

        assert transition_state_mock.call_count == num_of_events_to_enter_arbiter
        assert spy_on_set_chrome_state.call_count == 0
        assert spy_on_set_program_state.call_count == num_of_events_to_enter_arbiter

        # # The Program DAO was called with the expected values
        one_left_in_tracker = 1
        # assert program_dao_create_spy.call_count == len(
        #     real_program_events) - one_left_in_tracker

        # ### Confirm that the objects don't change much in their transit
        # from facade to arbiter
        for i in range(0, 4):
            event = real_program_events[i]
            call_to_compare = spy_on_set_program_state.call_args_list[i]

            # call_to_compare is a tuple of (args, kwargs)
            args, kwargs = call_to_compare
            # print("For next test:")
            # print('args0', args[0])   # Uncomment to record for next test
            # TODO: Assert all events have timezones

            assert args[0].window_title in event["window_title"]
            assert isinstance(args[0].start_time, UserLocalTime)
            assert isinstance(args[0].start_time.dt, datetime)
            assert (
                args[0].end_time is None
            ), "How could end time be set before entering the arbiter?"
            assert (
                args[0].duration is None
            ), "How could duration be set before entering the arbiter?"
        # assert 1 == 2  # Uncomment to print data for next test
    finally:
        # Run the cleanup
        await cleanup_test_resources(surveillance_manager)


# # #    222222
# # #   22    22
# # #        22
# # #       22
# # #      22
# # #     22
# # #    22
# # #   2222222222
# # Second, events make their way from ChromeService to the Arbiter.
# # # # #
# # Chrome Svc -> Arbiter


@pytest.mark.asyncio
# @pytest.mark.skip
# @pytest.mark.skip("working on below test")
async def test_chrome_svc_to_arbiter_path(regular_session_maker):
    chrome_events_for_test = chrome_data

    # chrome_dao = ChromeDao(plain_asm)

    # # Spy
    # chrome_dao_create_spy = Mock(side_effect=chrome_dao.create)
    # chrome_dao.create = chrome_dao_create_spy

    t1 = datetime.now()
    irrelevant_clock = MockClock([t1, t1, t1, t1, t1, t1, t1, t1, t1])

    container = MockEngineContainer([])

    sys_status_dao = SystemStatusDao(
        cast(UserFacingClock, irrelevant_clock), 10, regular_session_maker
    )

    activity_arbiter = ActivityArbiter(irrelevant_clock, sys_status_dao, container)

    chrome_service = ChromeService(irrelevant_clock, arbiter=activity_arbiter)

    @chrome_service.event_emitter.on("tab_change")
    def handle_tab_change(tab):
        # Create and schedule the task
        activity_arbiter.set_tab_state(tab)

    # timezone_service = TimezoneService()

    transition_state_mock = Mock()
    # Unhook it so nothing past entry is called
    activity_arbiter.transition_state = transition_state_mock

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    spy_on_set_chrome_state = Mock(side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_chrome_state

    session_ready_for_arbiter_spy = Mock(
        side_effect=chrome_service.handle_session_ready_for_arbiter
    )
    chrome_service.handle_session_ready_for_arbiter = session_ready_for_arbiter_spy

    user_id = 1

    timezone_service = TimezoneService()

    # --
    # -- -- Act (2)
    # --

    for tab_change_event in chrome_events_for_test:
        # Bypass for test:
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event = timezone_service.convert_tab_change_timezone(
            tab_change_event, tz_for_user
        )
        # ALSO for the test, bypass the chrome_svc queue, which
        # (a) is known to work
        # (b) is extremely effortful to circumvent
        # so don't
        # chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)

        # Test setup conditions
        assert isinstance(chrome_service, ChromeService)
        assert isinstance(updated_tab_change_event, TabChangeEventWithLtz)
        assert isinstance(updated_tab_change_event.start_time_with_tz, UserLocalTime)
        # FIXME: >           concluding_start_time: datetime = self.last_entry.start_time.dt
        # FIXME:            AttributeError: 'datetime.datetime' object has no attribute 'dt'
        # Act
        chrome_service.log_tab_event(updated_tab_change_event)
    queue_debounce_timer_wait = 1.0  # seconds
    await asyncio.sleep(queue_debounce_timer_wait)

    one_left_in_chrome_svc = 1
    # assert chrome_dao_create_spy.call_count == len(
    #     chrome_events_for_test) - one_left_in_chrome_svc
    assert spy_on_set_chrome_state.call_count == len(chrome_events_for_test)
    assert session_ready_for_arbiter_spy.call_count == len(chrome_events_for_test)
    assert (
        spy_on_set_program_state.call_count == 0
    ), "Set program state was called in a chrome tabs test!"

    # TODO: Assert all events have timezones

    for i in range(0, len(chrome_events_for_test)):
        event = chrome_events_for_test[i]
        call_to_compare = spy_on_set_chrome_state.call_args_list[i]

        # call_to_compare is a tuple of (args, kwargs)
        args, _ = call_to_compare
        # print("For next test:")
        # print(args[0])  # Uncomment to record for next test

        assert args[0].domain == event.url
        assert args[0].detail == event.tabTitle
        assert isinstance(args[0].start_time, UserLocalTime)
        assert args[0].end_time is None
        assert args[0].duration is None
    # assert 1 == 2  # Uncomment to enable capturing test data

    # Then, we check that the events are there as planned.


#    333333
#   33    33
#         33
#      3333
#         33
#         33
#   33    33
#    333333

# # # # # # # # #
# Arbiter -> DAO Layer


def parse_time_string(time_str):
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split(".")
    seconds = int(seconds_parts[0])
    microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

    return timedelta(
        hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds
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
    if "+" in s or "-" in s and len(s) > 10 and s[-6] in ["+", "-"]:
        # String already has timezone info, just parse it directly
        return datetime.fromisoformat(s)
    else:
        # String doesn't have timezone info, append the offset
        return datetime.fromisoformat(f"{s}{offset}")


# NOTE I COOKED these numbers manually, they DO NOT reflect the times from the prev tests.
# TODO: Cook the above test's inputs so that they come out with LINEAR
# sessions program -> chrome & 1-10 sec durations


imaginary_path_to_chrome = "C:/imaginary/path/to/Photoshop.exe"
imaginary_chrome_processe = "Photoshop.exe"
adobe_photoshop = "Adobe Photoshop"

pr_events_v2 = [
    ProgramSession(
        exe_path=imaginary_path_to_chrome,
        process_name=imaginary_chrome_processe,
        window_title=adobe_photoshop,  # Previously Chrome
        detail="X. It’s what’s happening / X",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:14:50.201399-07:00")),
    ),
    ProgramSession(
        exe_path="C:/wherever/you/find/Postman.exe",
        process_name="Xorg",
        window_title="My Workspace",
        detail="dash | Overview",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:15:55.237392-07:00")),
    ),
    ProgramSession(
        exe_path="C:/path/to/VSCode.exe",
        process_name="Code.exe",
        window_title="Visual Studio Code",
        detail="surveillance_manager.py - deskSense",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:03.374304-07:00")),
    ),
    # NOTE: Manual change from Gnome Shell to a second Chrome entry
    ProgramSession(
        exe_path=imaginary_path_to_chrome,
        process_name=imaginary_chrome_processe,
        window_title=adobe_photoshop,  # Previously Chrome
        detail="Google",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:17.480951-07:00")),
    ),
]

# May 1: Had to cook the numbers manually more
ch_events_v2 = [
    ChromeSession(
        domain="docs.google.com",
        detail="Google Docs",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:23-07:00")),
    ),
    ChromeSession(
        domain="chatgpt.com",
        detail="ChatGPT",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:31-07:00")),
    ),
    ChromeSession(
        domain="claude.ai",
        detail="Claude",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:46-07:00")),
    ),
    ChromeSession(
        domain="chatgpt.com",
        detail="ChatGPT",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:51-07:00")),
    ),
]


@pytest.mark.asyncio
# @pytest.mark.skip
async def test_arbiter_to_dao_layer(regular_session_maker, plain_asm):
    output_programs = pr_events_v2  # Values from the end of the previous tests
    output_domains = ch_events_v2  # Values from the end of the previous tests
    assert len(output_programs) == 4
    assert len(output_domains) == 4

    times_for_window_push = [x.start_time for x in output_programs] + [
        x.start_time for x in output_domains
    ]

    # don't calculate the changes by hand, it'll waste your time. make the computer do it.
    # durations_between_events = [5, 8, 4, 2, 7, 7, 8]

    assert output_domains[-1].start_time is not None, "Setup condition not met"

    final_time = output_domains[-1].start_time + timedelta(seconds=8)

    times_for_window_push.append(final_time)  # used for what?

    def sort_sessions_chronologically(program_sessions, chrome_sessions):
        all = program_sessions + chrome_sessions
        chronological_sessions = sorted(all, key=lambda event: event.start_time.dt)
        return chronological_sessions

    whole_session_list = sort_sessions_chronologically(output_domains, output_programs)

    whole_session_list_len = len(whole_session_list)

    # Test setup conditions!

    # type: ignore
    assert all(
        t.day == 22 for t in times_for_window_push
    ), "All days should be 22 like in the above test data"

    # this is just appeasing type checking
    as_dt = [x for x in times_for_window_push if x is not None]

    assert isinstance(as_dt, list) and len(as_dt) > 0
    assert all(isinstance(x, UserLocalTime) for x in as_dt), "Testing setup conditions again"
    clock_again = UserLocalTimeMockClock(as_dt)

    # Test setup conditions

    # program_durations = []
    # tab_durations = []

    def calculate_expected_durations_in_seconds(program_sessions, chrome_sessions):
        total_amt = len(program_sessions) + len(chrome_sessions)
        sorted_by_time = sort_sessions_chronologically(program_sessions, chrome_sessions)
        durations = []

        time_tally_in_sec = {"programs": [], "domains": []}
        print("\n\n")
        for i in range(0, total_amt):
            if i == total_amt - 1:
                break
            change = sorted_by_time[i + 1].start_time.dt - sorted_by_time[i].start_time.dt
            seconds = change.total_seconds()
            if isinstance(sorted_by_time[i], ProgramSession):
                tally_key = sorted_by_time[i].exe_path
                time_tally_in_sec["programs"].append(seconds)
            else:
                time_tally_in_sec["domains"].append(seconds)
                tally_key = sorted_by_time[i].domain
            if tally_key in time_tally_in_sec:
                time_tally_in_sec[tally_key] += seconds
            else:
                time_tally_in_sec[tally_key] = seconds
            print(f"gap {i}: {seconds}")
            durations.append(seconds)
        return sum(durations), durations, time_tally_in_sec

    session_durations_sum_in_sec, session_durations_in_sec, output_times_tally = (
        calculate_expected_durations_in_seconds(output_programs, output_domains)
    )

    def get_partials_for_add_partial_window(durations_arr):
        """
        As a reminder, if a session is open for the 30th second, the end time will be set to 30 sec.
        The session then stops at the 33 second mark, the recorder must add the partial window, 3 sec,
        to bring the total duration in line with the actual end time.

        The test was changed from deducting a remainder to just adding the partially consumed window.

        This func assumes the durations_arr arrives in the same order the sessions are entered into the Arbiter.
        """
        partials = []
        for x in durations_arr:
            partial = x % 10
            partials.append(partial)
        return partials

    partials_for_mock_recorder = get_partials_for_add_partial_window(
        session_durations_in_sec
    )

    def assert_setup_times_went_well(session_durations):
        """
        These times are needed for the TestActivityRecorder
        and to verify the end of the test has the right duration.
        """

        assert len(session_durations) == len(output_programs) + len(output_domains) - 1

        assert session_durations_sum_in_sec != 0.0

        assert all(isinstance(x, float) for x in session_durations)
        assert all(x >= 0 for x in session_durations)
        assert all(
            x < 10 for x in partials_for_mock_recorder
        ), "A partial window is always below 10 and it wasn't here"

    assert_setup_times_went_well(session_durations_in_sec)

    program_logging_dao = ProgramLoggingDao(regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(regular_session_maker)

    program_logging_push_spy = Mock(
        side_effect=program_logging_dao.push_window_ahead_ten_sec
    )

    program_logging_start_session_spy = Mock(side_effect=program_logging_dao.start_session)

    chrome_logging_push_spy = Mock(side_effect=chrome_logging_dao.push_window_ahead_ten_sec)

    chrome_logging_start_session_spy = Mock(side_effect=chrome_logging_dao.start_session)

    program_logging_dao.start_session = program_logging_start_session_spy
    chrome_logging_dao.start_session = chrome_logging_start_session_spy

    program_logging_dao.push_window_ahead_ten_sec = program_logging_push_spy
    chrome_logging_dao.push_window_ahead_ten_sec = chrome_logging_push_spy

    program_summary_dao = ProgramSummaryDao(program_logging_dao, regular_session_maker)
    chrome_summary_dao = ChromeSummaryDao(chrome_logging_dao, regular_session_maker)

    # Create spies on the DAOs' push window methods
    program_sum_start_session_spy = Mock(side_effect=program_summary_dao.start_session)
    program_summary_dao.start_session = program_sum_start_session_spy

    chrome_sum_start_session_spy = Mock(side_effect=chrome_summary_dao.start_session)
    chrome_summary_dao.start_session = chrome_sum_start_session_spy

    program_summary_push_spy = Mock(
        side_effect=program_summary_dao.push_window_ahead_ten_sec
    )
    program_summary_dao.push_window_ahead_ten_sec = program_summary_push_spy

    chrome_summary_push_spy = Mock(side_effect=chrome_summary_dao.push_window_ahead_ten_sec)
    chrome_summary_dao.push_window_ahead_ten_sec = chrome_summary_push_spy

    # Create spies on DAOs' _create methods
    program_create_spy = Mock(side_effect=program_summary_dao._create)
    program_summary_dao._create = program_create_spy

    chrome_create_spy = Mock(side_effect=chrome_summary_dao._create)
    chrome_summary_dao._create = chrome_create_spy

    # Create spies on the DAOs' add_used_time methods
    program_summary_add_used_time_spy = Mock(side_effect=program_summary_dao.add_used_time)
    program_summary_dao.add_used_time = program_summary_add_used_time_spy

    chrome_summary_add_used_time_spy = Mock(side_effect=chrome_summary_dao.add_used_time)
    chrome_summary_dao.add_used_time = chrome_summary_add_used_time_spy

    # activity_recorder = ActivityRecorder(
    # clock_again, program_logging_dao, chrome_logging_dao,
    # program_summary_dao, chrome_summary_dao)

    class TestActivityRecorder(ActivityRecorder):
        def __init__(self, *args, durations_to_override=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._override_durations = durations_to_override or []
            self._override_index = 0

        def add_partial_window(self, duration_in_sec, session):
            """
            Must give deduct duration answers calculated by hand because
            the actual test will run way faster than the actual elapsed time of the sessions
            so the KeepAliveEngine won't know which values to input.
            """
            if self._override_index < len(self._override_durations):
                duration_in_sec = self._override_durations[self._override_index]
                if isinstance(session, ProgramSession):

                    print(f"getting {duration_in_sec} for {session.process_name}")
                else:
                    print(f"getting {duration_in_sec} for {session.domain}")

                self._override_index += 1
            super().add_partial_window(duration_in_sec, session)

    debug = True

    activity_recorder = TestActivityRecorder(
        program_logging_dao,
        chrome_logging_dao,
        program_summary_dao,
        chrome_summary_dao,
        debug,
        durations_to_override=partials_for_mock_recorder,
    )

    activity_recorder_add_ten_spy = Mock(
        side_effect=activity_recorder.add_ten_sec_to_end_time
    )
    activity_recorder.add_ten_sec_to_end_time = activity_recorder_add_ten_spy

    container = MockEngineContainer([int(x) for x in session_durations_in_sec])

    sys_status_dao = SystemStatusDao(
        cast(UserFacingClock, clock_again), 10, regular_session_maker
    )

    activity_arbiter = ActivityArbiter(clock_again, sys_status_dao, container)

    #
    # # Mocks in order of appearance:
    #

    # Create a spy on the notify_summary_dao method
    notify_summary_dao_spy = Mock(side_effect=activity_arbiter.notify_summary_dao)
    activity_arbiter.notify_summary_dao = notify_summary_dao_spy

    # Spy on the set_program_state method
    spy_on_set_program_state = Mock(side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state
    spy_on_set_tab_state = Mock(side_effect=activity_arbiter.set_tab_state)
    activity_arbiter.set_tab_state = spy_on_set_tab_state

    asm_spy = Mock(side_effect=activity_arbiter.state_machine.set_new_session)
    activity_arbiter.state_machine.set_new_session = asm_spy

    notify_of_new_session_spy = Mock(side_effect=activity_arbiter.notify_of_new_session)
    activity_arbiter.notify_of_new_session = notify_of_new_session_spy

    pr_start_session_spy = Mock(
        side_effect=activity_recorder.program_logging_dao.start_session
    )
    activity_recorder.program_logging_dao.start_session = pr_start_session_spy

    ch_start_session_spy = Mock(
        side_effect=activity_recorder.chrome_logging_dao.start_session
    )
    activity_recorder.chrome_logging_dao.start_session = ch_start_session_spy

    pr_push_window_spy = Mock(
        side_effect=activity_recorder.program_logging_dao.push_window_ahead_ten_sec
    )
    activity_recorder.program_logging_dao.push_window_ahead_ten_sec = pr_push_window_spy

    ch_push_window_spy = Mock(
        side_effect=activity_recorder.chrome_logging_dao.push_window_ahead_ten_sec
    )
    activity_recorder.chrome_logging_dao.push_window_ahead_ten_sec = ch_push_window_spy

    pr_finalize_spy = Mock(side_effect=activity_recorder.program_logging_dao.finalize_log)
    activity_recorder.program_logging_dao.finalize_log = pr_finalize_spy

    ch_finalize_spy = Mock(side_effect=activity_recorder.chrome_logging_dao.finalize_log)
    activity_recorder.chrome_logging_dao.finalize_log = ch_finalize_spy

    # This line MUST be last before Act. Otherwise, the mocks aren't setup
    # properly.
    activity_arbiter.add_recorder_listener(activity_recorder)

    # --
    # -- -- Act (3)
    # --

    # It just so happens that all tab states are after program states
    def run_arbiter_in_order(sorted_session_list):
        """
        You MUST do the acting part using this pattern.

        In the first iteration, the program sessions were the first four, and
        the Chrome sessions were the last four. But that isn't always the case!

        So this function takes the events, that were sorted chronologically, and runs them in turn.

        If you run this with out of order sessions it will not work!
        """
        final_event_type = None
        count = {"programs": 0, "domains": 0}
        for event in sorted_session_list:
            if isinstance(event, ProgramSession):
                count["programs"] += 1
                final_event_type = "Program"
                activity_arbiter.set_program_state(event)
            else:
                count["domains"] += 1
                final_event_type = "Domain"
                activity_arbiter.set_tab_state(event)
        return final_event_type, count

    final_event_type, count = run_arbiter_in_order(whole_session_list)

    print(f"final event type: {final_event_type}")
    print(count)

    # Don't do them by type, because the real program does them chronologically, not by type.
    # for event in output_programs:
    #     activity_arbiter.set_program_state(event)
    # for event in output_domains:
    #     activity_arbiter.set_tab_state(event)

    count_of_programs = len(output_programs)
    count_of_tabs = len(output_domains)
    one_left_in_arbiter = 1
    initialization_entry = 1

    # ### ### Checkpoint:
    # ### [Arbiter layer]
    # ### The Arbiter's outbound funcs were called with the expected values
    assert spy_on_set_program_state.call_count == count_of_programs
    assert spy_on_set_tab_state.call_count == count_of_tabs

    num_of_events_to_enter_arbiter = count_of_programs + count_of_tabs

    assert (
        asm_spy.call_count == num_of_events_to_enter_arbiter
    ), "A session escaped asm.set_new_session"
    assert notify_of_new_session_spy.call_count == num_of_events_to_enter_arbiter

    for call in asm_spy.call_args_list:
        # Get the first positional argument from each call
        session = call.args[0]
        assert session.duration is None
        assert session.end_time is None

    for i in range(0, num_of_events_to_enter_arbiter):
        arg, _ = notify_of_new_session_spy.call_args_list[i]
        session = arg[0]  # Get the first positional argument from each call
        if i in [0, 1, 2, 3]:
            assert isinstance(session, ProgramSession)
        else:
            assert isinstance(session, ChromeSession)

    # ### The Arbiter recorded the expected *number* of times
    assert (
        notify_summary_dao_spy.call_count
        == count_of_programs + count_of_tabs - one_left_in_arbiter
    )
    #  # TODO: The Arbiter recorded the expected total amount of time

    # #
    # ### [Recorder layer]
    # #
    assert program_logging_start_session_spy.call_count == len(
        output_programs
    ), "Expected each session to make it through one time"

    #
    # The DAOs recorded the expected number of times
    #

    add_ten_count = sum([x // 10 for x in session_durations_in_sec])

    assert activity_recorder_add_ten_spy.call_count == add_ten_count

    assert pr_start_session_spy.call_count == count_of_programs
    assert ch_start_session_spy.call_count == count_of_tabs

    assert pr_push_window_spy.call_count == sum(
        [x // 10 for x in output_times_tally["programs"]]
    )
    assert ch_push_window_spy.call_count == sum(
        [x // 10 for x in output_times_tally["domains"]]
    )

    assert pr_finalize_spy.call_count == count_of_programs
    assert ch_finalize_spy.call_count == count_of_tabs - one_left_in_arbiter

    #
    # The DAOs were called in the expected order with the expected args
    #

    a_duplicate = 1

    def assert_start_sessions_were_normal():
        assert program_sum_start_session_spy.call_count == len(output_programs) - a_duplicate
        assert chrome_sum_start_session_spy.call_count == len(output_domains) - a_duplicate
        assert program_logging_start_session_spy.call_count == len(output_programs)
        assert chrome_logging_start_session_spy.call_count == len(output_domains)

    # FIXME: I need a dict for this
    push_tally = {"programs": 0, "domains": 0}

    time_tally_in_sec = {"programs": [], "domains": []}
    for i in range(0, whole_session_list_len):
        if i == whole_session_list_len - 1:
            break
        current = whole_session_list[i]
        change = whole_session_list[i + 1].start_time.dt - current.start_time.dt
        seconds = change.total_seconds()
        if isinstance(current, ProgramSession):
            push_tally["programs"] += seconds // window_push_length
        else:
            push_tally["domains"] += seconds // window_push_length

    def assert_window_push_was_normal():
        # assert program_summary_push_spy.call_count == push_tally["program_sum_count"]
        # assert chrome_summary_push_spy.call_count == push_tally["chrome_sum_count"]
        # assert program_logging_push_spy.call_count == push_tally["program_logging_count"]
        # assert chrome_logging_push_spy.call_count == push_tally["chrome_logging_count"]
        assert program_summary_push_spy.call_count == push_tally["programs"]
        assert chrome_summary_push_spy.call_count == push_tally["domains"]
        assert program_logging_push_spy.call_count == push_tally["programs"]
        assert chrome_logging_push_spy.call_count == push_tally["domains"]

    def assert_add_used_time_worked():
        if final_event_type == "program":
            assert (
                program_summary_add_used_time_spy.call_count
                == len(output_programs) - one_left_in_arbiter
            )
            assert chrome_summary_add_used_time_spy.call_count == len(output_domains)
        else:
            assert program_summary_add_used_time_spy.call_count == len(output_programs)
            assert (
                chrome_summary_add_used_time_spy.call_count
                == len(output_domains) - one_left_in_arbiter
            )

    def assert_finalize_logs_was_normal():
        if final_event_type == "program":
            assert pr_finalize_spy.call_count == len(output_programs) - one_left_in_arbiter
            assert ch_finalize_spy.call_count == len(output_domains)
        else:
            assert pr_finalize_spy.call_count == len(output_programs)
            assert ch_finalize_spy.call_count == len(output_domains) - one_left_in_arbiter

    def assert_dao_layer_went_as_expected():
        # Start session
        assert_start_sessions_were_normal()
        # Window push
        assert_window_push_was_normal()
        # Partials
        assert_add_used_time_worked()
        # On state changed / Finalize logs
        assert_finalize_logs_was_normal()

    assert_dao_layer_went_as_expected()

    def assert_all_start_sessions_were_proper():
        for x in range(0, len(output_programs)):
            assert isinstance(pr_start_session_spy.call_args_list[x][0][0], ProgramSession)

        for x in range(0, len(output_programs)):
            assert isinstance(ch_start_session_spy.call_args_list[x][0][0], ChromeSession)

    assert_all_start_sessions_were_proper()

    # The DAOs recorded the expected amount of time
    # Check the arguments that were passed were as expected
    # NOTE:
    # [0][0][0] -> program_session: ProgramSession,
    # [0][0][1] -> right_now: datetime
    for i in range(len(output_programs)):
        program_session_arg = pr_finalize_spy.call_args_list[i][0][0]
        # right_now_arg = program_summary_push_spy.call_args_list[i][0][1]
        assert isinstance(program_session_arg, ProgramSession)
        # assert isinstance(right_now_arg, datetime)

        # Transformation happens in the ProgramTracker:
        # detail, window = separate_window_name_and_detail(
        #     window_change_dict["window_title"])
        # new_session.window_title = window
        # new_session.detail = detail

        result = separate_window_name_and_detail(output_programs[i].window_title)
        assert program_session_arg.window_title == result[0]
        assert program_session_arg.start_time == output_programs[i].start_time

    # #
    # # Summary DAO tests
    # #

    assert program_sum_start_session_spy.call_count == count_of_programs - a_duplicate
    assert chrome_sum_start_session_spy.call_count == count_of_tabs - a_duplicate

    # Start session

    for i in range(len(output_programs)):
        program_arg = program_logging_start_session_spy.call_args_list[i][0][0]

        assert isinstance(program_arg, ProgramSession)
        assert program_arg.window_title == output_programs[i].window_title

    for i in range(len(ch_events_v2) - one_left_in_arbiter):
        chrome_arg = chrome_logging_start_session_spy.call_args_list[i][0][0]
        # right_now_arg = chrome_summary_push_spy.call_args_list[i][0][1]

        assert isinstance(chrome_arg, ChromeSession)
        # assert isinstance(right_now_arg, datetime)
        assert chrome_arg.domain == ch_events_v2[i].domain

    # Add used duration
    assert program_summary_add_used_time_spy.call_count == count_of_programs
    assert chrome_summary_add_used_time_spy.call_count == count_of_tabs - one_left_in_arbiter

    num_of_unique_programs = 3
    num_of_unique_domains = 3
    # there are 3 unique programs; Chrome is twice.
    assert program_create_spy.call_count == num_of_unique_programs
    # There are 3 unique tabs; ChatGPT is in twice.
    assert chrome_create_spy.call_count == num_of_unique_domains

    for i in range(num_of_unique_programs):
        name_arg = program_create_spy.call_args_list[i][0][0]
        start_time_arg = program_create_spy.call_args_list[i][0][1]

        assert isinstance(name_arg, ProgramSession)
        assert isinstance(start_time_arg, datetime)

    for i in range(num_of_unique_domains):
        name_arg = chrome_create_spy.call_args_list[i][0][0]
        start_time_arg = chrome_create_spy.call_args_list[i][0][1]

        assert isinstance(name_arg, str)
        assert isinstance(start_time_arg, datetime)

    # ###
    # --
    # -- The beginning of the end
    # --
    # ###

    # Prove that all the values are there in the database
    program_summaries = program_summary_dao.read_all()
    chrome_summaries = chrome_summary_dao.read_all()
    program_logs = program_logging_dao.read_all()
    chrome_logs = chrome_logging_dao.read_all()

    for x in program_summaries:
        print("program summary:", x)
    for x in chrome_summaries:
        print("chrome summary:", x)

    pst_tz = pytz.timezone("America/Los_Angeles")

    expected_date = pst_tz.localize(datetime(2025, 3, 22, 0, 0, 0))
    expected_date = convert_to_utc(expected_date)

    # FIXME: "Hours: 0.00" for all summaries

    logger = ConsoleLogger()

    def assert_all_rows_existed():
        assert len(program_summaries) != 0, "read all was 0 for program summary"
        assert len(chrome_summaries) != 0, "read all was 0 chrome summary"
        assert len(program_logs) != 0, "read all was 0 for program logs"
        assert len(chrome_logs) != 0, "read all was 0 for chrome logs"

    assert_all_rows_existed()

    p_sums_seconds = []
    ch_sums_seconds = []

    logger.log_blue("Program summaries loop:")
    for b in program_summaries:
        logger.log_blue(b)
        p_sums_seconds.append(b.hours_spent * SECONDS_PER_HOUR)

    logger.log_blue("Chrome summaries loop:")
    for g in chrome_summaries:
        logger.log_blue(g)
        ch_sums_seconds.append(g.hours_spent * SECONDS_PER_HOUR)

    # These values COULD just be very very small, like 0.00000003, so cut off
    # by truncation
    assert all(
        [x.hours_spent > 0 for x in program_summaries]
    ), "Some value for entries we just added was zero"
    assert all(
        [x.hours_spent > 0 for x in chrome_summaries]
    ), "Some value for entries we just added was zero"

    half_sec = 0.5
    assert all([x > half_sec for x in p_sums_seconds])
    assert all([x > half_sec for x in ch_sums_seconds])

    assert len(program_summaries) == 3
    assert all(
        x.hours_spent > 0 for x in program_summaries
    ), "A summary was started but no time was recorded?"
    assert len(chrome_summaries) == 3
    assert all(
        x.hours_spent > 0 for x in chrome_summaries
    ), "A summary was started but no time was recorded?"

    def assert_all_rows_have_correct_gathering_date():
        assert all(
            item.gathering_date == expected_date for item in program_summaries
        ), "Program summaries have incorrect gathering date"

        assert all(
            item.gathering_date == expected_date for item in chrome_summaries
        ), "Chrome summaries have incorrect gathering date"
        assert all(
            item.gathering_date == expected_date for item in program_logs
        ), "Program logs have incorrect gathering date"
        assert all(
            item.gathering_date == expected_date for item in chrome_logs
        ), "Chrome logs have incorrect gathering date"

    assert_all_rows_have_correct_gathering_date()

    # --
    # -- Go by program and domain:
    # --

    # -- logs and ledgers
    def assert_expected_values_match_ledger(test_data, expected_durations):
        """Verify each one using it's ledger."""
        for i in range(0, len(test_data)):
            ledger_total = test_data[i].ledger.get_total()
            print(ledger_total, "ledger total")
        for i in range(0, len(test_data)):
            # check that the ledger says what you expect
            if i == len(test_data) - 1:
                # Claude, final session
                assert test_data[i].ledger.get_total() == 0
                break
            ledger_total = test_data[i].ledger.get_total()
            assert ledger_total == expected_durations[i]
        print("Ledgers matched expected values")

    assert_expected_values_match_ledger(whole_session_list, session_durations_in_sec)

    def assert_actual_logs_match_expected_durations(
        verified_sessions, actual_durations_from_logs
    ):
        for i in range(0, len(verified_sessions)):
            current = verified_sessions[i]
            assert current.ledger.get_total() == actual_durations_from_logs[i]
        print("Ledgers matched actual durations from logs")

    logs_in_order = sorted(program_logs + chrome_logs, key=lambda obj: obj.start_time_local)

    log_durations_in_order = [log.duration_in_sec for log in logs_in_order]

    assert_actual_logs_match_expected_durations(whole_session_list, log_durations_in_order)

    # -- end logs and ledgers

    def get_unique_programs_with_times(program_summaries):
        tally_dict = {}
        for program in program_summaries:
            if program.exe_path_as_id in tally_dict:
                tally_dict[program.exe_path_as_id] += program.hours_spent
            else:
                tally_dict[program.exe_path_as_id] = program.hours_spent
        return tally_dict

    def get_unique_domains_with_times(chrome_summaries):
        tally_dict = {}
        for domain in chrome_summaries:
            if domain.domain_name in tally_dict:
                tally_dict[domain.domain_name] += domain.hours_spent
            else:
                tally_dict[domain.domain_name] = domain.hours_spent
        return tally_dict

    program_tally = get_unique_programs_with_times(program_summaries)
    chrome_tally = get_unique_domains_with_times(chrome_summaries)

    def pair_summary_with_logs(summaries, logs):
        pairs = []
        for summary in summaries:
            target_name = summary.get_name()
            related_logs = [x for x in logs if x.get_name() == target_name]
            print(target_name, "related logs: ", related_logs[0])
            pairs.append((summary, related_logs))
        return pairs

    def audit_logs_vs_summaries(summaries, logs):

        pairs = pair_summary_with_logs(summaries, logs)
        comparisons = []
        for pair in pairs:
            name = pair[0].get_name()
            logs_total = sum([x.duration_in_sec for x in pair[1]])
            summary_total_in_hours = pair[0].hours_spent
            summary_total = summary_total_in_hours * SECONDS_PER_HOUR
            comparisons.append((name, summary_total, logs_total))
        for v in comparisons:
            print(v)
        tolerance = 0.002  # 0.2% tolerance
        for v in comparisons:
            # FIXME: ('Xorg', 8.136912, 8.136912)
            # FIXME: ('Code.exe', 4.106647000000001, 14.106647)  # Off by 10 - 10 too much
            # FIXME: ('Chrome.exe', 80.555042, 70.555042)  # Off by 10  - 10 too little
            # FIXME: ('docs.google.com', 8.0, 8.0)
            print(f"name: {v[0]}")
            summary_value = v[1]
            logs_value = v[2]
            # Check if values are close enough
            difference = abs(summary_value - logs_value)
            max_value = max(abs(summary_value), abs(logs_value))
            relative_diff = difference / max_value if max_value > 0 else 0

            print(
                f"Summary: {summary_value}, Logs: {logs_value}, Relative diff: {relative_diff:.6f}"
            )
            assert (
                relative_diff <= tolerance
            ), f"Values differ by more than {tolerance*100}%: {summary_value} vs {logs_value}"

    audit_logs_vs_summaries(program_summaries + chrome_summaries, program_logs + chrome_logs)

    program_keys = program_tally.keys()
    chrome_keys = chrome_tally.keys()

    for key, dao_tally in program_tally.items():
        converted = output_times_tally[key] / SECONDS_PER_HOUR  # type: ignore
        assert converted == dao_tally
    for key, dao_tally in chrome_tally.items():
        converted = output_times_tally[key] / SECONDS_PER_HOUR  # type: ignore
        assert converted == dao_tally

    # for key, tally in inputs_with_sums.items():
    #     assert key in program_keys or key in chrome_keys
    #     assert

    # Check that the DAO's tally matches the hand made one at the top of the file

    def assert_all_programs_had_expected_times():
        """Verify that"""
        pass

    # ### ### Checkpoint:
    # # Dashboard Service reports the right amount of time for get_weekly_productivity_overview
    timeline_dao = TimelineEntryDao(plain_asm)
    dashboard_service = DashboardService(
        timeline_dao,
        program_summary_dao,
        program_logging_dao,
        chrome_summary_dao,
        chrome_logging_dao,
    )

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

    # # Events are from 03-22, a Saturday.
    # # So we need 03-16, the prior Sunday.
    the_16th_with_tz = some_local_tz.localize(datetime(2025, 3, 16))

    time_for_week = await dashboard_service.get_weekly_productivity_overview(
        the_16th_with_tz
    )

    assert any(
        entry["productivity"] > 0 and entry["leisure"] > 0 for entry in time_for_week
    ), "Dashboard Service should've retrieved the times created earlier, but it didn't"

    def get_day_seen_in_test_data(days_of_productivity):
        program_day = output_programs[0].start_time
        chrome_day = output_domains[0].start_time

        assert program_day.dt.day == chrome_day.dt.day
        assert program_day.dt.month == chrome_day.dt.month

        for day in days_of_productivity:
            same_day = program_day.dt.day == day["day"].day
            same_month = program_day.dt.month == day["day"].month
            if same_day and same_month:
                return day
        pytest.fail("No valid day found from dashboard svc data")

    day_with_data = get_day_seen_in_test_data(time_for_week)

    production = day_with_data["productivity"]
    leisure = day_with_data["leisure"]

    assert isinstance(production, float)
    assert isinstance(leisure, float)
    assert production > 0.0
    assert leisure > 0.0

    dashboard_svc_total = production + leisure

    def assert_summary_db_falls_within_tolerance(
        dashboard_svc_total, expected_durations_sum
    ):
        tolerance = 0.02  # 5%
        lower_threshold = expected_durations_sum * (1 - tolerance)
        upper_bounds = expected_durations_sum * (1 + tolerance)

        assert (
            lower_threshold < dashboard_svc_total < upper_bounds
        ), "Test input duration sum didn't match dashboard service"

    assert dashboard_svc_total != 0.0
    calculated_up_top = session_durations_sum_in_sec / SECONDS_PER_HOUR

    assert_summary_db_falls_within_tolerance(production + leisure, calculated_up_top)
    # assert dashboard_svc_total == calculated_up_top, "By hand tally didn't exactly match dashboard service"
    # 3600 is 60 * 60
