import pytest
import signal
import threading
from unittest.mock import AsyncMock, Mock, MagicMock

from datetime import datetime, timedelta


from src.trackers.system_tracker import SystemPowerTracker
from surveillance.src.object.enums import SystemStatusType


# You can find out more about the signals by asking GPT.
# signal.SIGTERM
# signal.SIGINT
# signal.SIGHUP

def fake_on_shutdown():
    return 1


def test_signal_handling_ignores_multiple_requests(monkeypatch):
    on_shutdown = Mock()
    system_status_dao = AsyncMock()
    check_sys = Mock()

    obj = SystemPowerTracker(on_shutdown, system_status_dao, check_sys)

    # Monkeypatch the shutdown method to check if it's called
    called_signals = []
    called_reasons = []

    def fake_shutdown(signal_name, reason):
        called_signals.append(signal_name)
        called_reasons.append(reason)

    monkeypatch.setattr(obj, "_initiate_shutdown", fake_shutdown)

    # Send signals as if they were from the OS
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
        # after the first signal, _shutdown_in_progress = True
        obj._handle_shutdown_signal(sig, None)

    assert len(called_signals) == 1, "Expected exactly one signal to get through"
    assert len(called_reasons) == 1, "Expected exactly one reason to get through"


def test_signal_handling(monkeypatch):
    """
    Note that hot reload, Ctrl C, Shutdown are handled here. 
    Sleep is elsewhere.
    """
    on_shutdown = Mock()
    system_status_dao = AsyncMock()
    check_sys = Mock()

    obj = SystemPowerTracker(on_shutdown, system_status_dao, check_sys)

    # Monkeypatch the shutdown method to check if it's called
    called_signals = []
    called_reasons = []

    def fake_shutdown(signal_name, reason):
        called_reasons.append(reason)
        called_signals.append(signal_name)

    monkeypatch.setattr(obj, "_initiate_shutdown", fake_shutdown)

    # Send signals as if they were from the OS
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
        obj._handle_shutdown_signal(sig, None)
        obj._shutdown_in_progress = False  # Reset for testing

    assert called_reasons == ["restart program",
                              "Ctrl+C or Interrupt", "Terminal closed"]
    shutdown_signals = [SystemStatusType.HOT_RELOAD_STARTED,
                        SystemStatusType.CTRL_C_SIGNAL,
                        SystemStatusType.SHUTDOWN]  # Sleep handled elsewhere
    for i in range(0, len(shutdown_signals)):
        assert called_signals[i].name == shutdown_signals[i].name
