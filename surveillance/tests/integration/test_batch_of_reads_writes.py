import pytest

from typing import cast

from surveillance.src.object.classes import ProgramSession, ChromeSession
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.src.db.models import DailyProgramSummary, ProgramSummaryLog
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.const import SECONDS_PER_HOUR

from ..helper.confirm_chronology import (
    assert_test_data_is_chronological_with_tz, assert_start_times_are_chronological,
    get_durations_from_test_data, assert_all_start_times_precede_end_times
)

from ..helper.polling_util import count_full_loops
from ..helper.counting import get_total_in_sec, get_logs_total

from ..data.arbiter_events import test_sessions, times_for_system_clock_as_ult

from ..mocks.mock_clock import MockClock, UserLocalTimeMockClock

# TODO: Import the arbiter_events.py file,
# write them all in a row, using the Recorder layer and manually crunched numbers.
# Compare the expected with the actual, using both just the summary DAOs and
# also some kind of audit function, that you may have to write.

# Literally go in almost by hand and do very simple loops to run the expected funcs.
# Then, go in with the read_all() methods to verify that the recorded time is accurate.



@pytest.fixture
def setup_recorder_etc(db_session_in_mem, mock_async_session_maker):
    
    program_logging_dao = ProgramLoggingDao(db_session_in_mem)
    chrome_logging_dao = ChromeLoggingDao(db_session_in_mem)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, db_session_in_mem, mock_async_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, db_session_in_mem, mock_async_session_maker)
    
    recorder = ActivityRecorder(program_logging_dao, chrome_logging_dao, program_summary_dao, chrome_summary_dao)
    
    return {"program_logging": program_logging_dao, "chrome_logging": chrome_logging_dao,
            "program_summary": program_summary_dao, "chrome_summary": chrome_summary_dao,
            "recorder": recorder
            }
    
@pytest.fixture
def verified_data_with_durations():
    assert_test_data_is_chronological_with_tz(test_sessions)
    assert_all_start_times_precede_end_times(test_sessions)
    assert_start_times_are_chronological(test_sessions)

    durations = get_durations_from_test_data(test_sessions)

    return test_sessions, durations


# TODO: Migrate alembic
# TODO: Write very simple integration tests for DAOs confirming the name fields work and are the same across all models, equally present


