from __future__ import annotations

from activitytracker.object.classes import ChromeSession, ProgramSession

from .session_polling import KeepAliveEngine, ThreadedEngineContainer


class PulseController:
    """Owns keep-alive engine construction and container lifecycle.

    The arbiter says *when* a session becomes active; this controller
    decides *how* the pulse thread reflects that.
    """

    def __init__(
        self,
        threaded_container: ThreadedEngineContainer,
        engine_class=KeepAliveEngine,
    ):
        self._container = threaded_container
        self._engine_class = engine_class
        self._recorder = None

    def set_recorder(self, recorder) -> None:
        self._recorder = recorder

    def start_first(self, session: ProgramSession | ChromeSession) -> None:
        engine = self._engine_class(session, self._recorder)
        self._container.add_first_engine(engine)
        self._container.start()

    def replace_with(self, session: ProgramSession | ChromeSession) -> None:
        self._container.stop()
        engine = self._engine_class(session, self._recorder)
        self._container.replace_engine(engine)
        self._container.start()

    def stop(self) -> None:
        self._container.stop()
