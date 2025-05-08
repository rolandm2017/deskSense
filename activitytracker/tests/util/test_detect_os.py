import pytest

from activitytracker.util.detect_os import OperatingSystemInfo


@pytest.mark.skipif(
    OperatingSystemInfo().is_windows == True,  # Use explicit comparison
    reason="Test only applicable on Ubuntu systems",
)
def test_is_ubuntu():
    os = OperatingSystemInfo()

    assert os.is_ubuntu
    assert not os.is_windows


@pytest.mark.skipif(
    OperatingSystemInfo().is_ubuntu == True,  # Use explicit comparison
    reason="Test only applicable on Ubuntu systems",
)
def test_is_windows():
    os = OperatingSystemInfo()

    assert os.is_windows
    assert not os.is_ubuntu