def test_long_series_of_writes_yields_correct_final_times(setup_recorder_etc, verified_data_with_durations):
    verified_sessions, expected_durations = verified_data_with_durations

    expected_on_new_sessions = len(verified_sessions)  # on_new_session does see final entry
    expected_add_ten_count = int(sum([num // 10 for num in expected_durations[:-1]]))  # Must remove final entry
    expected_partial_windows = len(expected_durations) - 1  # Must remove final entry
    expected_on_state_changed = len(verified_sessions) - 2  # Doesn't see final val OR the 2nd to last val

    durations_per_session_dict = {}


    # TODO: Verify the test's expected summary is what you think. full cycles + partials

    def get_session_key(session):
        """Create a unique key for each session based on name and start time"""
        return f"{session.get_name()}_{session.start_time.dt.isoformat()}"
    
    for i, session in enumerate(verified_sessions):
        session_key = get_session_key(session)
        if i == len(verified_sessions) - 2:
            durations_per_session_dict[session_key] = None
            break  # The duration doesn't exist
        durations_per_session_dict[session_key] = expected_durations[i]

    actual_on_new_sessions = 0
    actual_add_ten_count = 0
    actual_partial_windows = 0
    actual_on_state_changed = 0

    # So you can verify per instance
    actual_calls_dict = {}

    # Open all the sessions
    for i in range(0, len(verified_sessions)):
        actual_on_new_sessions += 1
        setup_recorder_etc["recorder"].on_new_session(verified_sessions[i])

    recorded_times = []
    # Write all the sessions with their expected times
    for i in range(0, len(verified_sessions)):
        current_session = verified_sessions[i]
        if i == len(verified_sessions) - 1:
            print(f"breaking on {current_session.get_name()}")
            break  # Do nothing with final session
        duration = expected_durations[i]
        total_cycles = count_full_loops(duration)
        partial_window_time = duration - (total_cycles * 10)

        recorded_time = 0

        session_key = get_session_key(session)
        calls_dict = {"add_ten": 0,
                      "add_partial": 0,
                      "state_changed": 0}

        for _ in range(0, total_cycles):
            actual_add_ten_count += 1
            calls_dict["add_ten"] += 1
            recorded_time += 10
            setup_recorder_etc["recorder"].add_ten_sec_to_end_time(current_session)
        # Add in the partial window
        actual_partial_windows += 1
        calls_dict["add_partial"] += 1
        recorded_time += partial_window_time
        setup_recorder_etc["recorder"].add_partial_window(partial_window_time, current_session)

        # Finalize session
        next_session_start_time = verified_sessions[i + 1].start_time
        # print("current:",current_session)
        # print("next:",verified_sessions[i + 1])
        assert next_session_start_time.dt > current_session.start_time.dt
        completed_session = current_session.to_completed(next_session_start_time)

        actual_on_state_changed += 1
        calls_dict["state_changed"] += 1
        setup_recorder_etc["recorder"].on_state_changed(completed_session)
        actual_calls_dict[session_key] = calls_dict

        recorded_times.append(recorded_time)


    logs = []
    for session in verified_sessions:
        if isinstance(session, ProgramSession):
            log = setup_recorder_etc["program_logging"].find_session(session)
            logs.append(log)
        else:
            log = setup_recorder_etc["chrome_logging"].find_session(session)
            logs.append(log)

    actual_durations_in_logs = [log.duration_in_sec for log in logs]

    count = []
    v = 0
    for i in actual_durations_in_logs:
        if i > 0:
            v += 1
            count.append(i)
        else:
            print(i)
    
    print(count, v, "162ru")

    def assert_expected_values_match_ledger():
        """Verify each one using it's ledger."""
        for i in range(0, len(verified_sessions)):
            # check that the ledger says what you expect
            if i == len(verified_sessions) - 1:
                assert verified_sessions[i].ledger.get_total() == 0  # Claude, final session
                break
            ledger_total = verified_sessions[i].ledger.get_total()
            assert ledger_total == expected_durations[i]
            # assert verified_sessions[i].ledger.get_total() == actual_durations_in_logs[i]

    assert_expected_values_match_ledger()

    zips = []
    for i in range(0, len(verified_sessions)):
        zip = (actual_durations_in_logs[i], verified_sessions[i].ledger.get_total())
        zips.append(zip)



    print("-- comparing zips -- ")

    for log_and_ledger in zips:
        print(log_and_ledger)
        assert log_and_ledger[0] == log_and_ledger[1]

    def assert_actual_logs_match_expected_durations():
        for i in range(0, len(verified_sessions)):
            current = verified_sessions[i]
            assert current.ledger.get_total() == actual_durations_in_logs[i]

    assert_actual_logs_match_expected_durations()

    # For each session, verify that it had the expected amount of time recorded
        
    def assert_that_writes_had_exact_expected_count():
        assert actual_on_new_sessions == expected_on_new_sessions
        assert actual_add_ten_count == expected_add_ten_count
        assert actual_partial_windows == expected_partial_windows
        assert actual_on_state_changed == expected_on_state_changed

    assert_that_writes_had_exact_expected_count()

    program_logs = setup_recorder_etc["program_logging"].read_all()
    domain_logs = setup_recorder_etc["chrome_logging"].read_all()

    def assert_count_of_logs_is_right(program_logs, domain_logs):
        """One log per entry"""
        # It isn't - 1 because the final test session is seen by on_new_session
        seen_session_count = len(test_sessions)  
        assert len(program_logs) + len(domain_logs) == seen_session_count

    assert_count_of_logs_is_right(program_logs, domain_logs)

    program_sums = setup_recorder_etc["program_summary"].read_all()
    domain_sums = setup_recorder_etc["chrome_summary"].read_all()

    def get_total_in_sec(item_name, verified_sessions, expected_durations):
        """Gets the durations that correspond to the arg's test_session positions"""
        chosen_indexes = []
        print("\n\n\n--\n158ru")
        print(item_name, "-- 158ru")
        for i in range(0, len(verified_sessions)):
            if i == len(verified_sessions) - 2:
                break  # Ignore the final entry
            print(verified_sessions[i].get_name(), "162ru")
            if verified_sessions[i].get_name() == item_name:
                chosen_indexes.append(i)
        # Turn the indexes into durations
        durations = []
        for index in chosen_indexes:
            durations.append(expected_durations[index])
        return sum(durations)

    def get_logs_total(item_name, logs_arr):
        relevant_picks = []
        for entry in logs_arr:
            if item_name == entry.get_name():
                relevant_picks.append(entry)
        total_time = sum([x.end_time - x.start_time for x in relevant_picks])
        return total_time
    
    actual_program_total_from_logs = 0
    actual_chrome_total_from_logs = 0

    for program in program_logs:
        actual_total = program.hours_spent * SECONDS_PER_HOUR
        expected_total = get_total_in_sec(program.get_name(), verified_sessions, expected_durations)
        assert actual_total == expected_total

        # Check it against the logs
        actual_program_total_from_logs: int = get_logs_total(program.get_name(), program_logs)

    for domain in domain_logs:
        actual_total = domain.hours_spent * SECONDS_PER_HOUR
        expected_total = get_total_in_sec(domain.get_name(), verified_sessions, expected_durations)
        assert actual_total == expected_total
        
        # Check it against the logs
        actual_chrome_total_from_logs: int = get_logs_total(domain.get_name(), domain_logs)

    assert actual_program_total_from_logs > 0
    assert actual_chrome_total_from_logs > 0
        
    logs_total = actual_program_total_from_logs + actual_chrome_total_from_logs

