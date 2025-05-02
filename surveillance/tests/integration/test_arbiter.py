# tests/integration/test_arbiter.py
import pytest
from unittest.mock import  Mock, MagicMock
from datetime import  timedelta, datetime
import math

from surveillance.src.config.definitions import keep_alive_cycle_length
from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.arbiter.session_polling import KeepAliveEngine

from surveillance.src.util.time_wrappers import UserLocalTime
from ..helper.copy_util import snapshot_obj_for_tests_with_ledger


from ..data.arbiter_events import test_sessions, minutes_between_start_and_2nd_to_last, test_events_elapsed_time_in_sec, times_for_system_clock, minutes_between_start_and_final_time_change 
from ..mocks.mock_clock import MockClock
from ..mocks.mock_engine_container import MockEngineContainer

from ..helper.confirm_chronology import assert_test_data_is_chronological_with_tz, get_durations_from_test_data

# ###
# ##
# #  -- Test the integrated arbiter with a series of somewhat realistic data.
# #  -- A series of test sessions is inserted. 
# #  -- The Arbiter yields the expected time.
# ##
# ###



@pytest.fixture
def activity_arbiter_and_setup():
    """
    Pytest fixture that returns a fresh ActivityArbiter instance for each test.
    Mocks the dependencies to avoid actual database or system interactions.
    """

    assert_test_data_is_chronological_with_tz(test_sessions)

    durations = get_durations_from_test_data(test_sessions)

    # Start by doing a deepcopy so integration test A doesn't influence integration test B
    copied_test_data = [snapshot_obj_for_tests_with_ledger(x) for x in test_sessions]

    # Mock dependencies
    clock = MockClock(times=times_for_system_clock)

    # Create mock UI components
    ui_layer = MagicMock()
    ui_layer.on_state_changed = Mock()

    # Create a new arbiter instance for this test
    ultrafast_interval_for_testing = 0.025  # usually is 1.0
    durations_as_int = [int(x) for x in durations]
    
    final_loop = 7  # keep it under 10 so there isn't a final pulse
    durations_as_int.append(final_loop)

    threaded_container = MockEngineContainer(durations_as_int, ultrafast_interval_for_testing)
    arbiter = ActivityArbiter(clock, threaded_container, KeepAliveEngine)

    # Add UI listener
    arbiter.add_ui_listener(ui_layer.on_state_changed)

    # Create an event log
    events = []

    def event_handler(session):
        events.append(session)

    # Create mock listeners with side effects to record calls

    # Use this pretty darn cool MagicMock(spec_set=whatever) thing
    recorder_spy = MagicMock(spec_set=ActivityRecorder)
    recorder_spy.on_state_changed.side_effect = event_handler
    recorder_spy.add_partial_window.side_effect = lambda amount_used, session: session.ledger.extend_by_n(amount_used)
    recorder_spy.add_ten_sec_to_end_time.side_effect = lambda session: session.ledger.add_ten_sec()

    arbiter.add_recorder_listener(recorder_spy)

    assert arbiter.activity_recorder == recorder_spy, "Test setup conditions failed"

    return arbiter, events, ui_layer, recorder_spy, copied_test_data, durations


