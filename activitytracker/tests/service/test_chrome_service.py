import copy
import os

import pytest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import asyncio

import pytz
from datetime import datetime, timedelta

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.debug.debug_overlay import Overlay
from activitytracker.debug.ui_notifier import UINotifier
from activitytracker.object.classes import TabChangeEventWithLtz
from activitytracker.object.pydantic_dto import UtcDtTabChange
from activitytracker.services.chrome_service import ChromeService, TabQueue
from activitytracker.util.clock import SystemClock

from ..helper.confirm_chronology import (
    assert_start_times_are_chronological,
    get_durations_from_test_data,
)
from ..helper.deepcopy_test_data import deepcopy_test_data
from ..mocks.mock_engine_container import MockEngineContainer

tokyo_tz = pytz.timezone("Asia/Tokyo")

# Fixture to read and reconstruct events from the CSV file

shorter_debounce = 0.15

# Safe to scope module because it doesn't mutate


@pytest.fixture(scope="module")
def reconstructed_tab_changes():
    #
    # Did you run out of test data?
    # You can generate new data by logging
    # @app.post("/chrome/tab" inputs
    # to a csv file for a few min
    # while you use Chrome.
    #
    # Get the directory of the current script
    # Get the current directory

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one level
    parent_dir = os.path.dirname(current_dir)

    # Construct the path to the events.csv file
    events_csv_path = os.path.join(parent_dir, "data", "events.csv")
    print(events_csv_path, "34ru")

    reconstructed = []
    with open(events_csv_path, "r", encoding="utf-8") as f:
        events = f.readlines()

        for event in events:
            try:
                line = event.strip().split(",")
                dt_of_start_time = datetime.fromisoformat(line[2])
                tab_change_event = TabChangeEventWithLtz(
                    tab_title=line[0], url=line[1], start_time_with_tz=dt_of_start_time
                )
                reconstructed.append(tab_change_event)
            except ValueError as e:
                line = event.strip().split(",")
                print(line)
                print(e)
    return reconstructed


transience_for_test = 100


from typing import cast

from activitytracker.util.clock import UserFacingClock


@pytest.fixture
def chrome_service_fixture_with_arbiter(db_session_in_mem):
    # Initialize ChromeService with the mocked DAOs

    # recorder = ActivityRecorder(program_summary_dao, chrome_summary_dao)
    clock = SystemClock()
    threaded_container = MockEngineContainer([], 0.1)

    system_status_dao = SystemStatusDao(cast(UserFacingClock, clock), 10, db_session_in_mem)

    arbiter = ActivityArbiter(clock, system_status_dao, threaded_container)

    # Create mock listeners with side effects to record calls
    mock_program_listener = MagicMock()
    mock_program_listener.on_state_changed = None  # Isn't used?

    arbiter.add_recorder_listener(mock_program_listener)

    chrome_service = ChromeService(clock, arbiter, shorter_debounce, transience_for_test)

    # Return the initialized ChromeService instance
    return chrome_service


@pytest.fixture
def chrome_service_with_mock():
    # Create a mock for log_tab_event
    mock_log_tab_event = Mock()

    # Create mock dao
    mock_dao = AsyncMock()

    # Create a custom ChromeService that uses our mock

    class TestChromeService(ChromeService):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Replace the TabQueue with one that uses our mock
            self.tab_queue = TabQueue(mock_log_tab_event, shorter_debounce)

    # Create the test service
    service = TestChromeService(AsyncMock(), mock_dao)

    # Return both the service and the mock so we can make assertions
    return service, mock_log_tab_event


