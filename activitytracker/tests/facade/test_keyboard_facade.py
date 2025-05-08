import pytest
from unittest.mock import Mock, patch
from pynput.keyboard import Key, KeyCode
import signal
import os
from activitytracker.facade.keyboard_facade import KeyboardFacadeCore

# TODO: test mouse/keyboard facade


@pytest.fixture
def keyboard_facade():
    return KeyboardFacadeCore()


@pytest.fixture
def mock_listener():
    with patch("pynput.keyboard.Listener", autospec=True) as mock:
        # Create a mock instance
        listener_instance = Mock()
        mock.return_value = listener_instance
        yield mock


def test_read_event_returns_none_when_no_event(keyboard_facade):
    assert keyboard_facade.read_event() is None
