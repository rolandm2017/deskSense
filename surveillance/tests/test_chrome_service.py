
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import os

from surveillance.src.object.pydantic_dto import TabChangeEvent
from surveillance.src.services.chrome_service import ChromeService

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
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the events.csv file
    events_csv_path = os.path.join(current_dir, "data", "events.csv")

    with open(events_csv_path, "r") as f:
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

    # Initialize ChromeService with the mocked DAOs
    chrome_service = ChromeService(dao=mock_dao, summary_dao=mock_summary_dao)

    # Return the initialized ChromeService instance
    return chrome_service


@pytest.mark.asyncio
async def test_add_arrival_to_queue(event_fixture, chrome_service_fixture):
    events_in_test = 8
    events = event_fixture[:events_in_test]

    assert len(
        chrome_service_fixture.message_queue) == 0, "Start circumstances defied requirements"

    for event in events:
        print(event, '59ru')
        await chrome_service_fixture.add_to_arrival_queue(event)

    assert len(chrome_service_fixture.message_queue) == events_in_test


@pytest.mark.asyncio
async def test_queue_with_debounce(event_fixture, chrome_service_fixture):
    num_in_first_batch = 4
    num_in_second_batch = 7

    # TODO: log_tab_event as a mock

    group1 = event_fixture[0:num_in_first_batch]
    group2 = event_fixture[num_in_first_batch:num_in_first_batch +
                           num_in_second_batch]

    with patch.object(chrome_service_fixture, 'log_tab_event', new_callable=AsyncMock) as mock_log_tab_event:
        for event in group1:
            await chrome_service_fixture.add_to_arrival_queue(event)

        assert len(chrome_service_fixture.message_queue) == num_in_first_batch

        # Wait for 1 second to let the debounce logic process the first batch
        await asyncio.sleep(1.1)

        assert mock_log_tab_event.await_count == num_in_first_batch

        for event in group2:
            await chrome_service_fixture.add_to_arrival_queue(event)

        assert len(chrome_service_fixture.message_queue) == num_in_second_batch

        # Wait another second to let the debounce logic process the second batch
        await asyncio.sleep(1.1)

        assert mock_log_tab_event.await_count == num_in_first_batch + num_in_second_batch


def is_chronological(array):
    if len(array) <= 1:
        return True

    for i in range(len(array) - 1):
        if array[i].startTime > array[i + 1].startTime:
            return False

    return True


def test_order_message_queue(event_fixture, chrome_service_fixture):
    start_of_events = 100
    selected_events = event_fixture[start_of_events:]

    # Verify events are NOT all in order.
    # Otherwise, the test is pointless!
    assert is_chronological(
        selected_events) is False, "Starting events need to be out of order chronologically"

    chrome_service_fixture.message_queue = selected_events  # Not necessarily in order
    assert len(
        chrome_service_fixture.ordered_messages) == 0, "Initial environment had a problem"

    # ### Act
    chrome_service_fixture.order_message_queue()

    # ### Assert
    output = chrome_service_fixture.ordered_messages

    for i in range(len(output) - 1):
        if output[i].startTime > output[i + 1].startTime:
            return False

    all_events_are_chronological = is_chronological(output)
    assert all_events_are_chronological, "Events were not chronological"
