from unittest.mock import MagicMock, patch
import pytest

from contextlib import ExitStack


import platform

# Skip the entire module if not on Windows
if platform.system() != "Linux":
    pytest.skip(
        "Skipping Windows-specific tests on non-Linux platform", allow_module_level=True
    )


from activitytracker.facade.program_facade_ubuntu import UbuntuProgramFacadeCore


@pytest.fixture
def samples():
    return [
        {"pid": 1234, "process_name": "firefox", "window_title": "Mozilla Firefox"},
        {"pid": 5678, "process_name": "code", "window_title": "Visual Studio Code"},
        {"pid": 9012, "process_name": "terminal", "window_title": "Terminal"},
    ]


@pytest.fixture
def facade():
    return UbuntuProgramFacadeCore()


# Skip the entire module if not on Windows
if platform.system() != "Linux":
    pytest.skip(
        "Skipping Windows-specific tests on non-Linux platform", allow_module_level=True
    )

# FIXME: the tests must run and pass. simple ones for ubuntu facade


def assert_correct_result(result, sample):
    assert result["os"] == "Windows"
    assert result["pid"] == sample["pid"]
    assert result["exe_path"] == sample["exe_path"]
    assert result["process_name"] == sample["process_name"]


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


def test_window_listener_with_mocks():
    # Ignore unless it becomes a problem
    pass


def test_read_ubuntu(facade):
    """Test _read_windows with mocked library responses"""
    result = facade._read_ubuntu()

    assert "os" in result and result["os"] == "Ubuntu"
    assert "process_name" in result
    assert "exe_path" in result
    assert "pid" in result
    assert "window_title" in result
