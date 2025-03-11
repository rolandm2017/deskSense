from __future__ import annotations
from ast import Attribute
from datetime import datetime, timedelta, timezone
from typing import Optional
from enum import Enum

from ..object.classes import ChromeSessionData, ProgramSessionData
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao

from .activity_state_machine import ActivityStateMachine
from ..object.arbiter_classes import ChromeInternalState, ApplicationInternalState, InternalState


class RecordKeeperCore:
    def __init__(self):
        pass  # A name I might use


class ActivityArbiter:
    def __init__(self, user_facing_clock):
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

        self.ui_update_listener = None
        self.summary_listener = None

    def add_ui_listener(self, listener):
        self.ui_update_listener = listener

    def add_summary_dao_listener(self, listener):
        if hasattr(listener, "on_state_changed"):
            self.summary_listener = listener
        else:
            raise AttributeError("Listener method was missing")

    def notify_display_update(self, state):
        if self.ui_update_listener:
            self.ui_update_listener(state)

    async def notify_summary_dao(self, session):
        if self.summary_listener:
            await self.summary_listener.on_state_changed(session)

    async def set_tab_state(self, tab: ChromeSessionData):
        await self.transition_state(tab)

    async def set_program_state(self, event: ProgramSessionData):
        await self.transition_state(event)

    async def transition_state(self, new_session: ChromeSessionData | ProgramSessionData):
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
        self.notify_display_update(new_session)

        if self.state_machine.current_state:
            # ### Calculate the duration that the current state has existed
            # end_time & duration is set inside the ASM
            concluded_session = self.state_machine.current_state.session

            # Get the current state's session to put into the summary DAO along w/ the time
            # old_session.duration = now - old_session.start_time
            # old_session.end_time = now

            # ### Create the replacement state
            self.state_machine.set_new_session(new_session)

            # FIXME: The program is intended to handle Chrome separately from Programs.
            # FIXME: in other words, while Chrome and a tab is stored in the Chrome var,
            # FIXME: all that can stay maintained separately from whatever the Programs is doing.
            # if chrome_active:
            #     start_session_for_tab()
            # else:
            #     record_program_session()

            # if active_program.is_chrome:
            #     tab_session.resume()
            # else:
            #     tab_session.idle()

            # ### Put outgoing state into the DAO
            # FIXME: what is the point of this state business if the output state isn't used for these args?
            await self.notify_summary_dao(concluded_session)
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
            self.state_machine.current_state = updated_state\


    async def shutdown(self):
        """Concludes the current state/session without adding a new one"""
        if self.state_machine.current_state:
            concluded_session = self.state_machine.conclude_without_replacement()
            await self.notify_summary_dao(concluded_session)
