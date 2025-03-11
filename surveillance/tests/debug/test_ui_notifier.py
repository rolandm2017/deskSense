import pytest
from unittest.mock import Mock, MagicMock
import asyncio

from src.debug.ui_notifier import UINotifier
from src.object.arbiter_classes import ApplicationInternalState, ChromeInternalState
from src.object.classes import ProgramSessionData, ChromeSessionData


# Import or recreate your classes here
class OtherState:
    def __init__(self, domain):
        self.session = MagicMock()
        self.session.domain = domain


@pytest.fixture
def mock_overlay():
    """Fixture that creates a mock overlay with call tracking"""
    overlay = MagicMock()
    # Store calls in a list that we can inspect
    overlay.change_display_text.calls = []

    # Make the mock record all calls
    def record_call(text, color):
        overlay.change_display_text.calls.append(
            {"text": text, "color": color})

    overlay.change_display_text.side_effect = record_call
    return overlay


@pytest.fixture
def ui_notifier(mock_overlay):
    """Fixture that creates a UINotifier with the mock overlay"""
    return UINotifier(mock_overlay)


def test_internal_state_change(ui_notifier, mock_overlay):
    """Test that internal state changes update the overlay with the right text and color"""
    # Create a test state
    program_session = ProgramSessionData()
    program_session.window_title = "Test Window Title"
    test_state = ApplicationInternalState(
        "Test Window Title", False, program_session)

    # Trigger the state change
    ui_notifier.on_state_changed(test_state)

    # Check that change_display_text was called with the right arguments
    assert len(mock_overlay.change_display_text.calls) == 1
    call = mock_overlay.change_display_text.calls[0]
    assert call["text"] == "Test Window Title"
    assert call["color"] == "lime"


def test_other_state_change(ui_notifier, mock_overlay):
    """Test that other state changes update the overlay with domain and blue color"""
    # Create a test state

    chrome_session = ChromeSessionData()
    chrome_session.domain = "example.com"
    test_state = ChromeInternalState(
        "Chrome", True, "example.com", chrome_session)

    # Trigger the state change
    ui_notifier.on_state_changed(test_state)

    # Check that change_display_text was called with the right arguments
    assert len(mock_overlay.change_display_text.calls) == 1
    call = mock_overlay.change_display_text.calls[0]
    assert call["text"] == "example.com"
    assert call["color"] == "#4285F4"


def test_multiple_state_changes(ui_notifier, mock_overlay):
    """Test multiple state changes in sequence"""
    # Create test states
    program_session = ProgramSessionData()
    program_session.window_title = "Internal App"
    chrome_session = ChromeSessionData()
    chrome_session.domain = "test-domain.org"
    internal_state = ApplicationInternalState(
        "Internal App", True, program_session)
    other_state = ChromeInternalState(
        "Chrome", True, "test-domain.org", chrome_session)

    # Trigger state changes
    ui_notifier.on_state_changed(internal_state)
    ui_notifier.on_state_changed(other_state)
    ui_notifier.on_state_changed(internal_state)

    # Check that change_display_text was called the right number of times
    assert len(mock_overlay.change_display_text.calls) == 3

    # Check the first call
    assert mock_overlay.change_display_text.calls[0]["text"] == "Internal App"
    assert mock_overlay.change_display_text.calls[0]["color"] == "lime"

    # Check the second call
    assert mock_overlay.change_display_text.calls[1]["text"] == "test-domain.org"
    assert mock_overlay.change_display_text.calls[1]["color"] == "#4285F4"

    # Check the third call
    assert mock_overlay.change_display_text.calls[2]["text"] == "Internal App"
    assert mock_overlay.change_display_text.calls[2]["color"] == "lime"
