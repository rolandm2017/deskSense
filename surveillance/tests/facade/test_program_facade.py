import pytest
from unittest.mock import patch, MagicMock


from src.facade.program_facade import ProgramApiFacadeCore
from src.util.detect_os import OperatingSystemInfo


@pytest.mark.skipif(
    OperatingSystemInfo().is_windows,
    reason="Test only applicable on Ubuntu systems"
)
def test_program_facade_on_ubuntu():
    os_info = OperatingSystemInfo()
    facade = ProgramApiFacadeCore(os_info)

    program_info = facade._read_ubuntu()

    assert program_info["os"] == "Ubuntu"
    assert program_info["pid"] is not None
    assert program_info["process_name"] is not None
    assert program_info["window_title"] is not None


@pytest.mark.skipif(
    OperatingSystemInfo().is_ubuntu,
    reason="Test only applicable on Windows systems"
)
def test_program_facade_on_windows():
    os_info = OperatingSystemInfo()
    facade = ProgramApiFacadeCore(os_info)

    program_info = facade._read_windows()

    assert program_info["os"] == "Windows"
    assert program_info["pid"] is not None
    assert program_info["process_name"] is not None
    assert program_info["window_title"] is not None


real_program_responses = [
    # Visual Studio Code
    {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
     'window_title': 'program_tracker.py - deskSense - Visual Studio Code'},
    # Google Chrome
    {'os': 'Ubuntu', 'pid': 129614, 'process_name': 'chrome',
        'window_title': 'Squashing Commits with Git Rebase - Claude - Google Chrome'},
    {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
        'window_title': 'Vite + React + TS - Google Chrome'},
    {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
        'window_title': 'H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome'},

    # Alt-tab window
    {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
        'window_title': 'Alt-tab window'},
    {'os': 'Ubuntu', 'pid': 130117, 'process_name': 'code',
        'window_title': 'Alt-tab window'},
    {'os': 'Ubuntu', 'pid': None, 'process_name': None,
        'window_title': 'Alt-tab window'},

    # Terminal
    {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
        'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'},
    {'os': 'Ubuntu', 'pid': None, 'process_name': None,
        'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'}
]


def test_listen_for_window_changes():
    os_info = MagicMock()
    os_info.is_windows = False
    os_info.is_ubuntu = True

    facade = ProgramApiFacadeCore(os_info)

    mock_display = MagicMock()
    mock_root = MagicMock()
    mock_event = MagicMock()

    mock_display.Display.return_value = mock_display
    mock_display.screen.return_value.root = mock_root
    mock_display.next_event.return_value = mock_event
    mock_display.intern_atom.return_value = '_NET_ACTIVE_WINDOW'

    # Create X mock with required mask attributes
    mock_X = MagicMock()
    mock_X.FocusChangeMask = 1
    mock_X.PropertyChangeMask = 2
    mock_X.PropertyNotify = 'PropertyNotify'
    facade.X = mock_X

    mock_event.type = 'PropertyNotify'
    mock_event.atom = '_NET_ACTIVE_WINDOW'

    # Mock _read_ubuntu to return controlled values
    expected_window_info = {
        "os": "Ubuntu",
        "pid": 1234,
        "process_name": "test-process",
        "window_title": "Test Window"
    }

    with patch.object(facade, '_read_ubuntu', return_value=expected_window_info):
        with patch.object(facade, 'display', mock_display):
            # Get first yielded value from generator
            window_info = next(facade.listen_for_window_changes())

            assert window_info == expected_window_info
