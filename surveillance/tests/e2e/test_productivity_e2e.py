import pytest
import pytest_asyncio
from unittest.mock import Mock
import traceback
import asyncio

import pytz
from datetime import datetime, timedelta

from typing import cast


from surveillance.src.config.definitions import imported_local_tz_str

from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.surveillance_manager import FacadeInjector, SurveillanceManager

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.timeline_entry_dao import TimelineEntryDao

from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.facade.facade_singletons import (
    get_keyboard_facade_instance,
    get_mouse_facade_instance,
)

from surveillance.src.services.tiny_services import TimezoneService

from surveillance.src.services.dashboard_service import DashboardService
from surveillance.src.services.chrome_service import ChromeService

from surveillance.src.object.classes import (
    ChromeSession,
    ProgramSession,
    TabChangeEventWithLtz,
)
from surveillance.src.util.program_tools import separate_window_name_and_detail
from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.time_wrappers import UserLocalTime

from surveillance.src.util.time_formatting import convert_to_utc

from ..mocks.mock_clock import UserLocalTimeMockClock, MockClock
from ..mocks.mock_message_receiver import MockMessageReceiver
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


some_local_tz = pytz.timezone(imported_local_tz_str)


@pytest.fixture
def times_from_test_data():
    program_times = [datetime.fromisoformat(d["time"]) for d in program_data]
    chrome_times = [d.startTime for d in chrome_data]
    return program_times, chrome_times


async def cleanup_test_resources(manager):
    print("Cleaning up test resources...")

    # Clean up surveillance manager (this should now properly clean up
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
async def test_setup_conditions(regular_session, plain_asm):
    program_logging = ProgramLoggingDao(regular_session)
    chrome_logging = ChromeLoggingDao(regular_session)
    program_summaries_dao = ProgramSummaryDao(
        program_logging, regular_session, plain_asm
    )
    chrome_summaries_dao = ChromeSummaryDao(chrome_logging, regular_session, plain_asm)

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


@pytest.mark.asyncio
@pytest.mark.skip
async def test_tracker_to_arbiter(plain_asm, regular_session, times_from_test_data):

    real_program_events = [x["event"] for x in program_data]
    real_chrome_events = chrome_data

    times_for_program_events = [x["time"] for x in program_data]

    mock_clock_times = []

    for i in range(0, len(times_for_program_events)):
        # TODO: The if block looks useless, delete
        if i == len(times_for_program_events) - 1:
            current = datetime.fromisoformat(times_for_program_events[i])
            mock_clock_times.append(current)
            break
        current = datetime.fromisoformat(times_for_program_events[i])
        mock_clock_times.append(current)

    mock_clock = MockClock(mock_clock_times)

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
    spy_on_listen_for_window = Mock(
        side_effect=program_facade.listen_for_window_changes
    )
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

    activity_arbiter = ActivityArbiter(mock_user_facing_clock, pulse_interval=1)
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
        regular_session,
        chrome_svc,
        activity_arbiter,
        facades,
        mock_message_receiver,
    )

    window_change_spy = Mock(
        side_effect=surveillance_manager.program_tracker.window_change_handler
    )
    surveillance_manager.program_tracker.window_change_handler = window_change_spy

    surveillance_manager.start_trackers()

    async def wait_for_events_to_process():
        # Wait for events to be processed
        print("\n++\n++\nWaiting for events to be processed...")
        # Give the events time to propagate through the system
        # Try for up to 10 iterations
        for _ in range(len(real_chrome_events) + len(real_program_events)):
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
            program_facade.yield_count == 4
        ), "Facade yielded more or less events than intended"

        assert (
            window_change_spy.call_count == 4
        ), "Window change wasn't called once per new program"

        for i in range(0, 4):
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
@pytest.mark.skip
# @pytest.mark.skip("working on below test")
async def test_chrome_svc_to_arbiter_path(regular_session, plain_asm):
    chrome_events_for_test = chrome_data

    # chrome_dao = ChromeDao(plain_asm)

    # # Spy
    # chrome_dao_create_spy = Mock(side_effect=chrome_dao.create)
    # chrome_dao.create = chrome_dao_create_spy

    t1 = datetime.now()
    irrelevant_clock = MockClock([t1, t1, t1, t1, t1, t1, t1, t1, t1])

    activity_arbiter = ActivityArbiter(irrelevant_clock, pulse_interval=1)

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


