# Suggest typing 'spaghetti,' 'noodle,' 'basketball'
import pytest
from unittest.mock import Mock, call
from pynput.keyboard import Key, KeyCode
import time

from src.facade.keyboard_facade import KeyboardApiFacade

@pytest.fixture
def keyboard(monkeypatch):
    """
    Modified fixture that doesn't use real listener or sleeps
    """
    kb = KeyboardApiFacade()
    # Mock the listener to avoid actual thread creation
    mock_listener = Mock()
    monkeypatch.setattr(kb, 'listener', mock_listener)
    return kb

def simulate_keypress(keyboard, char):
    """One char at a time"""
    # Simulate key press by directly calling the callback
    keyboard._on_press(KeyCode.from_char(char))
    time.sleep(0.02)  # Small delay to prevent events from getting lost

@pytest.mark.parametrize("key,expecting", [
    (22, 22),
    (25, 25),
    (30, 30)
])
def test_read_event(key, expecting):
    # Setup
    facade = KeyboardApiFacade()
    facade._on_press(key)
    # Act
    event = facade.read_event()
    assert event == expecting

@pytest.mark.parametrize("key,expecting", [
        (2, True),
        (3, True),
        (4, True),
        (None, False)
    ])
def test_event_is_key_down(keyboard, key, expecting):
    assert keyboard.event_type_is_key_down(key) == expecting


#
# #
# # # Complex tests
# #
#

@pytest.fixture
def mock_keyboard(monkeypatch):
    kb = KeyboardApiFacade()
    # Create a mock for the _on_press method
    mock_on_press = Mock()
    monkeypatch.setattr(kb, '_on_press', mock_on_press)
    return kb, mock_on_press
@pytest.mark.parametrize("test_word", [
    'food',
    'paint',
    'spaghetti',
])
def test_typing_words_with_stub(mock_keyboard, test_word):
    keyboard, mock_on_press = mock_keyboard
    for char in test_word:
        simulate_keypress(keyboard, char)
    
    # Verify that _on_press was called for each character
    expected_calls = [Mock(call(KeyCode.from_char(char))) for char in test_word]
    assert mock_on_press.call_count == len(test_word)
    
    # You can also verify the specific calls if needed
    actual_calls = mock_on_press.call_args_list
    for i, char in enumerate(test_word):
        assert actual_calls[i].args[0].char == char


@pytest.mark.parametrize("test_word", [
    'gong',
    'drum',
    'chime',
])
def test_keyboard_read_event(keyboard, test_word):
    events = []
    for char in test_word:
        simulate_keypress(keyboard, char)
        event = keyboard.read_event()
        events.append(event)

    expected_chars = list(test_word)
    assert len(expected_chars) == len(test_word)  # testing the test
    assert all(x is not None for x in events), "Array contains None values"

@pytest.mark.parametrize("test_word", [
    'spaghetti',
    'domino',
    'chemistry',
])
def test_typing_words(keyboard, test_word):
    events = []
    for char in test_word:
        simulate_keypress(keyboard, char)
        event = keyboard.read_event()
        events.append(event)

    received_chars = [event.char for event in events]
    expected_chars = list(test_word)
    
    assert all(x.isalpha() for x in received_chars), "Array contains non-alphabetical characters"        
    assert received_chars == expected_chars
    
    next_event = keyboard.read_event()
    assert next_event is None, "An unexpected event occurred"

def test_no_events_when_empty(keyboard):
    event = keyboard.read_event()
    assert event is None
    assert not keyboard.event_type_is_key_down(event)

# def test_event_clearing(keyboard):
#     simulate_typing(keyboard, 'a')
    
#     # First read should return the event
#     event1 = keyboard.read_event()
#     assert keyboard.event_type_is_key_down(event1)
#     assert event1.char == 'a'
    
#     # Second read should return None
#     event2 = keyboard.read_event()
#     assert event2 is None
#     assert not keyboard.event_type_is_key_down(event2)

# def test_special_keys(keyboard):
#     keyboard._on_press(Key.space)
#     event = keyboard.read_event()
#     assert keyboard.event_type_is_key_down(event)
#     assert event == Key.space

# def test_rapid_typing(keyboard):
#     test_word = 'fast'
#     # Type without delays
#     for char in test_word:
#         keyboard._on_press(KeyCode.from_char(char))
    
#     received_chars = []
#     for _ in range(len(test_word)):
#         event = keyboard.read_event()
#         assert keyboard.event_type_is_key_down(event)
#         received_chars.append(event.char)
    
#     assert received_chars == list(test_word)