@pytest.mark.asyncio
async def test_add_arrival_to_queue(
    reconstructed_tab_changes, chrome_service_fixture_with_arbiter
):
    # NOTE: This test BREAKS if you remove async/await!

    events_in_test = 8
    # Sort before starting
    # Sort the reconstructed events by start_time_with_tz
    test_events = deepcopy_test_data(reconstructed_tab_changes[:events_in_test])

    # Arrange for the differences between their starttimes to be < transience delay (300ms)

    start_time = tokyo_tz.localize(datetime(2025, 4, 15, 1, 0, 0))
    for i in range(0, events_in_test):
        updated_start = start_time + timedelta(milliseconds=i * transience_for_test)
        test_events[i].start_time_with_tz = updated_start

    # Arrange spies
    # Set up spies - ONLY ONE SPY PER METHOD
    with mock.patch.object(
        chrome_service_fixture_with_arbiter.tab_queue,
        "add_to_arrival_queue",
        wraps=chrome_service_fixture_with_arbiter.tab_queue.add_to_arrival_queue,
    ) as add_to_arrival_queue_spy, mock.patch.object(
        chrome_service_fixture_with_arbiter.tab_queue,
        "order_message_queue",
        wraps=chrome_service_fixture_with_arbiter.tab_queue.order_message_queue,
    ) as order_message_queue_spy, mock.patch.object(
        chrome_service_fixture_with_arbiter.tab_queue,
        "remove_transient_tabs",
        wraps=chrome_service_fixture_with_arbiter.tab_queue.remove_transient_tabs,
    ) as remove_transient_tabs_spy, mock.patch.object(
        chrome_service_fixture_with_arbiter.tab_queue,
        "empty_queue_as_sessions",
        wraps=chrome_service_fixture_with_arbiter.tab_queue.empty_queue_as_sessions,
    ) as empty_queue_as_sessions_spy, mock.patch.object(
        chrome_service_fixture_with_arbiter,
        "log_tab_event",
        wraps=chrome_service_fixture_with_arbiter.log_tab_event,
    ) as log_tab_event_spy:

        # Verify empty queue to start
        assert len(chrome_service_fixture_with_arbiter.tab_queue.message_queue) == 0

        # Add events one by one and confirm they're added to the queue
        for index, event in enumerate(test_events):
            chrome_service_fixture_with_arbiter.tab_queue.add_to_arrival_queue(event)
            # Either the event is in the queue OR the queue was processed

        # Check either:
        # 1. Events are in the queue (if debounce hasn't fired yet)
        queue_length = len(chrome_service_fixture_with_arbiter.tab_queue.message_queue)
        if queue_length > 0:
            # If debounce hasn't fired, make sure all events were added
            assert queue_length == events_in_test
        else:
            # If debounce has fired, check that events were processed
            assert order_message_queue_spy.called
            assert remove_transient_tabs_spy.called
            assert empty_queue_as_sessions_spy.called

        # Wait for debounce to complete (if it hasn't already)
        await asyncio.sleep(shorter_debounce * 2.0)

        # Cancel any pending timers
        if (
            chrome_service_fixture_with_arbiter.tab_queue.debounce_timer
            and not chrome_service_fixture_with_arbiter.tab_queue.debounce_timer.done()
        ):
            chrome_service_fixture_with_arbiter.tab_queue.debounce_timer.cancel()

        # Now all events should have been processed
        assert add_to_arrival_queue_spy.call_count == events_in_test
        assert order_message_queue_spy.called
        assert remove_transient_tabs_spy.called
        assert empty_queue_as_sessions_spy.called

        # Queue should be empty after processing
        assert len(chrome_service_fixture_with_arbiter.tab_queue.message_queue) == 0

        # If there are no transient tabs, log_tab_event should be called for each event
        # Otherwise, it will be called fewer times
        assert log_tab_event_spy.call_count <= events_in_test


@pytest.mark.asyncio
async def test_debounce_process(reconstructed_tab_changes, db_session_in_mem):
    # NOTE: This test BREAKS if you remove async/await!

    # You must set everything back up here, because it uses a specific ms delay for debounce

    very_short_debounce = 0.25
    local_transience_ms = 20  # get a transience threshold under the deboucne

    # recorder = ActivityRecorder(program_summary_dao, chrome_summary_dao)
    clock = SystemClock()
    threaded_container = MockEngineContainer([], 0.1)

    system_status_dao = SystemStatusDao(cast(UserFacingClock, clock), 10, db_session_in_mem)

    arbiter = ActivityArbiter(clock, system_status_dao, threaded_container)

    # Create mock listeners with side effects to record calls
    mock_program_listener = MagicMock()
    mock_program_listener.on_state_changed = None  # Isn't used

    arbiter.add_recorder_listener(mock_program_listener)

    chrome_service = ChromeService(clock, arbiter, very_short_debounce, local_transience_ms)

    # Arrange spies

    log_tab_event_spy = Mock(side_effect=chrome_service.tab_queue.log_tab_event)
    chrome_service.tab_queue.log_tab_event = log_tab_event_spy

    events_in_test = 8

    # Sort before starting
    # Sort the reconstructed events by start_time_with_tz
    test_events = deepcopy_test_data(reconstructed_tab_changes[:events_in_test])

    # Arrange for the differences between their starttimes to be < transience delay (300ms)

    start_time = tokyo_tz.localize(datetime(2025, 4, 15, 1, 0, 0))
    for i in range(0, events_in_test):
        updated_start = start_time + timedelta(milliseconds=i * 50)  # 10, a very small value
        test_events[i].start_time_with_tz = updated_start

    # get the delays between events and make sure they're short enough to only trigger debounce one time
    print("check the delays")
    for i in range(0, len(test_events)):
        if i == len(test_events) - 2:
            break  # no next in chain
        next_stamp = test_events[i + 1].start_time_with_tz
        curr = test_events[i].start_time_with_tz
        print(next_stamp - curr)
        assert (next_stamp - curr).total_seconds() < very_short_debounce

    with mock.patch.object(
        chrome_service.tab_queue,
        "start_processing_msgs",
        wraps=chrome_service.tab_queue.start_processing_msgs,
    ) as debounce_start_processing_msgs_spy:

        assert (
            len(chrome_service.tab_queue.message_queue) == 0
        ), "Start circumstances defied requirements"
        for i, event in enumerate(test_events):

            chrome_service.tab_queue.add_to_arrival_queue(event)
            assert len(chrome_service.tab_queue.message_queue) == i + 1

            # Wait for the debounce timer to fire
        # Make sure to wait longer than your debounce delay
        await asyncio.sleep(very_short_debounce * 2)

        # Check if debounced_process was called
        assert debounce_start_processing_msgs_spy.called, "debounced_process was not called"
        assert (
            debounce_start_processing_msgs_spy.call_count == 1
        ), f"Expected debounced_process to be called once, but it was called {debounce_start_processing_msgs_spy.call_count} times"

        # Clean up any pending timers
        if (
            chrome_service.tab_queue.debounce_timer
            and not chrome_service.tab_queue.debounce_timer.done()
        ):
            chrome_service.tab_queue.debounce_timer.cancel()

        assert len(chrome_service.tab_queue.message_queue) == 0
        # You can test with very short duration tabs too
        assert log_tab_event_spy.call_count == events_in_test


