# test_program_session_path.py
"""
Proves that the ProgramSession and all relevant fields get where they're intended to go.

Using three sessions to notice edge cases and prove a chain is established.
"""
import pytest
import asyncio
from unittest.mock import Mock

from datetime import datetime
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


from ..mocks.mock_clock import UserLocalTimeMockClock, MockClock


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


@pytest.fixture
def setup_for_test(regular_session, mock_async_session_maker):
    # TODO: refactor so that this class lives in one place (it's a duplicate)

    class MockProgramFacade:
        def __init__(self):
            self.yield_count = 0  # Initialize the counter
            self.MAX_EVENTS = len(test_events)
            self.test_program_dicts = [convert_back_to_dict(x, made_up_pids[i]) for i, x in enumerate(test_events)]

        def listen_for_window_changes(self):
            print("Mock listen_for_window_changes called")
            for program_event in self.test_program_dicts:
                self.yield_count += 1
                print(f"Yielding event: {program_event['window_title']}")
                yield program_event  # Always yield the event first

                # Check if we've reached our limit AFTER yielding
                if self.yield_count >= self.MAX_EVENTS:
                    print(
                        f"Reached max events limit ({self.MAX_EVENTS}), stopping generator")
                    # stop more events from occurring
                    surveillance_manager.program_thread.stop_event.set()
                    break

    mock_program_facade = MockProgramFacade()

    def choose_program_facade(current_os):
        return mock_program_facade

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade)
    mock_user_facing_clock = MockClock([])
    get_it_done_quickly_interval = 0.1
    activity_arbiter = ActivityArbiter(
        mock_user_facing_clock, pulse_interval=get_it_done_quickly_interval)

    program_logging_dao = ProgramLoggingDao(regular_session)
    chrome_logging_dao = ChromeLoggingDao(regular_session)

    program_sum_dao = ProgramSummaryDao(
        program_logging_dao, regular_session, mock_async_session_maker)
    chrome_sum_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session, mock_async_session_maker)

    activity_recorder = ActivityRecorder(
        cast(UserFacingClock, mock_user_facing_clock), program_logging_dao, chrome_logging_dao, program_sum_dao, chrome_sum_dao)

    chrome_svc = ChromeService(mock_user_facing_clock, activity_arbiter)
    surveillance_manager = SurveillanceManager(cast(UserFacingClock, mock_user_facing_clock),
                                               mock_async_session_maker, regular_session, chrome_svc, activity_arbiter, facades)

    return surveillance_manager, program_sum_dao, program_logging_dao, mock_program_facade, activity_arbiter

counter = 0

