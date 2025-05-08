# test_program_session_path.py
"""
Proves that the ProgramSession and all relevant fields get where they're intended to go.

Using three sessions to notice edge cases and prove a chain is established.
"""

import pytest
from unittest.mock import Mock

import asyncio

import pytz
from datetime import datetime, timedelta

from typing import Dict, List, cast

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.arbiter.session_polling import KeepAliveEngine
from activitytracker.config.definitions import window_push_length
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.models import DailyProgramSummary, ProgramSummaryLog
from activitytracker.facade.facade_singletons import (
    get_keyboard_facade_instance,
    get_mouse_facade_instance,
)
from activitytracker.object.classes import ProgramSession, ProgramSessionDict
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.const import SECONDS_PER_HOUR, ten_sec_as_pct_of_hour
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.program_session_path import (
    session1,
    session2,
    session3,
    session4,
    test_events,
)
from ..helper.deepcopy_test_data import deepcopy_test_data
from ..helper.testing_util import convert_back_to_dict
from ..mocks.mock_clock import UserLocalTimeMockClock
from ..mocks.mock_engine_container import MockEngineContainer
from ..mocks.mock_message_receiver import MockMessageReceiver

timezone_for_test = "Europe/Berlin"  # UTC +1 or UTC +2

some_local_tz = pytz.timezone(timezone_for_test)


def fmt_time_string(s):
    return datetime.fromisoformat(s)


made_up_pids = [2345, 3456, 4567, 5678]


