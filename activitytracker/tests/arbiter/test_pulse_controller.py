from datetime import datetime

from activitytracker.arbiter.pulse_controller import PulseController
from activitytracker.object.classes import ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime


class SpyContainer:
    def __init__(self):
        self.calls = []
        self.engine = None

    def add_first_engine(self, engine):
        self.calls.append(("add_first_engine", engine))
        self.engine = engine

    def replace_engine(self, engine):
        self.calls.append(("replace_engine", engine))
        self.engine = engine

    def start(self):
        self.calls.append(("start",))

    def stop(self):
        self.calls.append(("stop",))


class FakeEngine:
    def __init__(self, session, recorder):
        self.session = session
        self.recorder = recorder


def make_session():
    return ProgramSession(
        "some/exe/path.exe",
        "path.exe",
        "Visual Studio Code",
        "myfile.py",
        UserLocalTime(datetime.now().astimezone()),
    )


def test_start_first_adds_and_starts_engine():
    container = SpyContainer()
    controller = PulseController(container, FakeEngine)

    session = make_session()
    controller.start_first(session)

    call_names = [c[0] for c in container.calls]
    assert call_names == ["add_first_engine", "start"]
    assert isinstance(container.calls[0][1], FakeEngine)
    assert container.calls[0][1].session is session


def test_replace_with_stops_replaces_and_starts():
    container = SpyContainer()
    controller = PulseController(container, FakeEngine)

    controller.start_first(make_session())
    container.calls.clear()

    controller.replace_with(make_session())

    call_names = [c[0] for c in container.calls]
    assert call_names == ["stop", "replace_engine", "start"]


def test_stop_stops_container():
    container = SpyContainer()
    controller = PulseController(container, FakeEngine)
    controller.start_first(make_session())
    container.calls.clear()

    controller.stop()

    assert [c[0] for c in container.calls] == ["stop"]


def test_engine_built_with_recorder_set_via_setter():
    container = SpyContainer()
    controller = PulseController(container, FakeEngine)
    recorder = object()
    controller.set_recorder(recorder)

    controller.start_first(make_session())

    assert container.calls[0][1].recorder is recorder


def test_engine_built_with_none_recorder_before_set():
    container = SpyContainer()
    controller = PulseController(container, FakeEngine)

    controller.start_first(make_session())

    assert container.calls[0][1].recorder is None
