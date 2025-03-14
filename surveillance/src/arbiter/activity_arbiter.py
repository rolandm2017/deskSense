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
        self.program_summary_listener = None
        self.chrome_summary_listener = None

    def add_ui_listener(self, listener):
        self.ui_update_listener = listener

    def add_program_summary_listener(self, listener):
        if hasattr(listener, "on_program_session_completed"):
            self.program_summary_listener = listener
        else:
            raise AttributeError("Listener method was missing")

    def add_chrome_summary_listener(self, listener):
        if hasattr(listener, "on_chrome_session_completed"):
            self.chrome_summary_listener = listener
        else:
            raise AttributeError("Listener method was missing")

    def notify_display_update(self, state):
        if self.ui_update_listener:
            self.ui_update_listener(state)

    async def notify_program_summary(self, program_session):
        if self.program_summary_listener:
            await self.program_summary_listener.on_program_session_completed(program_session)

    async def notify_chrome_summary(self, chrome_session):
        if self.chrome_summary_listener:
            await self.chrome_summary_listener.on_chrome_session_completed(chrome_session)

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
            updated_state = self.state_machine.set_new_session(new_session)

            # TODO: Handle case where current session was continued, i.e. by "return self"

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
            if isinstance(concluded_session, ChromeSessionData):
                # FIXME: [chrome summary dao] adding time  -1 day, 16:00:02.581249  to  localho
                # FIXME: chrome summary dao] adding time  -1 day, 16:00:03.879910  to  claude.ai
                await self.notify_chrome_summary(concluded_session)
            else:
                await self.notify_program_summary(concluded_session)
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
            self.state_machine.current_state = updated_state


# TODO: Test the state changes,
# TODO: Test the arbiter
# TODO: Test the overlay
