import pytest

from typing import cast

from surveillance.db.models import SummaryLogBase
from surveillance.object.classes import ProgramSession, ChromeSession
from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from surveillance.arbiter.activity_recorder import ActivityRecorder
from surveillance.util.const import SECONDS_PER_HOUR


from ..helper.confirm_chronology import (
    assert_test_data_is_chronological_with_tz, assert_start_times_are_chronological,
    get_durations_from_test_data, assert_all_start_times_precede_end_times
)

from ..helper.copy_util import snapshot_obj_for_tests_with_ledger
from ..helper.polling_util import count_full_loops
from ..helper.counting import get_total_in_sec, get_logs_total
from ..helper.truncation import truncate_summaries_and_logs_tables_via_session

from ..data.arbiter_events import test_sessions

# Intent: write dao layer ops all in a row, using the Recorder layer and manually crunched numbers.
# Compare the expected with the actual, using both just the summary DAOs and
# also some kind of audit function, that you may have to write.

# Literally go in almost by hand and do very simple loops to run the expected funcs.
# Then, go in with the read_all() methods to verify that the recorded time is accurate.

"""
You cannot use a Sqlite db for timezone related tests. 
Sqlite does not store tz info. Only pg does.
"""


@pytest.fixture
def setup_recorder_etc(regular_session_maker):

    program_logging_dao = ProgramLoggingDao(regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(regular_session_maker)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session_maker)

    recorder = ActivityRecorder(
        program_logging_dao, chrome_logging_dao, program_summary_dao, chrome_summary_dao, True)

    return {"program_logging": program_logging_dao, "chrome_logging": chrome_logging_dao,
            "program_summary": program_summary_dao, "chrome_summary": chrome_summary_dao,
            "recorder": recorder, "session_maker": regular_session_maker
            }


@pytest.fixture
def verified_data_with_durations():
    assert_test_data_is_chronological_with_tz(test_sessions)
    assert_all_start_times_precede_end_times(test_sessions)
    assert_start_times_are_chronological(test_sessions)

    # Start by doing a deepcopy so integration test A doesn't influence integration test B
    copied_test_data = [
        snapshot_obj_for_tests_with_ledger(x) for x in test_sessions]

    durations = get_durations_from_test_data(test_sessions)

    return copied_test_data, durations

# TODO: Migrate alembic
# TODO: Write very simple integration tests for DAOs confirming the name fields work and are the same across all models, equally present