def test_activity_arbiter(activity_arbiter_and_setup):
    arbiter = activity_arbiter_and_setup[0]
    events_from_on_state_changed_handler = activity_arbiter_and_setup[1]
    ui_layer = activity_arbiter_and_setup[2]
    mock_activity_recorder = activity_arbiter_and_setup[3]
    copied_test_data = activity_arbiter_and_setup[4]
    durations_between_events_from_setup = activity_arbiter_and_setup[5]

    # Setup: How much time should pass?
    expected_sum_of_time_in_sec = test_events_elapsed_time_in_sec
    program_sessions_in_test = [
        item for item in copied_test_data if isinstance(item, ProgramSession)]

    chrome_sessions_in_test = [
        item for item in copied_test_data if isinstance(item, ChromeSession)]
    
    # TODO: Get the test data durations and use it with a MockEngineContainer

    assert len(copied_test_data) > 0, "Test setup failed"

    # --
    # -- Act
    # --

    counter = 0
    # Recommend using "-v --capture=no" to see logging,
    # as in "pytest .\tests\integration\test_arbiter.py -v --capture=no"
    for session in copied_test_data:
        print(f"Loop iter {counter}")
        counter = counter + 1
        arbiter.transition_state(session)


    # --
    # -- Assert
    # --

    # ### ### Assert
    remaining_open_session_offset = 1

    # ### Test some basic assumptions

    program_events = [
            e for e in events_from_on_state_changed_handler if isinstance(e, ProgramSession)]
    chrome_events = [
            e for e in events_from_on_state_changed_handler if isinstance(e, ChromeSession)]

    def assert_basic_expectations_met():
        assert len(
            events_from_on_state_changed_handler) > 0, "Not even one event made it"

        assert all(isinstance(log, ProgramSession)
                for log in program_events), "A program event wasn't a program session"
        assert all(isinstance(log, ChromeSession)
                for log in chrome_events), "A Chrome event wasn't a Chrome session"

        # Because .duration is set in the ASM before on_state_changed:
        assert all(isinstance(obj.duration, timedelta)
                for obj in events_from_on_state_changed_handler)
        
    assert_basic_expectations_met()
    

    # ### Test DAO notifications
    def assert_recorder_worked_as_intended():
        assert mock_activity_recorder.on_state_changed.call_count == len(
            # NOTE: Would be "- 1" if the final input was a ProgramSession
            program_sessions_in_test) + len(chrome_sessions_in_test) - remaining_open_session_offset

    assert_recorder_worked_as_intended()

    def assert_names_match(session1, session2):
        try:
            if isinstance(session1, ProgramSession):
                assert session1.process_name == session2.process_name
                assert isinstance(session1, ProgramSession) and isinstance(session2, ProgramSession)
            else:
                assert isinstance(session1, ChromeSession) and isinstance(session2, ChromeSession)
                assert session1.domain == session2.domain
        except AssertionError:
            print(session1)
            print(session2)
            raise

    total_expected_calls = sum(math.floor(duration // 10) for duration in durations_between_events_from_setup)
    assert len(mock_activity_recorder.add_ten_sec_to_end_time.call_args_list) == total_expected_calls


    # assert number of conclude calls equals the num of sessions
    # assert the num of add_partial_window calls equals the num of sessions

    def assert_keep_alive_worked_as_intended():
        """
        Part of the challenge of these tests is confirming that 
        the KeepAlive DAO funcs were called as expected.
        The order depends greatly on what the test data says.
        """
        # Tally up the arguments from 
        end_of_prev_calls = 0
        for i in range(0, len(copied_test_data)):
            target_session = copied_test_data[i]
            final_duration = len(durations_between_events_from_setup) - 1
            if i > final_duration:
                # The session is never closed.
                session_from_spy = mock_activity_recorder.add_ten_sec_to_end_time.call_args_list[0][0][0]
                assert_names_match(session_from_spy, target_session)
                return  # Done
            expected_duration = durations_between_events_from_setup[i]

            corresponding_num_of_pushes = math.floor(expected_duration // 10)
            # Check that the window push spy saw that event that many times
            for j in range(end_of_prev_calls, corresponding_num_of_pushes + end_of_prev_calls):
                end_of_prev_calls += 1
                session_from_spy = mock_activity_recorder.add_ten_sec_to_end_time.call_args_list[j][0][0]
                assert_names_match(session_from_spy, target_session)
                assert session_from_spy.start_time.dt == target_session.start_time.dt

            # Check that the add parital window calls were as intended

            corresponding_addition = expected_duration % 10
            
            args = mock_activity_recorder.add_partial_window.call_args_list[i].args

            corresponding_addition_arg = args[0]  # First argument
            add_partial_window_session_arg = args[1]  # Second argument

            assert_names_match(add_partial_window_session_arg, target_session)
        
            # assert the sessions are actually the same
        
            assert corresponding_addition == corresponding_addition_arg
            assert isinstance(session.start_time.dt, datetime)
            assert isinstance(add_partial_window_session_arg.start_time.dt, datetime)

            t1 = target_session.start_time.dt
            t2 = add_partial_window_session_arg.start_time.dt
            assert t1.hour == t2.hour
            assert t1.minute == t2.minute
            assert t1.second == t2.second

            assert target_session.start_time.dt == add_partial_window_session_arg.start_time.dt

    assert_keep_alive_worked_as_intended()


    # Total number of recorded Program DAO entries was as expected
    assert len(program_events) == len(
        program_sessions_in_test), "A program session didn't make it through"
    # Total number of recorded Chrome DAO Entries was as expected
    remaining_open_session_offset = 1
    assert len(chrome_events) == len(
        chrome_sessions_in_test) - remaining_open_session_offset, "A Chrome session didn't make it through"

    # ### Test UI Notification layer
    # UI notifier was called the expected number of times
    assert ui_layer.on_state_changed.call_count == len(copied_test_data)

    # To get the total time elapsed, you can go thru the on_state_changed args
    # and sum up the start-to-start-to-start chain.
    # It's really just the final one's start time, versus the first one's start time.

    def assert_on_state_changed_recorded_correct_time():
        total = timedelta()
        for e in events_from_on_state_changed_handler:
            total = total + e.duration  # Counting the duration works too

        total_duration = total.total_seconds()

        assert expected_sum_of_time_in_sec == total_duration
        assert sum(durations_between_events_from_setup) == total_duration

    assert_on_state_changed_recorded_correct_time()

    # ### Check that sessions all received durations and end times
    assert all(
        log.end_time is not None for log in events_from_on_state_changed_handler), "An end time wasn't set"
    # FIXME: should also check that the duration is 10 sec despite the 0.1 sec pulse
    assert all(
        log.duration is not None for log in events_from_on_state_changed_handler), "A duration wasn't set"

    chronological = sorted(
        events_from_on_state_changed_handler, key=lambda obj: obj.start_time)

    # ### Assert the nth entry is concluded when the (n + 1)th entry starts

    for i in range(0, len(chronological)):
        is_last = i == len(chronological) - 1
        if is_last:
            break
        current = chronological[i]
        next = chronological[i + 1]
        duration_from_start_end_times = next.start_time - current.start_time
        assert current.end_time == next.start_time, "There was a misalignment in session start & end"
        assert current.duration == duration_from_start_end_times, "A duration did not calculate correctly"

    # Check that the Arbiter's test pulse did not
    # change the amount of time
    # in the sessions
    zero_index = 1
    
    events_from_handler_len = len(copied_test_data) - zero_index

    final_event_index = events_from_handler_len - 1

    assert len(events_from_on_state_changed_handler) == 13
    assert len(events_from_on_state_changed_handler) == events_from_handler_len

    # verify that copied_test_data[14] is still lodged in the Arbiter.
    # Note that you have to match up the index of the one that is still in the arbiter
    # with it's position in copied_test_data, while also accounting for zero index.
    # So as of this comment, the final test_session is number 14, meaning index 13, i.e. the final one.
    assert arbiter.state_machine.current_state.session.start_time == copied_test_data[
        len(copied_test_data) - 1].start_time
    
    # To get the total time elapsed, you can also count the number of window pushes,
    # minus all the deductions made. The number should be the same.

    sec_per_min = 60
    def assert_time_matches_in_on_state_changed():
        t0 = events_from_on_state_changed_handler[0].start_time
        t13 = events_from_on_state_changed_handler[final_event_index].start_time

        elapsed_time_in_test = (t13 - t0).total_seconds() / sec_per_min
        # it's "minutes btwn first session and 2nd to last" here because
        # the final sessionh, the very last, does not get into on_state_changed
        assert elapsed_time_in_test == minutes_between_start_and_2nd_to_last, f"The elapsed time was not as expected, perhaps due to interval pulse"

    assert_time_matches_in_on_state_changed()


    def assert_expected_values_match_ledger():
        """
        Verify each one using it's ledger. This is testing that 
        the session ledgers recorded the amount expected at the top of the test
        """
        for i in range(0, len(copied_test_data)):
            # check that the ledger says what you expect
            if i == len(copied_test_data) - 1:
                assert copied_test_data[i].ledger.get_total() == 0  # Claude, final session
                break
            ledger_total = copied_test_data[i].ledger.get_total()
            assert ledger_total == durations_between_events_from_setup[i]
            # assert verified_sessions[i].ledger.get_total() == actual_durations_in_logs[i]

    assert_expected_values_match_ledger()
    

    def assert_actual_values_match_ledger():
        """Verify each one using it's ledger."""
        for i in range(0, len(copied_test_data)):
            # check that the ledger says what you expect
            if i == len(copied_test_data) - 1:
                assert copied_test_data[i].ledger.get_total() == 0  # Claude, final session
                break
            ledger_total = copied_test_data[i].ledger.get_total()
            assert ledger_total == events_from_on_state_changed_handler[i].ledger.get_total()
            # assert verified_sessions[i].ledger.get_total() == actual_durations_in_logs[i]

    assert_actual_values_match_ledger()

    total_expected_partials = len(durations_between_events_from_setup)  # Because even 0 is a partial

    partials_tally = 0

    for i in range(0, total_expected_partials):
        args = mock_activity_recorder.add_partial_window.call_args_list[i].args

        corresponding_addition_arg = args[0]  # First argument

        partials_tally += corresponding_addition_arg  # Even 0

    amount_from_add_ten_sec = total_expected_calls * 10
    full_keep_alive_output = amount_from_add_ten_sec + partials_tally

    add_ten_calls_per_session = [math.floor(duration // 10) for duration in durations_between_events_from_setup]
    partial_for_session = [duration % 10 for duration in durations_between_events_from_setup]

    zips = []
    # create zips: ledger, keepAlive, expectedDuration pairs.
    print("zips:")
    print(len(add_ten_calls_per_session))
    for i in range(0, len(copied_test_data)):
        print(f"session {i + 1}")
        if i + 1 == len(copied_test_data):
            break
        if i + 1 == len(copied_test_data):
            print(durations_between_events_from_setup)
            expected_duration = 0
        else:
            expected_duration = int(durations_between_events_from_setup[i])
        ledger_amt = copied_test_data[i].ledger.get_total()
        keep_alive_tally = int(add_ten_calls_per_session[i] * 10 + partial_for_session[i])
        
        zip = (int(expected_duration), ledger_amt, int(keep_alive_tally))
        print(zip)
        assert ledger_amt == expected_duration, f"Failed on index {i} of {len(copied_test_data) - 1}"
        assert keep_alive_tally == expected_duration, f"Failed on index {i} of {len(copied_test_data) - 1}"

        zips.append(zip)



    def assert_time_matches_in_keep_alive():
        num_of_window_pushes = len(mock_activity_recorder.add_ten_sec_to_end_time.call_args_list)
        num_of_additions = len(mock_activity_recorder.add_partial_window.call_args_list)

        window_push_tally = 0

        # For each session, if the session made it to
        # the session would have on_new_session either window push, or add ten sec in start_session.
        # So we have to add ten sec per entry.

        # for i in range(0, len(copied_test_data)):
        #     keep_alive_tally_in_sec += from_on_new_session
        for i in range(0, num_of_window_pushes):
            # Don't bother with what went in there, just add the window duration
            window_push_tally += keep_alive_cycle_length
            # Verify there is something in it
            session = mock_activity_recorder.add_ten_sec_to_end_time.call_args_list[i][0][0]
            assert isinstance(session, ProgramSession) or isinstance(session, ChromeSession)

        assert window_push_tally == sum(add_ten_calls_per_session) * 10

        tally_from_partials = 0

        for j in range(0, num_of_additions):
            # get addition amt
            addition = mock_activity_recorder.add_partial_window.call_args_list[j].args[0]        
            if addition == 0:
                print("Zero addition")
            if addition == 10:
                raise ValueError("Addition of ten found")
                
            # assert duration > 0 and duration < 10
            # tally addition
            assert addition == partial_for_session[j]
            tally_from_partials += addition

        total = window_push_tally + tally_from_partials

        keep_alive_tally_in_minutes = total / sec_per_min

        assert keep_alive_tally_in_minutes == minutes_between_start_and_final_time_change

    assert_time_matches_in_keep_alive()