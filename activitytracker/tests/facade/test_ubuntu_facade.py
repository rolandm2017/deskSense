
from unittest.mock import MagicMock, patch
import pytest

import platform

# Skip the entire module if not on Windows
if platform.system() != "Linux":
    pytest.skip("Skipping Windows-specific tests on non-Linux platform",
                allow_module_level=True)


from activitytracker.facade.program_facade_ubuntu import UbuntuProgramFacadeCore


@pytest.fixture
def samples():
    return [
        {"pid": 1234, "process_name": "firefox",
            "window_title": "Mozilla Firefox"},
        {"pid": 5678, "process_name": "code", "window_title": "Visual Studio Code"},
        {"pid": 9012, "process_name": "terminal", "window_title": "Terminal"}
    ]


@pytest.fixture
def facade():
    return UbuntuProgramFacadeCore()


# Skip the entire module if not on Windows
if platform.system() != "Linux":
    pytest.skip("Skipping Windows-specific tests on non-Linux platform",
                allow_module_level=True)

# FIXME: the tests must run and pass. simple ones for ubuntu facade


def test_get_active_window_ubuntu(facade):
    result = facade._get_active_window_ubuntu()
    assert result is not None
    assert isinstance(result, dict)

    assert "window_title" in result
    assert "pid" in result
    assert "process_name" in result
    assert "exe_path" in result


def test_read_active_window_name_ubuntu(facade):
    result = facade._read_active_window_name_ubuntu()
    assert result is not None
    assert isinstance(result, str)
    assert "Code" in result
    assert "~/" in result


# def test_window_listener_with_mocks_ubuntu(facade, samples):
#     # Standard library patch instead of mocker.patch
#     with patch('activitytracker.facade.program_facade_ubuntu.psutil.process_iter') as mock_process_iter:
#         mock_process_iter.return_value = [
#             MagicMock(
#                 pid=s["pid"], name=lambda s=s: s["process_name"], status=lambda: "running")
#             for s in samples
#         ]

#         # Patch Xlib display with standard patch
#         with patch('activitytracker.facade.program_facade_ubuntu.display.Display') as mock_display_class:
#             mock_display_instance = MagicMock()
#             mock_display_class.return_value = mock_display_instance

#             mock_root = MagicMock()
#             mock_display_instance.screen.return_value.root = mock_root

#             # Fake Xlib constants
#             class FakeX:
#                 PropertyNotify = 1
#                 FocusChangeMask = 2
#                 PropertyChangeMask = 4
#                 AnyPropertyType = 0

#             facade.X = FakeX()
#             facade.display = mock_display_class

#             # Mock intern_atom
#             mock_display_instance.intern_atom.side_effect = lambda name: f"atom_{name}"

#             # Simulate X11 events
#             class FakeEvent:
#                 def __init__(self, atom):
#                     self.type = FakeX.PropertyNotify
#                     self.atom = atom

#             mock_display_instance.next_event.side_effect = [
#                 FakeEvent("atom__NET_ACTIVE_WINDOW"),
#                 FakeEvent("atom__NET_ACTIVE_WINDOW"),
#                 FakeEvent("atom__NET_ACTIVE_WINDOW"),
#             ]

#             # Simulate active window ID from root.get_full_property
#             mock_root.get_full_property.return_value.value = [1001]

#             # Mock get_full_property on window object to return encoded titles
#             fake_window = MagicMock()
#             fake_window.get_full_property.side_effect = [
#                 MagicMock(value=s["window_title"].encode()) for s in samples
#             ]
#             mock_display_instance.create_resource_object.return_value = fake_window

#             # Run the generator
#             gen = facade.listen_for_window_changes()
#             results = [next(gen) for _ in range(3)]

#             for result, sample in zip(results, samples):
#                 assert result['process_name'] == sample['process_name']
#                 assert result['window_title'] == sample['window_title']
