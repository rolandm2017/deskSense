# test_program_session_path.py
"""
Proves that the ProgramSession and all relevant fields get where they're intended to go.

Using three sessions to notice edge cases and prove a chain is established.
"""
import pytest
import asyncio
from unittest.mock import Mock

from datetime import datetime, timedelta
from typing import Dict, List, cast

import traceback

from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.surveillance_manager import FacadeInjector, SurveillanceManager
from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.trackers.program_tracker import ProgramTrackerCore

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.models import DailyProgramSummary, ProgramSummaryLog

from surveillance.src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance
from surveillance.src.object.classes import ChromeSession, ProgramSession

from surveillance.src.object.classes import ProgramSession
from surveillance.src.object.classes import ProgramSessionDict

from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.const import SECONDS_PER_HOUR


from ..mocks.mock_clock import UserLocalTimeMockClock


def fmt_time_string(s):
    return datetime.fromisoformat(s)


# def make_up_pids():
#     print("2345")
#     yield 2345
#     print("3456")
#     yield 3456
#     print("4567")
#     yield 4567
#     print("5678")
#     yield 5678
#     print("out of pids")

made_up_pids = [2345, 3456, 4567, 5678]


def convert_back_to_dict(session: ProgramSession, pid) -> ProgramSessionDict:
    return {"os": "Windows 11",
            "pid": pid,
            "exe_path": session.exe_path,
            "process_name": session.process_name,
            "window_title": session.window_title}


imaginary_path_to_chrome = "imaginary/path/to/Chrome.exe"
imaginary_chrome_processe = "Chrome.exe"


session1 = ProgramSession(
    exe_path=imaginary_path_to_chrome,
    process_name=imaginary_chrome_processe,
    title='Google Chrome',
    detail="X. It's what's happening / X",
    start_time=UserLocalTime(fmt_time_string(
        "2025-03-22 16:14:50.201399-07:00")),
    end_time=None,
    duration_for_tests=None,
    productive=False
)
session2 = ProgramSession(
    exe_path='C:/wherever/you/find/Postman.exe',
    process_name='Xorg',
    title='My Workspace',
    detail='dash | Overview',
    start_time=UserLocalTime(fmt_time_string(
        "2025-03-22 16:15:55.237392-07:00")),
    end_time=None,
    duration_for_tests=None,
    productive=False
)
session3 = ProgramSession(
    exe_path='C:/path/to/VSCode.exe',
    process_name='Code.exe',
    title='Visual Studio Code',
    detail='surveillance_manager.py - deskSense',
    start_time=UserLocalTime(fmt_time_string(
        "2025-03-22 16:16:03.374304-07:00")),
    end_time=None,
    duration_for_tests=None,
    productive=False
)

session4 = ProgramSession(
    # NOTE: Manual change from Gnome Shell to a second Chrome entry
    exe_path=imaginary_path_to_chrome,
    process_name=imaginary_chrome_processe,
    title='Google Chrome',
    detail='Google',
    start_time=UserLocalTime(fmt_time_string(
        "2025-03-22 16:16:17.480951-07:00")),
    end_time=None,
    duration_for_tests=None,
    productive=False
)
test_events = [
    session1,
    session2,
    session3,
    session4
]

@pytest.fixture
def validate_test_data():
    """Exists to ensure no PEBKAC. The data really does say what was intended."""
    # Validate your dummy test data
    for i in range(0, 4):
        assert isinstance(test_events[i].start_time, UserLocalTime)
        assert isinstance(test_events[i].start_time.dt, datetime)
        assert test_events[i].start_time.dt.tzinfo is not None

        assert test_events[i].end_time is None

        if i == 3:
            break  # There is no 4th value
        assert test_events[i].start_time < test_events[i + 1].start_time, "Events must be chronological"
    
    # Return the data to the test
    return test_events


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


