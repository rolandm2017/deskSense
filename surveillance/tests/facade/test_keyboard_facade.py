import pytest
from unittest.mock import Mock, patch
from pynput.keyboard import Key, KeyCode
import signal
import os
from src.facade.keyboard_facade import KeyboardApiFacadeCore

@pytest.fixture
def keyboard_facade():
    return KeyboardApiFacadeCore()

@pytest.fixture
def mock_listener():
    with patch('pynput.keyboard.Listener', autospec=True) as mock:
        # Create a mock instance
        listener_instance = Mock()
        mock.return_value = listener_instance
        yield mock

def test_init(mock_listener):
    facade = KeyboardApiFacadeCore()
    assert facade.current_event is None
    mock_listener.assert_called_once()
    mock_listener.return_value.start.assert_called_once()

def test_read_event_returns_none_when_no_event(keyboard_facade):
    assert keyboard_facade.read_event() is None

def test_read_event_clears_current_event(keyboard_facade):
    # Setup
    test_key = KeyCode(char='a')
    keyboard_facade.current_event = test_key
    
    # First read should return event with empty char
    event = keyboard_facade.read_event()
    assert isinstance(event, KeyCode)
    assert event.char == ''

    test_key_2 = KeyCode("f")
    keyboard_facade.current_event = test_key_2

    # Second read should return event with empty char
    event = keyboard_facade.read_event()
    assert isinstance(event, KeyCode)
    assert event.char == ''
    
    # Third read should return None
    assert keyboard_facade.read_event() is None

def test_event_type_is_key_down(keyboard_facade):
    assert not keyboard_facade.event_type_is_key_down(None)
    assert keyboard_facade.event_type_is_key_down(KeyCode(char='a'))
    assert keyboard_facade.event_type_is_key_down(Key.ctrl)

def test_is_ctrl_c_with_regular_key(keyboard_facade):
    # Mock the listener's canonical method
    keyboard_facade.listener.canonical = Mock(return_value=KeyCode(char='a'))
    
    # Test with regular key press
    key = KeyCode(char='a')
    assert not keyboard_facade.is_ctrl_c(key)

def test_is_ctrl_c_with_ctrl_c(keyboard_facade):
    # Mock the listener's canonical method to return ctrl
    keyboard_facade.listener.canonical = Mock(return_value=Key.ctrl)
    
    # Test with Ctrl+C combination
    key = KeyCode(char='c')
    assert keyboard_facade.is_ctrl_c(key)

def test_is_ctrl_c_with_special_key(keyboard_facade):
    # Test with special key (like shift, alt, etc.)
    assert not keyboard_facade.is_ctrl_c(Key.shift)

@patch('os.kill')
def test_trigger_ctrl_c(mock_kill):
    facade = KeyboardApiFacadeCore()
    facade.trigger_ctrl_c()
    mock_kill.assert_called_once_with(os.getpid(), signal.SIGINT)

def test_on_press_handles_ctrl_c(keyboard_facade):
    # Mock trigger_ctrl_c method
    keyboard_facade.trigger_ctrl_c = Mock()
    
    # Mock the listener's canonical method to return ctrl
    keyboard_facade.listener.canonical = Mock(return_value=Key.ctrl)
    
    # Simulate Ctrl+C press
    key = KeyCode(char='c')
    keyboard_facade._on_press(key)
    
    # Verify trigger_ctrl_c was called
    keyboard_facade.trigger_ctrl_c.assert_called_once()

def test_on_press_updates_current_event(keyboard_facade):
    test_key = KeyCode(char='a')
    keyboard_facade._on_press(test_key)
    assert keyboard_facade.current_event == test_key