imaginary_path_to_chrome = "imaginary/path/to/Chrome.exe"
imaginary_chrome_processe = "Chrome.exe"

pr_events_v2 = [
    ProgramSession(
        exe_path=imaginary_path_to_chrome,
        process_name=imaginary_chrome_processe,
        window_title="Google Chrome",
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
        window_title="Google Chrome",
        detail="Google",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:16:17.480951-07:00")),
    ),
]

ch_events_v2 = [
    ChromeSession(
        domain="docs.google.com",
        detail="Google Docs",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:15:02-07:00")),
    ),
    ChromeSession(
        domain="chatgpt.com",
        detail="ChatGPT",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:15:10-07:00")),
    ),
    ChromeSession(
        domain="claude.ai",
        detail="Claude",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:15:21-07:00")),
    ),
    ChromeSession(
        domain="chatgpt.com",
        detail="ChatGPT",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:15:30-07:00")),
    ),
]


@pytest.mark.asyncio
# @pytest.mark.skip
async def test_arbiter_to_dao_layer(regular_session, plain_asm):
    output_programs = pr_events_v2  # Values from the end of the previous tests
    output_domains = ch_events_v2  # Values from the end of the previous tests

    times_for_window_push = [x.start_time for x in pr_events_v2] + [
        x.start_time for x in ch_events_v2
    ]

    # see start_time_2 - start_time_1 in above events. The ints are durations
    # from start_times
    durations_between_events = [5, 8, 4, 2, 7, 7, 8]

    assert output_domains[-1].start_time is not None, "Setup condition not met"

    final_time = output_domains[-1].start_time + timedelta(seconds=8)

    times_for_window_push.append(final_time)  # used for what?

    # Test setup conditions!

    # type: ignore
    assert all(
        t.day == 22 for t in times_for_window_push
    ), "All days should be 22 like in the above test data"

    # this is just appeasing type checking
    as_dt = [x for x in times_for_window_push if x is not None]

    assert isinstance(as_dt, list) and len(as_dt) > 0
    assert all(
        isinstance(x, UserLocalTime) for x in as_dt
    ), "Testing setup conditions again"
    clock_again = UserLocalTimeMockClock(as_dt)

    # FIXME: NEed to have sessions be written with THE TIME in THE EVENT, not
    # 04-11 (today)

    # Test setup conditions

    program_durations = []
    tab_durations = []

    def calculate_expected_durations(program_sessions, chrome_sessions):
        pass

    for i in range(0, len(output_programs)):
        change = output_programs[i].duration
        if change is None:
            continue  # Do not add the final value: That event didn't "close" yet
        program_durations.append(change)

    for i in range(0, len(output_domains)):
        change = output_domains[i].duration
        if change is None:
            continue  # Do not add the final value: That event didn't "close" yet
        tab_durations.append(change)

    sum_of_program_times = sum(program_durations, timedelta(seconds=0))
    sum_of_tab_times = sum(tab_durations, timedelta(seconds=0))

    assert sum_of_program_times.total_seconds() != 0, "Setup conditions not met"
    assert sum_of_tab_times.total_seconds() != 0, "Setup conditions not met"

    program_logging_dao = ProgramLoggingDao(regular_session)
    chrome_logging_dao = ChromeLoggingDao(regular_session)

    program_push_spy = Mock(side_effect=program_logging_dao.push_window_ahead_ten_sec)
    program_start_session_spy = Mock(side_effect=program_logging_dao.start_session)
    chrome_push_spy = Mock(side_effect=chrome_logging_dao.push_window_ahead_ten_sec)
    chrome_start_session_spy = Mock(side_effect=chrome_logging_dao.start_session)

    program_logging_dao.push_window_ahead_ten_sec = program_push_spy
    program_logging_dao.start_session = program_start_session_spy
    chrome_logging_dao.push_window_ahead_ten_sec = chrome_push_spy
    chrome_logging_dao.start_session = chrome_start_session_spy

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session, plain_asm
    )
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session, plain_asm
    )

    #
    #
    # test setup conditions
    #
    p_logs = program_logging_dao.read_all()
    ch_logs = chrome_logging_dao.read_all()
    pro_sum = program_summary_dao.read_all()
    chrome_summaries = chrome_summary_dao.read_all()

    assert len(p_logs) == 0, "An important table was not empty"
    assert len(ch_logs) == 0, "An important table was not empty"
    assert len(pro_sum) == 0, "An important table was not empty"
    assert len(chrome_summaries) == 0, "An important table was not empty"

    # Create spies on the DAOs' push window methods
    program_summary_push_spy = Mock(
        side_effect=program_summary_dao.push_window_ahead_ten_sec
    )
    program_summary_dao.push_window_ahead_ten_sec = program_summary_push_spy

    chrome_summary_push_spy = Mock(
        side_effect=chrome_summary_dao.push_window_ahead_ten_sec
    )
    chrome_summary_dao.push_window_ahead_ten_sec = chrome_summary_push_spy

    # Create spies on DAOs' _create methods
    program_create_spy = Mock(side_effect=program_summary_dao._create)
    program_summary_dao._create = program_create_spy

    chrome_create_spy = Mock(side_effect=chrome_summary_dao._create)
    chrome_summary_dao._create = chrome_create_spy

    # Create spies on the DAOs' deduct_remaining_duration methods
    program_summary_deduct_spy = Mock(
        side_effect=program_summary_dao.deduct_remaining_duration
    )
    program_summary_dao.deduct_remaining_duration = program_summary_deduct_spy

    chrome_summary_deduct_spy = Mock(
        side_effect=chrome_summary_dao.deduct_remaining_duration
    )
    chrome_summary_dao.deduct_remaining_duration = chrome_summary_deduct_spy

    # activity_recorder = ActivityRecorder(
    # clock_again, program_logging_dao, chrome_logging_dao,
    # program_summary_dao, chrome_summary_dao)

    class TestActivityRecorder(ActivityRecorder):
        def __init__(self, *args, durations_to_override=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._override_durations = durations_to_override or []
            self._override_index = 0

        def deduct_duration(self, duration_in_sec, session):
            """Why is this here?"""
            if self._override_index < len(self._override_durations):
                duration_in_sec = self._override_durations[self._override_index]
                self._override_index += 1
            super().deduct_duration(duration_in_sec, session)

    activity_recorder = TestActivityRecorder(
        clock_again,
        program_logging_dao,
        chrome_logging_dao,
        program_summary_dao,
        chrome_summary_dao,
        durations_to_override=durations_between_events,
    )

    activity_recorder_add_ten_spy = Mock(
        side_effect=activity_recorder.add_ten_sec_to_end_time
    )
    activity_recorder.add_ten_sec_to_end_time = activity_recorder_add_ten_spy

    activity_arbiter = ActivityArbiter(clock_again, pulse_interval=0.5)

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

    pr_finalize_spy = Mock(
        side_effect=activity_recorder.program_logging_dao.finalize_log
    )
    activity_recorder.program_logging_dao.finalize_log = pr_finalize_spy

    ch_finalize_spy = Mock(
        side_effect=activity_recorder.chrome_logging_dao.finalize_log
    )
    activity_recorder.chrome_logging_dao.finalize_log = ch_finalize_spy

    # This line MUST be last before Act. Otherwise, the mocks aren't setup
    # properly.
    activity_arbiter.add_recorder_listener(activity_recorder)

    # ###
    # ### ### Act
    # ### ##

    # It just so happens that all tab states are after program states
    for event in output_programs:
        activity_arbiter.set_program_state(event)
    for event in output_domains:
        activity_arbiter.set_tab_state(event)

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

    assert spy_on_set_program_state.call_count == count_of_programs

    # ### The Arbiter recorded the expected *number* of times
    assert (
        notify_summary_dao_spy.call_count
        == count_of_programs + count_of_tabs - one_left_in_arbiter
    )
    #  # TODO: The Arbiter recorded the expected total amount of time

    # #
    # ### [Recorder layer]
    # #
    assert program_start_session_spy.call_count == len(
        output_programs
    ), "Expected each session to make it through one time"

    #
    # The DAOs recorded the expected number of times
    #

    # because the sessions change too fast for the pulse
    assert activity_recorder_add_ten_spy.call_count == 0

    assert pr_start_session_spy.call_count == count_of_programs
    assert ch_start_session_spy.call_count == count_of_tabs

    # because the sessions change too fast for the pulse
    assert pr_push_window_spy.call_count == 0
    # because the sessions change too fast for the pulse
    assert ch_push_window_spy.call_count == 0

    assert pr_finalize_spy.call_count == count_of_programs
    assert ch_finalize_spy.call_count == count_of_tabs - one_left_in_arbiter

    #
    # The DAOs were called in the expected order with the expected args
    #

    # This next section is obtusely plain on purpose.
    assert isinstance(pr_start_session_spy.call_args_list[0][0][0], ProgramSession)
    assert isinstance(pr_start_session_spy.call_args_list[1][0][0], ProgramSession)
    assert isinstance(pr_start_session_spy.call_args_list[2][0][0], ProgramSession)
    assert isinstance(pr_start_session_spy.call_args_list[3][0][0], ProgramSession)
    assert isinstance(ch_start_session_spy.call_args_list[0][0][0], ChromeSession)
    assert isinstance(ch_start_session_spy.call_args_list[1][0][0], ChromeSession)
    assert isinstance(ch_start_session_spy.call_args_list[2][0][0], ChromeSession)
    assert isinstance(ch_start_session_spy.call_args_list[3][0][0], ChromeSession)

    # The DAOs recorded the expected amount of time
    # Check the arguments that were passed were as expected
    # NOTE:
    # [0][0][0] -> program_session: ProgramSession,
    # [0][0][1] -> right_now: datetime
    print(program_summary_push_spy.call_args_list)
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

    assert program_start_session_spy.call_count == count_of_programs
    assert chrome_start_session_spy.call_count == count_of_tabs

    # Start session

    for i in range(len(pr_events_v2)):
        program_arg = program_start_session_spy.call_args_list[i][0][0]

        assert isinstance(program_arg, ProgramSession)
        assert program_arg.window_title == pr_events_v2[i].window_title

    for i in range(len(ch_events_v2) - one_left_in_arbiter):
        chrome_arg = chrome_start_session_spy.call_args_list[i][0][0]
        # right_now_arg = chrome_summary_push_spy.call_args_list[i][0][1]

        assert isinstance(chrome_arg, ChromeSession)
        # assert isinstance(right_now_arg, datetime)
        assert chrome_arg.domain == ch_events_v2[i].domain

    # Deduct remaining duration
    assert program_summary_deduct_spy.call_count == count_of_programs
    assert chrome_summary_deduct_spy.call_count == count_of_tabs - one_left_in_arbiter

    for i in range(len(pr_events_v2)):
        date_of_deduction = program_summary_deduct_spy.call_args_list[i][0][2]

        assert isinstance(date_of_deduction, UserLocalTime)
        assert pr_events_v2[0].start_time is not None
        assert date_of_deduction.day == pr_events_v2[0].start_time.day

    for i in range(len(ch_events_v2) - one_left_in_arbiter):
        date_of_deduction = chrome_summary_deduct_spy.call_args_list[i][0][2]

        assert isinstance(date_of_deduction, UserLocalTime)
        assert ch_events_v2[0].start_time is not None
        assert date_of_deduction.day == ch_events_v2[0].start_time.day

    num_of_unique_programs = 3
    num_of_unique_domains = 3
    # there are 3 unique programs; Chrome is twice.
    assert program_create_spy.call_count == num_of_unique_programs
    # There are 3 unique tabs; ChatGPT is in twice.
    assert chrome_create_spy.call_count == num_of_unique_domains

    # Assert that _create was called with SOME DURATION greater than zero for
    # duration
    for i in range(num_of_unique_programs):
        name_arg = program_create_spy.call_args_list[i][0][0]
        duration_arg = program_create_spy.call_args_list[i][0][1]

        assert isinstance(name_arg, ProgramSession)
        assert duration_arg > 0, "The duration of the usage should be greater than zero"

    # _create

    # TODO: Assert that _create was called with SOME DURATION greater than
    # zero for duration
    for i in range(num_of_unique_domains):
        name_arg = chrome_create_spy.call_args_list[i][0][0]
        duration_arg = chrome_create_spy.call_args_list[i][0][1]

        assert isinstance(name_arg, str)
        assert duration_arg > 0, "The duration of the usage should be greater than zero"

    # ###
    # #
    # # The beginning of the end
    # #
    # ###

    # Prove that all the values are there in the database
    program_summaries = program_summary_dao.read_all()
    chrome_summaries = chrome_summary_dao.read_all()
    program_logs = program_logging_dao.read_all()
    chrome_logs = chrome_logging_dao.read_all()

    expected_date = datetime(2025, 3, 22, 0, 0, 0)
    expected_date = convert_to_utc(expected_date)

    # FIXME: "Hours: 0.00" for all summaries

    logger = ConsoleLogger()
    assert len(program_summaries) != 0, "read all was 0 for program summary"
    assert len(chrome_summaries) != 0, "read all was 0 chrome summary"
    assert len(program_logs) != 0, "read all was 0 for program logs"
    assert len(chrome_logs) != 0, "read all was 0 for chrome logs"

    p_sums_seconds = []
    ch_sums_seconds = []

    for b in program_summaries:
        logger.log_blue_multiple(b, "964")
        p_sums_seconds.append(b.hours_spent * 3600)

    for g in chrome_summaries:
        logger.log_blue_multiple(g, "969")
        ch_sums_seconds.append(g.hours_spent * 3600)

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
    print(the_16th_with_tz, "1023ru")
    sunday_the_16th = UserLocalTime(the_16th_with_tz)

    time_for_week = await dashboard_service.get_weekly_productivity_overview(
        sunday_the_16th
    )

    assert any(
        entry["productivity"] > 0 or entry["leisure"] > 0 for entry in time_for_week
    ), "Dashboard Service should've retrieved the times created earlier, but it didn't"

    def get_day_seen_in_test_data(days_of_productivity):
        program_day = pr_events_v2[0].start_time
        chrome_day = ch_events_v2[0].start_time

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

    # FIXME: I think the test is just broken, like i think it was comparing
    # 0.0 == 0.0 before and i didn't know
    assert dashboard_svc_total != 0.0
    manual_tally_from_start_of_test = (
        sum_of_program_times.seconds + sum_of_tab_times.seconds
    ) / SECONDS_PER_HOUR
    assert manual_tally_from_start_of_test != 0.0
    assert (
        dashboard_svc_total == manual_tally_from_start_of_test
    ), "By hand tally didn't exactly match dashboard service"
    # 3600 is 60 * 60


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