def test_long_series_of_writes_yields_correct_final_times(setup_recorder_etc, verified_data_with_durations):
    verified_sessions, expected_durations = verified_data_with_durations

    counted_loops = [int(num // 10) for num in expected_durations]
    # for i in range(0, 14):
    #     print(counted_loops[i], expected_durations[i])

    # on_new_session does see final entry
    expected_on_new_sessions = len(verified_sessions)
    expected_add_ten_count = int(sum(counted_loops))
    # Final entry triggers a partial
    expected_partial_windows = len(expected_durations)
    expected_on_state_changed = len(
        verified_sessions) - 1  # Doesn't see final val

    durations_per_session_dict = {}

    # TODO: Verify the test's expected summary is what you think. full cycles + partials

    def get_session_key(session):
        """Create a unique key for each session based on name and start time"""
        return f"{session.get_name()}_{session.start_time.dt.isoformat()}"

    for i, session in enumerate(verified_sessions):
        session_key = get_session_key(session)
        if i == len(verified_sessions) - 2:  # Final entry has no duration
            durations_per_session_dict[session_key] = None
            break  # The duration doesn't exist
        durations_per_session_dict[session_key] = expected_durations[i]

    actual_on_new_sessions = 0
    actual_add_ten_count = 0
    actual_partial_windows = 0
    actual_on_state_changed = 0
    try:

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
                print(f"breaking on {current_session}")
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
                setup_recorder_etc["recorder"].add_ten_sec_to_end_time(
                    current_session)
            # Add in the partial window
            actual_partial_windows += 1
            calls_dict["add_partial"] += 1
            recorded_time += partial_window_time
            setup_recorder_etc["recorder"].add_partial_window(
                partial_window_time, current_session)

            # Finalize session
            next_session_start_time = verified_sessions[i + 1].start_time
            # print("current:",current_session)
            # print("next:",verified_sessions[i + 1])
            assert next_session_start_time.dt > current_session.start_time.dt
            completed_session = current_session.to_completed(
                next_session_start_time)

            actual_on_state_changed += 1
            calls_dict["state_changed"] += 1
            setup_recorder_etc["recorder"].on_state_changed(completed_session)
            actual_calls_dict[session_key] = calls_dict

            recorded_times.append(recorded_time)

        logs = []
        for session in verified_sessions:
            if isinstance(session, ProgramSession):
                log = setup_recorder_etc["program_logging"].find_session(
                    session)
                logs.append(log)
            else:
                log = setup_recorder_etc["chrome_logging"].find_session(
                    session)
                logs.append(log)

        actual_durations_in_logs = [log.duration_in_sec for log in logs]

        def assert_expected_values_match_ledger():
            """Verify each one using it's ledger."""
            for i in range(0, len(verified_sessions)):
                # check that the ledger says what you expect
                if i == len(verified_sessions) - 1:
                    # Claude, final session
                    assert verified_sessions[i].ledger.get_total() == 0
                    break
                ledger_total = verified_sessions[i].ledger.get_total()
                assert ledger_total == expected_durations[i]
                # assert verified_sessions[i].ledger.get_total() == actual_durations_in_logs[i]

        assert_expected_values_match_ledger()

        zips = []
        for i in range(0, len(verified_sessions)):
            zip = (actual_durations_in_logs[i],
                   verified_sessions[i].ledger.get_total())
            zips.append(zip)

        print("-- comparing zips -- ")

        for log_and_ledger in zips:
            print(log_and_ledger)
            assert log_and_ledger[0] == log_and_ledger[1]

        def assert_actual_logs_match_expected_durations():
            for i in range(0, len(verified_sessions)):
                current = verified_sessions[i]
                assert current.ledger.get_total(
                ) == actual_durations_in_logs[i]

        assert_actual_logs_match_expected_durations()

        # For each session, verify that it had the expected amount of time recorded

        def assert_that_writes_had_exact_expected_count():
            assert actual_on_new_sessions == expected_on_new_sessions
            assert actual_add_ten_count == expected_add_ten_count
            assert actual_partial_windows == expected_partial_windows
            assert actual_on_state_changed == expected_on_state_changed

        assert_that_writes_had_exact_expected_count()

        # --
        # --
        # --

        program_sums = setup_recorder_etc["program_summary"].read_all()
        domain_sums = setup_recorder_etc["chrome_summary"].read_all()

        # Create a tally to handle summing the sums
        tally_by_name = {}

        for summary in program_sums:
            name = summary.get_name()
            if name in tally_by_name:
                tally_by_name[name] += summary.hours_spent
            else:
                tally_by_name[name] = summary.hours_spent

        for summary in domain_sums:
            name = summary.get_name()
            if name in tally_by_name:
                tally_by_name[name] += summary.hours_spent
            else:
                tally_by_name[name] = summary.hours_spent

        total_sum = 0
        for key, hours_spent in tally_by_name.items():
            total_sum += hours_spent

        total_sum_from_db = total_sum * SECONDS_PER_HOUR

        # WHOO!
        # assert total_sum == sum(expected_durations)
        def assert_summary_db_falls_within_tolerance(expected_durations_arr):
            expected_total = sum(expected_durations_arr)
            tolerance = 0.02  # 5%
            lower_threshold = expected_total * (1 - tolerance)
            upper_bounds = expected_total * (1 + tolerance)

            assert lower_threshold < total_sum_from_db < upper_bounds

        assert_summary_db_falls_within_tolerance(expected_durations)

        program_logs = setup_recorder_etc["program_logging"].read_all()
        domain_logs = setup_recorder_etc["chrome_logging"].read_all()

        # Create a tally to handle summing the logs

        def assert_count_of_logs_is_right(program_logs, domain_logs, test_data_arr):
            """One log per test session"""
            # It isn't - 1 because the final test session is seen by on_new_session
            seen_session_count = len(test_data_arr)
            assert len(program_logs) + len(domain_logs) == seen_session_count

        assert_count_of_logs_is_right(
            program_logs, domain_logs, verified_sessions)

        logs_durations_tally_by_name = {}

        for log in program_logs + domain_logs:
            log: SummaryLogBase
            name = log.get_name()
            if name in logs_durations_tally_by_name:
                logs_durations_tally_by_name[name] += log.duration_in_sec
            else:
                logs_durations_tally_by_name[name] = log.duration_in_sec

        logs_total = 0
        for key, seconds_spent in logs_durations_tally_by_name.items():
            logs_total += seconds_spent

        assert logs_total == sum(expected_durations)

        # Even the end - start times work:

        logs_tally_start_end_times = {}
        v = 0

        max_duration_from_expectations = max(expected_durations)

        session_count = len(verified_sessions)
        bad_log_count = 0

        for log in program_logs + domain_logs:
            v += 1
            name = log.get_name()
            duration = (log.end_time - log.start_time).total_seconds()
            if duration > max_duration_from_expectations:
                bad_log_count += 1
                s = log.start_time.strftime("%H:%M")
                e = log.end_time.strftime("%H:%M")
            if name in logs_tally_start_end_times:
                logs_tally_start_end_times[name] += duration
            else:
                logs_tally_start_end_times[name] = duration

        print(f"{session_count}, {bad_log_count}")

        start_end_totals = 0
        for key, seconds_spent in logs_tally_start_end_times.items():
            start_end_totals += seconds_spent

        duration_sum = sum(expected_durations)
        tolerance = 0.03  # Roughly 10 sec from 550
        lower_bound = duration_sum * (1 - tolerance)
        upper_bound = duration_sum * (1 + tolerance)
        assert lower_bound < start_end_totals and start_end_totals < upper_bound

    finally:
        truncate_summaries_and_logs_tables_via_session(
            setup_recorder_etc["session_maker"])

    # TODO: Test that logs have the right start_time, end_time