@pytest.mark.asyncio
async def test_tracker_to_db_path_with_existing_sessions(
    validate_test_data_and_get_durations, regular_session_maker, mock_async_session_maker
):
    """
    The goal of the test is to prove that programSesssions get thru the DAO layer fine

    Here, "preexisting session" means "a value that, in
    pretend, already existed in the db when the test started."

    Intent is to not worry about start and end times too much. Focus is the str vals.
    """

    test_data_clone, durations_for_keep_alive = validate_test_data_and_get_durations

    class MockProgramFacade:
        def __init__(self):
            self.yield_count = 0  # Initialize the counter
            self.MAX_EVENTS = len(test_data_clone)
            self.test_program_dicts = [
                convert_back_to_dict(x, made_up_pids[i]) for i, x in enumerate(test_data_clone)
            ]

        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for program_event in self.test_program_dicts:
                self.yield_count += 1
                # print(f"[yield] Yielding event: {program_event['window_title']} for count {self.yield_count}")
                yield program_event  # Always yield the event first

                # Check if we've reached our limit AFTER yielding
                if self.yield_count >= self.MAX_EVENTS:
                    print(
                        f"\n\nReached max events limit ({self.MAX_EVENTS}), stopping generator\n\n"
                    )
                    # stop more events from occurring
                    surveillance_manager.program_thread.stop_event.set()
                    break

    mock_program_facade = MockProgramFacade()

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(side_effect=mock_program_facade.listen_for_window_changes)
    mock_program_facade.listen_for_window_changes = spy_on_listen_for_window

    def choose_program_facade(current_os):
        return mock_program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade
    )

    """
    Count of occurrences of the clock being used:
    1. ProgramTrackerCore - 1x per session
    2. ActivityRecorder.on_new_session - 1x per session
    3. ActivityRecorder.add_ten_sec_to_end_time - whenever it's called
    """
    # fmt: off
    times = [session1.start_time,  
             session2.start_time, 
             session3.start_time, 
             session4.start_time, session4.start_time, session4.start_time, session4.start_time
             ]
    # fmt: on

    mock_user_facing_clock = UserLocalTimeMockClock(times)

    engine_type = KeepAliveEngine

    short_pulse_interval = 0.1

    mock_container = MockEngineContainer(durations_for_keep_alive, short_pulse_interval)

    activity_arbiter = ActivityArbiter(mock_user_facing_clock, mock_container, engine_type)

    asm_set_new_session_spy = Mock(side_effect=activity_arbiter.state_machine.set_new_session)
    activity_arbiter.state_machine.set_new_session = asm_set_new_session_spy

    p_logging_dao = ProgramLoggingDao(regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(regular_session_maker)

    p_summary_dao = ProgramSummaryDao(p_logging_dao, regular_session_maker)
    chrome_sum_dao = ChromeSummaryDao(chrome_logging_dao, regular_session_maker)

    mock_message_receiver = MockMessageReceiver()

    mock_chrome_svc = Mock()
    shutdown_mock = Mock()
    mock_chrome_svc.shutdown = shutdown_mock

    surveillance_manager = SurveillanceManager(
        cast(UserFacingClock, mock_user_facing_clock),
        mock_async_session_maker,
        regular_session_maker,
        mock_chrome_svc,
        activity_arbiter,
        facades,
        mock_message_receiver,
    )

    start_new_session_spy = Mock(
        side_effect=surveillance_manager.program_tracker.start_new_session
    )
    surveillance_manager.program_tracker.start_new_session = start_new_session_spy

    window_change_spy = Mock(
        side_effect=surveillance_manager.program_tracker.window_change_handler
    )
    surveillance_manager.program_tracker.window_change_handler = window_change_spy

    activity_recorder = ActivityRecorder(
        p_logging_dao, chrome_logging_dao, p_summary_dao, chrome_sum_dao, True
    )

    #
    # # Activity Recorder spies
    #

    on_new_session_spy = Mock(side_effect=activity_recorder.on_new_session)
    activity_recorder.on_new_session = on_new_session_spy

    add_ten_sec_to_end_time_spy = Mock(side_effect=activity_recorder.add_ten_sec_to_end_time)
    activity_recorder.add_ten_sec_to_end_time = add_ten_sec_to_end_time_spy

    on_state_changed_spy = Mock(side_effect=activity_recorder.on_state_changed)
    activity_recorder.on_state_changed = on_state_changed_spy

    add_partial_window_spy = Mock(side_effect=activity_recorder.add_partial_window)
    activity_recorder.add_partial_window = add_partial_window_spy

    activity_arbiter.add_recorder_listener(activity_recorder)

    # ### Arrange
    starting_hours_spent_in_db = 1.0

    def make_preexisting_summary(session, id_for_session):
        """foosssdfdfdsdsdfsdfds"""
        return DailyProgramSummary(
            id=id_for_session,
            exe_path_as_id=session.exe_path,
            program_name=session.window_title,
            hours_spent=starting_hours_spent_in_db,
            gathering_date=get_start_of_day_from_datetime(session.start_time),
            gathering_date_local=get_start_of_day_from_datetime(session.start_time).replace(
                tzinfo=None
            ),
        )

    def group_of_preexisting_summaries():
        yield make_preexisting_summary(session1, made_up_pids[0])
        yield make_preexisting_summary(session2, made_up_pids[1])
        yield make_preexisting_summary(session3, made_up_pids[2])
        yield make_preexisting_summary(session4, made_up_pids[3])
        # return [s1,s2,s3,s4]

    def make_preexisting_log(session, id_for_log):
        sixty_sec = 60
        # Note that the test data is from  "2025-03-22 16:16:17.480951-07:00" ish. 03-22.
        very_early_morning = datetime(2025, 3, 22, 5, 35, 50)
        return ProgramSummaryLog(
            id=id_for_log,
            exe_path_as_id=session.process_name,
            process_name=session.process_name,
            program_name=session.window_title,
            # Assumes (10 - n) sec will be deducted later
            hours_spent=sixty_sec / SECONDS_PER_HOUR,
            start_time=very_early_morning,
            end_time=very_early_morning + timedelta(minutes=5),
            duration_in_sec=60.0,
            gathering_date=get_start_of_day_from_datetime(very_early_morning),
            gathering_date_local=get_start_of_day_from_datetime(very_early_morning).replace(
                tzinfo=None
            ),
            created_at=very_early_morning,
        )

    def group_of_preexisting_logs():
        yield make_preexisting_log(session1, made_up_pids[0])
        yield make_preexisting_log(session2, made_up_pids[1])
        yield make_preexisting_log(session3, made_up_pids[2])
        yield make_preexisting_log(session4, made_up_pids[3])

        # return [s1,s2,s3,s4]

    pretend_sums_from_db = group_of_preexisting_summaries()
    pretend_logs_from_db = group_of_preexisting_logs()

    #
    # Summary methods
    #
    summary_start_session_spy = Mock(side_effect=p_summary_dao.start_session)
    p_summary_dao.start_session = summary_start_session_spy

    summary_add_new_item_spy = Mock()
    p_summary_dao.add_new_item = summary_add_new_item_spy

    push_window_ahead_ten_sec_spy = Mock(side_effect=p_summary_dao.push_window_ahead_ten_sec)
    p_summary_dao.push_window_ahead_ten_sec = push_window_ahead_ten_sec_spy

    make_find_all_from_day_query_spy = Mock(
        side_effect=p_summary_dao.create_find_all_from_day_query
    )
    p_summary_dao.create_find_all_from_day_query = make_find_all_from_day_query_spy

    sum_dao_execute_and_read_one_or_none_spy = Mock()
    sum_dao_execute_and_read_one_or_none_spy.return_value = next(pretend_sums_from_db)
    p_summary_dao.execute_and_read_one_or_none = sum_dao_execute_and_read_one_or_none_spy

    find_todays_entry_for_program_mock = Mock(
        side_effect=p_summary_dao.find_todays_entry_for_program
    )
    find_todays_entry_for_program_mock.return_value = next(pretend_sums_from_db)
    # So that the condition "the user already has a session for these programs" is met
    p_summary_dao.find_todays_entry_for_program = find_todays_entry_for_program_mock

    execute_window_push_spy = Mock()
    p_summary_dao.execute_window_push = execute_window_push_spy

    do_addition_spy = Mock()
    p_summary_dao.do_addition = do_addition_spy

    #
    # Logger methods
    #
    logger_add_new_item_spy = Mock()
    p_logging_dao.add_new_item = logger_add_new_item_spy

    find_session_spy = Mock(side_effect=p_logging_dao.find_session)
    find_session_spy.return_value = next(pretend_logs_from_db)  # returns a ProgramLog
    p_logging_dao.find_session = find_session_spy

    logging_dao_execute_and_read_one_or_none_spy = Mock()
    # This happens in
    logging_dao_execute_and_read_one_or_none_spy.return_value = next(pretend_logs_from_db)
    p_logging_dao.execute_and_read_one_or_none = logging_dao_execute_and_read_one_or_none_spy

    finalize_log_spy = Mock(side_effect=p_logging_dao.finalize_log)
    p_logging_dao.finalize_log = finalize_log_spy

    update_item_spy = Mock()
    p_logging_dao.update_item = update_item_spy

    # program_facade = MockProgramFacade()

    spy_on_set_program_state = Mock(side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(side_effect=mock_program_facade.listen_for_window_changes)
    mock_program_facade.listen_for_window_changes = spy_on_listen_for_window

    try:
        # ### Act
        surveillance_manager.start_trackers()

        async def wait_for_events_to_process():
            # Wait for events to be processed
            try:
                print("\n++\n++\nWaiting for events to be processed...")
                # Give the events time to propagate through the system
                # Try for up to 10 iterations
                for _ in range(len(test_data_clone)):
                    if mock_program_facade.yield_count == 4:
                        print(mock_program_facade.yield_count, "stop signal ++ \n ++ \n ++ \n ++")
                        break
                    # Seems 1.3 is the minimum wait to get this done
                    await asyncio.sleep(1.3)  # Short sleep between checks ("short")
                    # await asyncio.sleep(1.3)  # Short sleep between checks ("short")
                    # await asyncio.sleep(1.7)  # Short sleep between checks ("short")
                    # await asyncio.sleep(0.8)  # Short sleep between checks ("short")
                    # Check if we have the expected number of calls
                    if spy_on_set_program_state.call_count >= len(test_data_clone) - 1:
                        print(f"Events processed after {_+1} iterations")
                        surveillance_manager.program_thread.stop()  # Stop the thread properly
                        break
            finally:
                surveillance_manager.program_thread.stop()

        await wait_for_events_to_process()

        event_count = len(test_data_clone)
        active_entry = 1

        def assert_all_window_change_args_match_src_material(calls_from_spy):
            assert calls_from_spy[0][0][0].exe_path == session1.exe_path
            assert calls_from_spy[1][0][0].exe_path == session2.exe_path
            assert calls_from_spy[2][0][0].exe_path == session3.exe_path
            assert calls_from_spy[3][0][0].exe_path == session4.exe_path

        def assert_state_machine_had_correct_order():
            assert_all_spy_args_were_sessions(
                asm_set_new_session_spy, event_count, "Activity State Machine"
            )

        def assert_activity_recorder_called_expected_times(count_of_events):
            assert on_new_session_spy.call_count == count_of_events

            # Count is 4 here becasuse it's used in on_new_session as of 04/26
            assert push_window_ahead_ten_sec_spy.call_count == sum(
                [x // window_push_length for x in durations_for_keep_alive]
            )

            # The final entry here is holding the window push open
            assert finalize_log_spy.call_count == count_of_events - active_entry
            assert add_partial_window_spy.call_count == count_of_events - active_entry

        def assert_session_was_in_order(actual: ProgramSession, i):
            """The first one"""
            expected = test_events[i]
            # print("Loop: ", i)
            # print("Expected:", expected.start_time)
            # print("Actual:", actual.start_time)
            assert actual.exe_path == expected.exe_path
            assert actual.process_name == expected.process_name
            assert actual.window_title == expected.window_title
            assert actual.detail == expected.detail
            assert actual.start_time == expected.start_time

        def assert_all_spy_args_were_sessions(spy_from_mock, expected_loops: int, spy_name: str):
            print(f"Asserting against {spy_name} with count {len(spy_from_mock.call_args_list)}")
            for i in range(0, expected_loops):
                some_session = spy_from_mock.call_args_list[i][0][0]
                assert isinstance(some_session, ProgramSession)
                assert_session_was_in_order(some_session, i)
            call_count = len(spy_from_mock.call_args_list)
            assert call_count == expected_loops, f"Expected exactly {expected_loops} calls"

        def assert_all_on_new_sessions_received_sessions():
            assert_all_spy_args_were_sessions(
                on_new_session_spy, event_count, "on_new_session_spy"
            )

        def assert_all_on_state_changes_received_sessions():
            """
            Note that on_state_changed probably is called 3x, not 4x, because
            nothing happens to push the final session out of the Arbiter.
            """
            one_left_in_arb = 1
            assert_all_spy_args_were_sessions(
                on_state_changed_spy, event_count - one_left_in_arb, "on_state_changed_spy"
            )

        def assert_add_partial_window_happened_as_expected():
            """
            Deduct duration might happen 3x b/c of the final val staying in the Arbiter.
            """
            # This func does not use assert_all_spy_args_were_sessions because
            # the arg order is reversed here, i.e. 0th arg is an int
            one_left_in_arb = 1
            total_loops = event_count - one_left_in_arb
            for i in range(0, total_loops):
                some_duration = add_partial_window_spy.call_args_list[i][0][0]
                assert isinstance(some_duration, int)

                some_session = add_partial_window_spy.call_args_list[i][0][1]
                assert isinstance(some_session, ProgramSession)
                assert_session_was_in_order(some_session, i)

            call_count = len(add_partial_window_spy.call_args_list)
            assert call_count == total_loops, f"Expected exactly {total_loops} calls"

        def assert_activity_recorder_saw_expected_vals():
            """Asserts that the recorder spies all saw, in general, what was expected."""
            assert_all_on_new_sessions_received_sessions()
            assert_all_on_state_changes_received_sessions()
            assert_add_partial_window_happened_as_expected()

        # ## Assert that each session showed up as specified above, in the correct place

        # --
        # -- Most ambitious stuff at the end. Alternatively: Earlier encounters asserted first
        # --

        assert event_count == 4
        assert start_new_session_spy.call_count == event_count
        assert window_change_spy.call_count == 4
        assert window_change_spy.call_count == event_count

        # Verify the programTracker's start_time times were accurate
        for i in range(0, event_count):
            start_time_arg = start_new_session_spy.call_args_list[i][0][1]

            assert start_time_arg.dt == times[i].dt

        def assert_window_change_spy_as_expected(arg):
            assert isinstance(arg, ProgramSession)
            assert arg.exe_path == test_events[i].exe_path

        for i in range(0, event_count):
            arg = window_change_spy.call_args_list[i][0][0]
            assert_window_change_spy_as_expected(arg)

        window_change_calls = window_change_spy.call_args_list

        def assert_all_start_new_session_spy_args_were_dicts(
            spy_from_mock, expected_loops: int, spy_name: str
        ):
            print(f"Asserting against {spy_name} with count {len(spy_from_mock.call_args_list)}")
            for i in range(0, expected_loops):
                actual_dict = spy_from_mock.call_args_list[i][0][0]
                actual_start = spy_from_mock.call_args_list[i][0][1]
                assert isinstance(actual_dict, dict)
                expected = test_events[i]
                print("Loop: ", i)
                print("Expected:", expected)
                print("Actual:", actual_dict)
                assert actual_dict["exe_path"] == expected.exe_path
                assert actual_dict["process_name"] == expected.process_name
                assert actual_start == expected.start_time
            call_count = len(spy_from_mock.call_args_list)
            assert call_count == expected_loops, f"Expected exactly {expected_loops} calls"

        assert_all_start_new_session_spy_args_were_dicts(
            start_new_session_spy, event_count, "Start new session spy"
        )

        def assert_all_start_new_session_spy_args_received_correct_time(expected_loops):
            print("Asserting that start new session had the correct times")
            for i in range(0, expected_loops):
                some_dict = start_new_session_spy.call_args_list[i][0][0]
                some_dt = start_new_session_spy.call_args_list[i][0][1]
                assert some_dt == test_events[i].start_time

        assert_all_start_new_session_spy_args_received_correct_time(event_count)

        assert_all_spy_args_were_sessions(window_change_spy, event_count, "Window change spy")

        assert_all_window_change_args_match_src_material(window_change_calls)

        assert (
            len(window_change_calls) == 4
        ), "The number of sessions is four, so the calls should be four"

        assert window_change_spy.call_count == event_count  # Deliberately redundant

        assert spy_on_set_program_state.call_count == event_count  # Deliberately redundant

        assert_state_machine_had_correct_order()

        assert_activity_recorder_saw_expected_vals()

        assert_activity_recorder_called_expected_times(event_count)

        assert find_todays_entry_for_program_mock.call_count == event_count

        # It's never used because preexisting sessions block the path
        assert summary_start_session_spy.call_count == 0

        # --
        # -- A much needed value: The count of window pushes
        # --
        total_pushes = sum([x // window_push_length for x in durations_for_keep_alive])

        def assert_sqlalchemy_layer_went_as_expected():
            """Covers only stuff that obscures sqlalchemy code."""
            assert sum_dao_execute_and_read_one_or_none_spy.call_count == event_count
            # FIXME:L assert 10 == (4 - 1)
            # execute_and_read_one_or_none is used in find_session, which
            # is used in window push and finalize log

            concluded_sessions = event_count - active_entry

            assert (
                logging_dao_execute_and_read_one_or_none_spy.call_count
                == total_pushes + concluded_sessions
            )

            assert (
                summary_add_new_item_spy.call_count == 0
            ), "A Summary existed already for each session, so this shouldn't happen"
            assert logger_add_new_item_spy.call_count == event_count

            assert update_item_spy.call_count == total_pushes + concluded_sessions

            assert execute_window_push_spy.call_count == total_pushes

        assert_sqlalchemy_layer_went_as_expected()

        # Count is 4 here becasuse it's used in on_new_session as of 04/26
        assert len(push_window_ahead_ten_sec_spy.call_args_list) == total_pushes

        def assert_sessions_form_a_chain():
            sessions = []
            for i in range(0, event_count - active_entry):
                args = on_state_changed_spy.call_args_list[i][0]
                sessions.append(args[0])
            assert sessions[0].end_time == sessions[1].start_time
            assert sessions[1].end_time == sessions[2].start_time
            # assert sessions[2].end_time == sessions[3].start_time
            # Sessions[3] has no .start_time to link up with
            # Sessions[4] is still left in the arbiter (not spied on)

        assert_sessions_form_a_chain()

        assert push_window_ahead_ten_sec_spy.call_count == total_pushes

        assert do_addition_spy.call_count == event_count - active_entry

        assert finalize_log_spy.call_count == event_count - active_entry

        assert (
            summary_add_new_item_spy.call_count == 0
        ), "A new summary was created despite preexisting sessions"

        assert logger_add_new_item_spy.call_count == event_count

        assert len(logger_add_new_item_spy.call_args_list) == event_count

        for i in range(0, event_count):
            summary_log = logger_add_new_item_spy.call_args_list[i][0][0]

            assert isinstance(summary_log, ProgramSummaryLog)
            assert (
                summary_log.exe_path_as_id == test_data_clone[i].exe_path
            ), "Exe path didn't make it to one of it's destinations"
            assert summary_log.process_name == test_data_clone[i].process_name
            assert (
                summary_log.program_name == test_data_clone[i].window_title
            ), "Window title's end result didn't look right"
    finally:
        v = await surveillance_manager.cleanup()
        await asyncio.sleep(0)  # Let pending tasks schedule
        tasks = [t for t in asyncio.all_tasks() if not t.done()]
        if tasks and len(tasks) >= 2:
            print("⚠️ Pending tasks at teardown:")
            for t in tasks:
                print(f" - {t}")