@pytest.mark.asyncio
async def test_queue_with_debounce(reconstructed_tab_changes, chrome_service_with_mock):
    chrome_svc, mock_log_tab_event = chrome_service_with_mock
    print("\n")

    num_in_first_batch = 4
    num_in_second_batch = 7

    group1 = reconstructed_tab_changes[0:num_in_first_batch]
    group2 = reconstructed_tab_changes[
        num_in_first_batch : num_in_first_batch + num_in_second_batch
    ]

    assert len(group1) == num_in_first_batch
    assert len(group2) == num_in_second_batch

    for event in group1:
        # Act
        chrome_svc.tab_queue.add_to_arrival_queue(event)

    assert len(chrome_svc.tab_queue.message_queue) == num_in_first_batch

    # Wait for debounce to complete
    pause_for_debounce = 0.28
    assert (
        pause_for_debounce > shorter_debounce
    ), "Test is nonsense if the pausee isn't > the delay"
    await asyncio.sleep(pause_for_debounce)

    # Verify the mock was called the expected number of times
    assert mock_log_tab_event.call_count == num_in_first_batch

    # Clean up any pending task
    if (
        chrome_svc.tab_queue.debounce_timer
        and not chrome_svc.tab_queue.debounce_timer.done()
    ):
        chrome_svc.tab_queue.debounce_timer.cancel()

    for event in group2:
        # Act
        chrome_svc.tab_queue.add_to_arrival_queue(event)

    assert len(chrome_svc.tab_queue.message_queue) == num_in_second_batch

    # Wait for debounce to complete
    await asyncio.sleep(pause_for_debounce)

    # Verify the mock was called the expected number of times
    assert mock_log_tab_event.call_count == num_in_second_batch + num_in_first_batch

    # Clean up any pending task
    if (
        chrome_svc.tab_queue.debounce_timer
        and not chrome_svc.tab_queue.debounce_timer.done()
    ):
        chrome_svc.tab_queue.debounce_timer.cancel()


def is_chronological(array: list[TabChangeEventWithLtz]):
    if len(array) <= 1:
        return True

    for i in range(len(array) - 1):
        if array[i].start_time_with_tz > array[i + 1].start_time_with_tz:
            return False

    return True


@pytest.mark.asyncio
async def test_order_message_queue(
    reconstructed_tab_changes, chrome_service_fixture_with_arbiter
):

    start_of_events = 100
    selected_events = reconstructed_tab_changes[start_of_events:]

    # Verify events are NOT all in order.
    # Otherwise, the test is pointless!
    assert (
        is_chronological(selected_events) is False
    ), "Starting events need to be out of order chronologically"

    # Not necessarily in order
    chrome_service_fixture_with_arbiter.tab_queue.message_queue = selected_events
    assert (
        len(chrome_service_fixture_with_arbiter.tab_queue.ordered_messages) == 0
    ), "Initial environment had a problem"

    # ### Act
    chrome_service_fixture_with_arbiter.tab_queue.order_message_queue()

    # ### Assert
    output: list[TabChangeEventWithLtz] = (
        chrome_service_fixture_with_arbiter.tab_queue.ordered_messages
    )

    for i in range(len(output) - 1):
        if output[i].start_time_with_tz > output[i + 1].start_time_with_tz:
            return False

    all_events_are_chronological = is_chronological(output)

    assert all_events_are_chronological, "Events were not chronological"
