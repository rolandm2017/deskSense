# tests/integration/test_arbiter.py
import math

import pytest
from unittest.mock import MagicMock, Mock

from datetime import datetime, timedelta

from typing import cast

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.arbiter.session_polling import KeepAliveEngine
from activitytracker.config.definitions import keep_alive_cycle_length
from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.arbiter_sleep_events import (
    minutes_between_start_and_2nd_to_last,
    minutes_between_start_and_final_time_change,
    test_events_elapsed_time_in_sec,
    test_sleep_sessions,
    times_for_status_dao_clock,
    times_for_system_clock,
)
from ..helper.confirm_chronology import (
    assert_test_data_is_chronological_with_tz,
    get_durations_from_test_data,
)
from ..helper.copy_util import snapshot_obj_for_tests_with_ledger
from ..mocks.mock_clock import MockClock, UserLocalTimeMockClock
from ..mocks.mock_engine_container import MockEngineContainer

# ###
# ##
# #  -- Test the integrated arbiter with a series of somewhat realistic data.
# #  -- A series of test sessions is inserted.
# #  -- The Arbiter yields the expected time.
# ##
# ###


@pytest.fixture
def activity_arbiter_and_setup(db_session_in_mem):
    """
    Pytest fixture that returns a fresh ActivityArbiter instance for each test.
    Mocks the dependencies to avoid actual database or system interactions.
    """

    assert_test_data_is_chronological_with_tz(test_sleep_sessions)

    durations = get_durations_from_test_data(test_sleep_sessions)

    # Start by doing a deepcopy so integration test A doesn't influence integration test B
    copied_test_data = [snapshot_obj_for_tests_with_ledger(x) for x in test_sleep_sessions]

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

    threaded_container = MockEngineContainer(
        durations_as_int, ultrafast_interval_for_testing
    )
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
    recorder_spy.add_partial_window.side_effect = (
        lambda amount_used, session: session.ledger.extend_by_n(amount_used)
    )
    recorder_spy.add_ten_sec_to_end_time.side_effect = (
        lambda session: session.ledger.add_ten_sec()
    )

    status_dao_clock = UserLocalTimeMockClock(times_for_status_dao_clock)

    status_dao = SystemStatusDao(
        cast(UserFacingClock, status_dao_clock), 10, db_session_in_mem
    )

    # TODO: Cook status dao return values. Needs to be, a fixed say, four.
    # THEN, the run_polling_loop() adds a new one, about an hour after the prev.
    # AND the times need to come from the sessions, like, align with them.

    arbiter.add_recorder_listener(recorder_spy)
    arbiter.add_status_listener(status_dao)

    assert arbiter.activity_recorder == recorder_spy, "Test setup conditions failed"

    return arbiter, events, recorder_spy, copied_test_data, durations, status_dao


#
# TODO SO
# The situation is that the arbiter receives a session.
# The computer goes to sleep.
# The computer wakes up and enters a new session.
# I want to see that the Arbiter receives a Sleep alert
# from the Status DAO. The Arbiter flushes and resets.
# The old session is concluded at the right time, i.e. prior to sleep.
# The new session is received normally.
#


def test_arbiter_after_sleep(activity_arbiter_and_setup):
    arbiter = activity_arbiter_and_setup[0]
    events_from_on_state_changed_handler = activity_arbiter_and_setup[1]
    mock_activity_recorder = activity_arbiter_and_setup[2]
    sleep_test_events = activity_arbiter_and_setup[3]
    durations_between_events_from_setup = activity_arbiter_and_setup[4]
    status_dao = activity_arbiter_and_setup[5]

    """
    Cooking hard to organize the right SystemStatusDao events
    in the right order, at the right time.
    """

    arbiter.transition_state(sleep_test_events[0])
    arbiter.transition_state(sleep_test_events[1])
    arbiter.transition_state(sleep_test_events[2])

    # To put the post-sleep log into queue
    status_dao.run_polling_loop()

    arbiter.transition_state(sleep_test_events[3])
    arbiter.transition_state(sleep_test_events[4])
    arbiter.transition_state(sleep_test_events[5])

    event_three = events_from_on_state_changed_handler[2]
    event_four = events_from_on_state_changed_handler[3]

    def event_three_concluded_around_correct_time():
        """Checks that the event concluded at the time right before the gap"""
        return event_three.end_time == times_for_status_dao_clock[-2]

    def event_four_started_around_right_time():
        """Checks that the event started at it's stated start time"""
        return event_four.start_time == test_sleep_sessions[-1].start_time

    assert event_three_concluded_around_correct_time()
    assert event_four_started_around_right_time()

    def on_state_changed_saw_correct_times():
        """
        Is a big deal because it's here that a malformed end time
        would add huge time by mistake.
        """
        pass

    # --
    # -- Usual stuff:
    # --

    def events_all_made_it_to_on_new_session():
        pass

    def events_all_made_it_to_on_state_changed():
        pass

    assert events_all_made_it_to_on_new_session()
    assert events_all_made_it_to_on_state_changed()