@pytest.mark.asyncio
async def test_tracker_to_db_path_with_preexisting_sessions(setup_for_test):
    """The goal of the test is to prove that programSesssions get thru the DAO layer fine"""
    surveillance_manager, summary_dao, logging_dao, mock_program_facade, arbiter = setup_for_test

    # ### Arrange
    starting_hours_spent_in_db = 1.0

    def make_preexisting_entry(session, id_for_session):
        """foosssdfdfdsdsdfsdfds"""
        return DailyProgramSummary(
            id=id_for_session, 
            exe_path_as_id=session.exe_path, 
            program_name=session.window_title, 
            hours_spent=starting_hours_spent_in_db, 
            gathering_date=session.start_time.date())

    def group_of_preexisting_entries():
        s1 = make_preexisting_entry(session1, made_up_pids[0])
        s2 = make_preexisting_entry(session2, made_up_pids[1])
        s3 = make_preexisting_entry(session3, made_up_pids[2])
        s4 = make_preexisting_entry(session4, made_up_pids[3])
        return [s1,s2,s3,s4]

    pretend_rows_from_db = group_of_preexisting_entries()

    def side_effect_function(query):
        global counter
        result = pretend_rows_from_db[counter % 4]
        counter += 1
        return result

    # Summary methods
    summary_add_new_item_spy = Mock()
    summary_dao.add_new_item = summary_add_new_item_spy

    make_find_all_from_day_query_spy = Mock(
        side_effect=summary_dao.create_find_all_from_day_query)
    summary_dao.create_find_all_from_day_query = make_find_all_from_day_query_spy

    sum_dao_execute_and_read_one_or_none_spy = Mock()
    sum_dao_execute_and_read_one_or_none_spy.return_value = side_effect_function  # FIXME: if this causes problems, move it to line 212, meaning "replace the dao method return val instead"
    summary_dao.execute_and_read_one_or_none = sum_dao_execute_and_read_one_or_none_spy

    # find_todays_entry_for_program_mock = Mock(
    #     side_effect=summary_dao.find_todays_entry_for_program)
    # find_todays_entry_for_program_mock.return_value = pretend_row_from_db
    # So that the condition "the user already has a session for these programs" is met
    # summary_dao.find_todays_entry_for_program = find_todays_entry_for_program_mock

    # Logger methods
    logger_add_new_item_spy = Mock()
    logging_dao.add_new_item = logger_add_new_item_spy

    logging_dao_execute_and_read_one_or_none_spy = Mock()
    logging_dao_execute_and_read_one_or_none_spy.return_value = None  # FIXME: if this causes problems, move it to line 212, meaning "replace the dao method return val instead"
    logging_dao.execute_and_read_one_or_none = logging_dao_execute_and_read_one_or_none_spy

    finalize_log_spy = Mock(side_effect=logging_dao.finalize_log)
    logging_dao.finalize_log = finalize_log_spy

    update_item_spy = Mock()
    logging_dao.update_item = update_item_spy

    # program_facade = MockProgramFacade()

    spy_on_set_program_state = Mock(
        side_effect=arbiter.set_program_state)
    arbiter.set_program_state = spy_on_set_program_state

    # Spy on listen_for_window_changes
    spy_on_listen_for_window = Mock(
        side_effect=mock_program_facade.listen_for_window_changes)
    mock_program_facade.listen_for_window_changes = spy_on_listen_for_window
    try: 

        # ### Act
        surveillance_manager.start_trackers()

        async def wait_for_events_to_process():
            # Wait for events to be processed
            print("\n++\n++\nWaiting for events to be processed...")
            # Give the events time to propagate through the system
            # Try for up to 10 iterations
            for _ in range(len(test_events)):
                if mock_program_facade.yield_count == 4:
                    print(mock_program_facade.yield_count,
                        "stop signal ++ \n ++ \n ++ \n ++")
                    break
                await asyncio.sleep(1.7)  # Short sleep between checks ("short")
                # await asyncio.sleep(0.8)  # Short sleep between checks ("short")
                # Check if we have the expected number of calls
                if spy_on_set_program_state.call_count >= len(test_events) - 1:
                    print(f"Events processed after {_+1} iterations")
                    surveillance_manager.program_thread.stop()  # Stop the thread properly
                    break

        await wait_for_events_to_process()

        # ### Assert!

        event_count = len(test_events)

        # Some basics, including, "assert that each session's field was used as intended"
        assert summary_add_new_item_spy.call_count == len(test_events)
        
        args, _ = summary_add_new_item_spy.call_args    
        assert all(isinstance(arg, DailyProgramSummary) for arg in args[:event_count])
        for i in range(0, event_count):
            assert args[i].exe_path_as_id == test_events[i].exe_path, "Exe path didn't make it to one of it's destinations"
            assert args[i].program_name == test_events[i].window_title, "Window title's end result didn't look right"
        
        assert logger_add_new_item_spy.call_count == len(test_events)
        
        args, _ = summary_add_new_item_spy.call_args    
        assert all(isinstance(arg, ProgramSummaryLog) for arg in args[:event_count])
        for i in range(0, event_count):
            assert args[i].exe_path_as_id == test_events[i].exe_path, "Exe path didn't make it to one of it's destinations"
            assert args[i].process_name == test_events[i].process_name
            assert args[i].program_name == test_events[i].window_title, "Window title's end result didn't look right"

        # TODO:
        # TODO: Cook it so that push_window_ahead_ten_sec is called 2? 3x? for each dao type
        # TODO: Otherwise, the method isn't covered! 
        # TODO:
        # ## Assert that each session showed up as specified above, in the correct place
        
        # assert that they form a chain

        # assert that the alchemy layer was used as expected. Each of them.
        assert sum_dao_execute_and_read_one_or_none_spy.call_count == event_count
        assert logging_dao_execute_and_read_one_or_none_spy.call_count == event_count
        
        assert summary_add_new_item_spy.call_count == event_count
        assert logger_add_new_item_spy.call_count == event_count

        assert finalize_log_spy.call_count == event_count
        assert update_item_spy.call_count == event_count

        assert finalize_log_spy.call_count == event_count
        assert update_item_spy.call_count == event_count

        # assert that process_name made it into where it belongs, and looked right
        # TODO: assert that detail looked right
    finally:
        # Run the cleanup
        await cleanup_test_resources(surveillance_manager)
