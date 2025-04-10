from __future__ import annotations
from datetime import datetime, timedelta, timezone

import asyncio

from ..config.definitions import power_on_off_debug_file


from ..object.classes import ChromeSessionData, ProgramSessionData

from .activity_state_machine import ActivityStateMachine
from ..object.arbiter_classes import ChromeInternalState, ApplicationInternalState
from ..util.console_logger import ConsoleLogger

from .session_heartbeat import KeepAliveEngine, ThreadedEngineContainer


class RecordKeeperCore:
    def __init__(self):
        pass  # A name I might use


class ActivityArbiter:
    def __init__(self, user_facing_clock, pulse_interval=1, loop=None):
        """
        This class exists to prevent the Chrome Service from doing ANYTHING but reporting which tab is active.

        This class exists to prevent the Program Tracker from doing ANYTHING except reporting the active program.

        This way, the Chrome Service doesn't need to know if Chrome is active.
        i.e. "chrome_open_close_handler" before e22d5badb15

        This way, the Program Tracker doesn't need to track if
        the current program is Chrome & do such and such if it is or isn't.
        i.e. "chrome_event_update" and "self.current_is_chrome" before e22d5badb15
        """
        self.state_machine = ActivityStateMachine(user_facing_clock)
        self.pulse_interval = pulse_interval
        self.loop = loop or asyncio.get_event_loop()

        self.ui_update_listener = None
        self.activity_recorder = None
        self.logger = ConsoleLogger()

    def add_ui_listener(self, listener):
        self.ui_update_listener = listener

    def add_summary_dao_listener(self, listener):
        if hasattr(listener, "on_state_changed"):
            self.activity_recorder = listener
        else:
            raise AttributeError("Listener method was missing")

    def notify_display_update(self, state):
        if self.ui_update_listener:
            self.ui_update_listener(state)

    def notify_summary_dao(self, session):
        if self.activity_recorder:
            result = self.activity_recorder.on_state_changed(session)
            if asyncio.iscoroutine(result):
                self.loop.create_task(result)

    def notify_of_new_session(self, session):
        if self.activity_recorder:
            result = self.activity_recorder.on_new_session(session)
            if asyncio.iscoroutine(result):
                self.loop.create_task(result)

    def set_tab_state(self, tab: ChromeSessionData):
        self.transition_state(tab)

    def set_program_state(self, event: ProgramSessionData):
        self.transition_state(event)

    def transition_state(self, new_session: ChromeSessionData | ProgramSessionData):
        """
        If newly_active = Chrome, start a session for the current tab.
        When Chrome is closed, end the session for the current tab.

        When a program is opened, start a session for the program. And vice versa when it closes.
        """
        # print("\n" + "✦★✦" * 6 + " DEBUG " + "✦★✦" * 6 + "\n")
        if isinstance(new_session, ProgramSessionData):
            print("[Arb]", new_session.window_title)
        else:
            print("[Tab]", new_session.domain)
        assert not isinstance(new_session, dict), "Found an empty dictionary as session"
        self.notify_display_update(new_session)

        if self.state_machine.current_state:
            # ### Calculate the duration that the current state has existed
            # end_time & duration is set inside the ASM
            concluded_session = self.state_machine.current_state.session

            # ### Create the replacement state
            self.state_machine.set_new_session(new_session)

            # ### Start the first window
            self.notify_of_new_session(new_session)
     
            engine_loop = self.current_heartbeat.engine.save_loop_for_reuse()
            self.current_heartbeat.stop()  # stop the old one from prev loop
            print("in repeat loop")
            new_keep_alive_engine = KeepAliveEngine(new_session, self.activity_recorder, engine_loop)
            self.current_heartbeat = ThreadedEngineContainer(new_keep_alive_engine, self.pulse_interval)
            self.current_heartbeat.start()


            if self.state_machine.is_initialization_session(concluded_session):
                return
            # ### Put outgoing state into the DAO
            self.notify_summary_dao(concluded_session)
        else:
            if isinstance(new_session, ProgramSessionData):
                updated_state = ApplicationInternalState(
                    new_session.window_title, False,  new_session)
            else:
                updated_state = ChromeInternalState(
                    active_application="Chrome",
                    is_chrome=True,
                    current_tab=new_session.detail,
                    session=new_session
                )
            start_of_loop = asyncio.new_event_loop()
            print("in arbiter init")
            new_keep_alive_engine = KeepAliveEngine(new_session, self.activity_recorder, start_of_loop)
            self.current_heartbeat = ThreadedEngineContainer(new_keep_alive_engine, self.pulse_interval)
            self.current_heartbeat.start()
            self.state_machine.current_state = updated_state


    async def shutdown(self):
        """Concludes the current state/session without adding a new one"""
        if self.state_machine.current_state:
            concluded_session = self.state_machine.conclude_without_replacement()
            await self.notify_summary_dao(concluded_session, True)
            with open(power_on_off_debug_file, "a") as f:
                f.write("Shutdown Activity Arbiter\n")
