import pytest
from src.facade.program_facade import ProgramApiFacade
from src.util.detect_os import OperatingSystemInfo

@pytest.mark.skipif(
    OperatingSystemInfo().is_windows,
    reason="Test only applicable on Ubuntu systems"
)
def test_program_facade_on_ubuntu():
    os_info = OperatingSystemInfo()
    facade = ProgramApiFacade(os_info)

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
    facade = ProgramApiFacade(os_info)

    program_info = facade._read_windows()

    assert program_info["os"] == "Windows"
    assert program_info["pid"] is not None
    assert program_info["process_name"] is not None
    assert program_info["window_title"] is not None