# @pytest.fixture
# def setup_for_test(regular_session, mock_async_session_maker):
#     # TODO: refactor so that this class lives in one place (it's a duplicate)

#     return surveillance_manager, program_sum_dao, program_logging_dao, mock_program_facade, activity_arbiter

sum_counter = 0
log_counter = 0

@pytest.mark.asyncio
async def test_tracker_to_db_path_with_preexisting_sessions(validate_test_data, regular_session, mock_async_session_maker):
    """
    The goal of the test is to prove that programSesssions get thru the DAO layer fine
    
    Here, "preexisting session" means "a value that, in 
    pretend, already existed in the db when the test started."

    Intent is to not worry about start and end times too much. Focus is the str vals.
    """
    # surveillance_manager, summary_dao, logging_dao, mock_program_facade, arbiter = setup_for_test

    valid_test_data = validate_test_data

    class MockProgramFacade:
        def __init__(self):
            self.yield_count = 0  # Initialize the counter
            self.MAX_EVENTS = len(valid_test_data)
            self.test_program_dicts = [convert_back_to_dict(x, made_up_pids[i]) for i, x in enumerate(valid_test_data)]

        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for program_event in self.test_program_dicts:
                self.yield_count += 1
                print(f"[yield] Yielding event: {program_event['window_title']} for count {self.yield_count}")
                yield program_event  # Always yield the event first

                # Check if we've reached our limit AFTER yielding
                if self.yield_count >= self.MAX_EVENTS:
                    print(
                        f"\n\nReached max events limit ({self.MAX_EVENTS}), stopping generator\n\n")
                    # stop more events from occurring
                    surveillance_manager.program_thread.stop_event.set()
                    break

    mock_program_facade = MockProgramFacade()

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(
        side_effect=mock_program_facade.listen_for_window_changes)
    mock_program_facade.listen_for_window_changes = spy_on_listen_for_window

    def choose_program_facade(current_os):
        return mock_program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade)
    
    times = []
    """
    Count of occurrences of the clock being used:
    1. ProgramTrackerCore - 1x per session
    2. ActivityRecorder.on_new_session - 1x per session
    3. ActivityRecorder.add_ten_sec_to_end_time - whenever it's called
    """
    mock_user_facing_clock = UserLocalTimeMockClock(times)

    wont_be_used = UserLocalTimeMockClock([])

    activity_arbiter = ActivityArbiter(
        mock_user_facing_clock, pulse_interval=0.1)
    
    asm_set_new_session_spy = Mock(side_effect=activity_arbiter.state_machine.set_new_session)
    activity_arbiter.state_machine.set_new_session = asm_set_new_session_spy

    p_logging_dao = ProgramLoggingDao(regular_session)
    chrome_logging_dao = ChromeLoggingDao(regular_session)

    p_summary_dao = ProgramSummaryDao(
        p_logging_dao, regular_session, mock_async_session_maker)
    chrome_sum_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session, mock_async_session_maker)

    chrome_svc = ChromeService(wont_be_used, activity_arbiter)
    surveillance_manager = SurveillanceManager(cast(UserFacingClock, mock_user_facing_clock),
                                               mock_async_session_maker, regular_session, chrome_svc, activity_arbiter, facades)

    window_change_spy = Mock(
        side_effect=surveillance_manager.program_tracker.window_change_handler)
    surveillance_manager.program_tracker.window_change_handler = window_change_spy


    activity_recorder = ActivityRecorder(
        cast(UserFacingClock, mock_user_facing_clock), p_logging_dao, chrome_logging_dao, p_summary_dao, chrome_sum_dao)

    #
    # # Activity Recorder spies
    #

    on_new_session_spy = Mock(side_effect=activity_recorder.on_new_session)
    activity_recorder.on_new_session = on_new_session_spy

    add_ten_sec_to_end_time_spy = Mock(side_effect=activity_recorder.add_ten_sec_to_end_time)
    activity_recorder.add_ten_sec_to_end_time = add_ten_sec_to_end_time_spy

    on_state_changed_spy = Mock(side_effect=activity_recorder.on_state_changed)
    activity_recorder.on_state_changed = on_state_changed_spy

    deduct_duration_spy = Mock(side_effect=activity_recorder.deduct_duration)
    activity_recorder.deduct_duration = deduct_duration_spy
    
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
            gathering_date=session.start_time.date())

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
            duration=timedelta(seconds=60),
            gathering_date=very_early_morning.date(),
            created_at=very_early_morning
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
    summary_add_new_item_spy = Mock()
    p_summary_dao.add_new_item = summary_add_new_item_spy

    push_window_ahead_ten_sec_spy = Mock(side_effect=p_summary_dao.push_window_ahead_ten_sec)
    p_summary_dao.push_window_ahead_ten_sec = push_window_ahead_ten_sec_spy

    make_find_all_from_day_query_spy = Mock(
        side_effect=p_summary_dao.create_find_all_from_day_query)
    p_summary_dao.create_find_all_from_day_query = make_find_all_from_day_query_spy

    sum_dao_execute_and_read_one_or_none_spy = Mock()
    sum_dao_execute_and_read_one_or_none_spy.return_value = next(pretend_sums_from_db)
    p_summary_dao.execute_and_read_one_or_none = sum_dao_execute_and_read_one_or_none_spy

    find_todays_entry_for_program_mock = Mock(
        side_effect=p_summary_dao.find_todays_entry_for_program)
    find_todays_entry_for_program_mock.return_value = next(pretend_sums_from_db)
    # So that the condition "the user already has a session for these programs" is met
    p_summary_dao.find_todays_entry_for_program = find_todays_entry_for_program_mock
    
    execute_window_push_spy = Mock()
    p_summary_dao.execute_window_push = execute_window_push_spy

    do_deduction_spy = Mock()
    p_summary_dao.do_deduction = do_deduction_spy

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

    spy_on_set_program_state = Mock(
        side_effect=activity_arbiter.set_program_state)
    activity_arbiter.set_program_state = spy_on_set_program_state

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(
        side_effect=mock_program_facade.listen_for_window_changes)
    mock_program_facade.listen_for_window_changes = spy_on_listen_for_window

     # ### Act
    surveillance_manager.start_trackers()

    async def wait_for_events_to_process():
        # Wait for events to be processed
        print("\n++\n++\nWaiting for events to be processed...")
        # Give the events time to propagate through the system
        # Try for up to 10 iterations
        for _ in range(len(valid_test_data)):
            if mock_program_facade.yield_count == 4:
                print(mock_program_facade.yield_count,
                    "stop signal ++ \n ++ \n ++ \n ++")
                break
            await asyncio.sleep(1.7)  # Short sleep between checks ("short")
            # await asyncio.sleep(0.8)  # Short sleep between checks ("short")
            # Check if we have the expected number of calls
            if spy_on_set_program_state.call_count >= len(valid_test_data) - 1:
                print(f"Events processed after {_+1} iterations")
                surveillance_manager.program_thread.stop()  # Stop the thread properly
                break

    await wait_for_events_to_process()

    event_count = len(valid_test_data)


    def assert_all_window_change_args_match_src_material(calls_from_spy):
        assert calls_from_spy[0][0][0].exe_path == session1.exe_path
        assert calls_from_spy[1][0][0].exe_path == session2.exe_path
        assert calls_from_spy[2][0][0].exe_path == session3.exe_path
        assert calls_from_spy[3][0][0].exe_path == session4.exe_path

    def assert_state_machine_had_correct_order():
        assert_all_spy_args_were_sessions(asm_set_new_session_spy, "Activity State Machine")
        # for i in range(0, event_count):
        #     some_session = asm_set_new_session_spy.call_args_list[i][0][0]
        #     assert isinstance(some_session, ProgramSession)
        #     assert_session_was_in_order(some_session, i)

    def assert_activity_recorder_called_expected_times(count_of_events):
        assert on_new_session_spy.call_count == count_of_events

        assert push_window_ahead_ten_sec_spy.call_count == count_of_events

        assert finalize_log_spy.call_count == count_of_events
        assert deduct_duration_spy.call_count == count_of_events

   

    def assert_session_was_in_order(actual: ProgramSession, i):
        expected = test_events[i]
        print(i, "441ru")
        print("Actual start time: \t", actual.start_time)
        print("Expected start time: \t", expected.start_time)
        print("\n", actual, "441ru")
        print("\n", expected, "442ru")
        assert actual.start_time == expected.start_time

    def assert_all_spy_args_were_sessions(spy_from_mock, spy_name):
        print(f"Asserting against {spy_name}")
        for i in range(0, event_count):
            some_session = spy_from_mock.call_args_list[i][0][0]
            assert isinstance(some_session, ProgramSession)
            assert_session_was_in_order(some_session, i)
        call_count = len(spy_from_mock.call_args_list)
        assert call_count == event_count, f"Expected exactly {event_count} calls"

    def assert_all_on_new_sessions_received_sessions():
        assert_all_spy_args_were_sessions(on_new_session_spy, "on_new_session_spy")
        # for i in range(0, count_of_events):
        #     some_session = on_new_session_spy.call_args_list[i][0]
        #     assert isinstance(some_session, ProgramSession) or isinstance(some_session, ChromeSession)
        # call_count = len(on_new_session_spy.call_args_list)
        # assert call_count == count_of_events, f"Expected exactly {count_of_events} calls"

    def assert_all_on_state_changes_received_sessions():
        """
        Note that on_state_changed probably is called 3x, not 4x, because
        nothing happens to push the final session out of the Arbiter.
        """
        assert_all_spy_args_were_sessions(on_state_changed_spy, "on_state_changed_spy")
        # for i in range(0, count_of_events):
        #     some_session = on_state_changed_spy.call_args_list[i][0]
        #     assert isinstance(some_session, ProgramSession) or isinstance(some_session, ChromeSession)
        # call_count = len(on_state_changed_spy.call_args_list)
        # assert call_count == count_of_events, f"Expected exactly {count_of_events} calls"

    def assert_deduct_duration_happened_as_expected():
        """
        Deduct duration might happen 3x b/c of the final val staying in the Arbiter.
        """
        assert_all_spy_args_were_sessions(deduct_duration_spy, "deduct_duration_spy")

    def assert_activity_recorder_saw_expected_vals():
        """Asserts that the recorder spies all saw, in general, what was expected."""
        assert_all_on_new_sessions_received_sessions()
        assert_all_on_state_changes_received_sessions()
        assert_deduct_duration_happened_as_expected()

    try: 
        # TODO: Final act here should be to organize the assertions.
        # ### Assert!

        # Most ambitious stuff at the end. Alternatively: Earlier encounters asserted first


        # Some basics, including, "assert that each session's field was used as intended"

        # TODO: Cook it so that push_window_ahead_ten_sec is called 2? 3x? for each dao type
        # TODO: Otherwise, the method isn't covered! 
        
        # ## Assert that each session showed up as specified above, in the correct place
        
        # assert that they form a chain

        #
        # ### Stuff before the Recorder layer - sanity checks.
        #

        
        assert event_count == 4
        assert window_change_spy.call_count == 4
        assert window_change_spy.call_count == event_count

        # args, _ = window_change_spy.call_args_list
        def assert_window_change_spy_as_expected(arg):
            print(i,window_change_spy.call_count, "424ru")
            assert isinstance(arg, ProgramSession)
            assert arg.exe_path == test_events[i].exe_path

        for i in range(0, event_count):
            arg = window_change_spy.call_args_list[i][0][0]
            assert_window_change_spy_as_expected(arg)
            # assert isinstance(arg, tuple)  # Cannot explain, expected ProgramSession
            # print(i,window_change_spy.call_count, "424ru")
            # print(arg, "428ru")
            # assert isinstance(arg[0], ProgramSession)
            # assert arg[0].exe_path == test_events[i].exe_path


        window_change_calls = window_change_spy.call_args_list

        assert_all_spy_args_were_sessions(window_change_spy, "Window change spy")

        assert_all_window_change_args_match_src_material(window_change_calls)

        assert len(window_change_calls) == 4, "The number of sessions is four, so the calls should be four"

        assert window_change_spy.call_count == event_count  # Deliberately redundant

        assert spy_on_set_program_state.call_count == event_count  # Deliberately redundant

        assert_state_machine_had_correct_order()

        assert_activity_recorder_saw_expected_vals()

        def assert_high_level_recorder_spies_match(v):
            pass
        
        assert find_todays_entry_for_program_mock.call_count == event_count
        assert sum_dao_execute_and_read_one_or_none_spy.call_count == event_count
        assert logging_dao_execute_and_read_one_or_none_spy.call_count == event_count
        
        #
        # assert that the alchemy layer was used as expected. Each of them.
        #
        assert summary_add_new_item_spy.call_count == 0, "A Summary existed already for each session, so this shouldn't happen"
        assert logger_add_new_item_spy.call_count == event_count
        assert update_item_spy.call_count == event_count
        v = execute_window_push_spy.call_args_list
        print(v, "457ru")
        # FIXME: [call(<sqlalchemy.sql.selectable.Select object at 0x000001314FD61610>, 'imaginary/path/to/Chrome.exe', 
        # datetime.datetime(2025, 3, 22, 16, 16, 3, 374304, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=61200))))] 457ru
        # NOTE that this is the start_time of session3, but the path of session4. How can this be? Unless something was switched

        # TEMP TODO: move this
        print(push_window_ahead_ten_sec_spy.call_args_list, "470ru")
        args = push_window_ahead_ten_sec_spy.call_args_list[0][0]

        assert args[0].exe_path == session4.exe_path
        received =  args[0].start_time.dt
        target = session4.start_time.dt
        assert received.hour == target.hour
        assert received.minute == target.minute
        assert received.second == target.second

        assert push_window_ahead_ten_sec_spy.call_count == 1  # The final entry being held suspended in Arbiter        

        assert execute_window_push_spy.call_count == event_count
        assert do_deduction_spy.call_count == event_count

        assert finalize_log_spy.call_count == event_count

        # assert that process_name made it into where it belongs, and looked right
        # TODO: assert that detail looked right

        assert summary_add_new_item_spy.call_count == len(valid_test_data)
        
        args, _ = summary_add_new_item_spy.call_args    
        assert all(isinstance(arg, DailyProgramSummary) for arg in args[:event_count])
        for i in range(0, event_count):
            assert args[i].exe_path_as_id == valid_test_data[i].exe_path, "Exe path didn't make it to one of it's destinations"
            assert args[i].program_name == valid_test_data[i].window_title, "Window title's end result didn't look right"
        
        assert logger_add_new_item_spy.call_count == len(valid_test_data)
        
        args, _ = summary_add_new_item_spy.call_args    

        # def assert_summary_dao_add_new_item_received_expected_vals():
        #     pass
        assert all(isinstance(arg, ProgramSummaryLog) for arg in args[:event_count])
        for i in range(0, event_count):
            assert args[i].exe_path_as_id == valid_test_data[i].exe_path, "Exe path didn't make it to one of it's destinations"
            assert args[i].process_name == valid_test_data[i].process_name
            assert args[i].program_name == valid_test_data[i].window_title, "Window title's end result didn't look right"
    finally:
        # Run the cleanup
        await cleanup_test_resources(surveillance_manager)
