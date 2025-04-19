
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import asyncio
import os

from surveillance.src.object.pydantic_dto import TabChangeEvent
from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.services.chrome_service import TabQueue
from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.util.clock import SystemClock
from surveillance.src.debug.debug_overlay import Overlay
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.debug.ui_notifier import UINotifier

# Fixture to read and reconstruct events from the CSV file


@pytest.fixture
def event_fixture():
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
    print(events_csv_path, '34ru')

    with open(events_csv_path, "r", encoding="utf-8") as f:
        events = f.readlines()

        reconstructed = []
        for event in events:
            try:
                line = event.strip().split(",")
                t = datetime.fromisoformat(line[2])
                v = TabChangeEvent(tabTitle=line[0], url=line[1], startTime=t)
                reconstructed.append(v)
            except ValueError as e:
                line = event.strip().split(",")
                print(line)
                print(e)
        return reconstructed


@pytest.fixture
def chrome_service_fixture():
    # Mock the DAO dependencies
    mock_dao = AsyncMock()
    mock_summary_dao = AsyncMock()

    # chrome_summary_dao = AsyncMock()
    # program_summary_dao = AsyncMock()

    # Initialize ChromeService with the mocked DAOs
    overlay = Overlay()
    ui_layer = UINotifier(overlay)

    # recorder = ActivityRecorder(program_summary_dao, chrome_summary_dao)
    clock = SystemClock()
    arbiter = ActivityArbiter(
        clock)
    arbiter.add_ui_listener(ui_layer.on_state_changed)

    program_events = []
    chrome_events = []

    # Create mock listeners with side effects to record calls
    mock_program_listener = MagicMock()
    mock_program_listener.on_program_session_completed = AsyncMock(  # FIXME: This method no longer exists in the code
        side_effect=program_events.append)

    mock_chrome_listener = MagicMock()
    mock_chrome_listener.on_chrome_session_completed = AsyncMock(  # FIXME: This method no longer exists in the code
        side_effect=chrome_events.append)

    arbiter.add_summary_dao_listener(mock_program_listener)

    chrome_service = ChromeService(clock, arbiter)

    # Return the initialized ChromeService instance
    return chrome_service


@pytest.mark.asyncio
async def test_add_arrival_to_queue(event_fixture, chrome_service_fixture):
    events_in_test = 8
    events = event_fixture[:events_in_test]

    assert len(
        chrome_service_fixture.tab_queue.message_queue) == 0, "Start circumstances defied requirements"

    for event in events:
        await chrome_service_fixture.tab_queue.add_to_arrival_queue(event)

    assert len(chrome_service_fixture.tab_queue.message_queue) == events_in_test


@pytest.fixture
def chrome_service_with_mock():
    # Create a mock for log_tab_event
    mock_log_tab_event = AsyncMock()

    # Create mock dao
    mock_dao = AsyncMock()

    # Create a custom ChromeService that uses our mock
    class TestChromeService(ChromeService):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Replace the TabQueue with one that uses our mock
            self.tab_queue = TabQueue(mock_log_tab_event)

    # Create the test service
    service = TestChromeService(AsyncMock(), mock_dao)

    # Return both the service and the mock so we can make assertions
    return service, mock_log_tab_event


@pytest.mark.asyncio
async def test_queue_with_debounce(event_fixture, chrome_service_with_mock):
    service, mock_log_tab_event = chrome_service_with_mock

    num_in_first_batch = 4
    num_in_second_batch = 7

    group1 = event_fixture[0:num_in_first_batch]
    group2 = event_fixture[num_in_first_batch:num_in_first_batch +
                           num_in_second_batch]

    assert len(group1) == num_in_first_batch
    assert len(group2) == num_in_second_batch

    for event in group1:
        await service.tab_queue.add_to_arrival_queue(event)

    assert len(service.tab_queue.message_queue) == num_in_first_batch

    # Wait for debounce to complete
    await asyncio.sleep(0.7)

    # Verify the mock was called the expected number of times
    assert mock_log_tab_event.call_count == num_in_first_batch

    # Clean up any pending task
    if service.tab_queue.debounce_timer and not service.tab_queue.debounce_timer.done():
        service.tab_queue.debounce_timer.cancel()

    for event in group2:
        await service.tab_queue.add_to_arrival_queue(event)

    assert len(service.tab_queue.message_queue) == num_in_second_batch

    # Wait for debounce to complete
    await asyncio.sleep(0.7)

    # Verify the mock was called the expected number of times
    assert mock_log_tab_event.call_count == num_in_second_batch + num_in_first_batch

    # Clean up any pending task
    if service.tab_queue.debounce_timer and not service.tab_queue.debounce_timer.done():
        service.tab_queue.debounce_timer.cancel()


def is_chronological(array):
    if len(array) <= 1:
        return True

    for i in range(len(array) - 1):
        if array[i].startTime > array[i + 1].startTime:
            return False

    return True


@pytest.mark.asyncio
async def test_order_message_queue(event_fixture, chrome_service_fixture):
    start_of_events = 100
    selected_events = event_fixture[start_of_events:]

    # Verify events are NOT all in order.
    # Otherwise, the test is pointless!
    assert is_chronological(
        selected_events) is False, "Starting events need to be out of order chronologically"

    # Not necessarily in order
    chrome_service_fixture.tab_queue.message_queue = selected_events
    assert len(
        chrome_service_fixture.tab_queue.ordered_messages) == 0, "Initial environment had a problem"

    # ### Act
    chrome_service_fixture.tab_queue.order_message_queue()

    # ### Assert
    output = chrome_service_fixture.tab_queue.ordered_messages

    for i in range(len(output) - 1):
        if output[i].startTime > output[i + 1].startTime:
            return False

    all_events_are_chronological = is_chronological(output)
    assert all_events_are_chronological, "Events were not chronological"
