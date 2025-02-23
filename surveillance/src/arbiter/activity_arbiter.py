from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import asyncio

from ..object.classes import ChromeSessionData, ProgramSessionData
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao

from ..util.program_tools import window_is_chrome


class ActivityType(Enum):
    CHROME = "chrome"
    PROGRAM = "program"
    IDLE = "idle"


def get_program_display_info(window_title):
    return {
        "text": window_title,
        "color": "lime"  # Could have a color map like the overlay
    }


def get_chrome_display_info(domain):
    return {
        "text": f"Chrome | {domain}",
        "color": "#4285F4"
    }


def get_display_info(state):

    if isinstance(state, ChromeInternalState):
        print(state, "91ru")
        print(state.session)
        return get_chrome_display_info(state.session.domain)
    else:
        print(state, "96ru")
        print(state.session)
        return get_program_display_info(state.session.window_title)


class InternalState:
    def __init__(self, active_application, is_chrome, current_tab, session):
        self.active_application = active_application
        self.is_chrome = is_chrome
        self.current_tab = current_tab
        self.session = session

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        raise NotImplementedError


class ApplicationInternalState(InternalState):
    def __init__(self, active_application, is_chrome, current_tab, session):
        super().__init__(active_application, is_chrome, current_tab, session)

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        if isinstance(next_state, ProgramSessionData):
            return self.change_to_new_program(next_state)
        else:
            return self.transit_to_chrome_state(next_state)

    def change_to_new_program(self, next: ProgramSessionData):
        # TODO: If next state is the same program, return current state
        is_same_program = next.window_title == self.active_application
        if is_same_program:
            return self.stay_on_same_program()
        else:
            # Program A -> Program B, neither is Chrome
            # Create a new state that is on a different program
            is_chrome = False
            current_tab = None
            next_state = ApplicationInternalState(
                next.window_title, is_chrome, current_tab, next)
            return next_state

    def stay_on_same_program(self):
        return self  # No change needed

    def transit_to_chrome_state(self, next: ChromeSessionData):
        # FIXME: What to do with the case where, where, there is a new Chrome opening?
        # A new tab opens at the same time as Chrome opens.
        # FIXME: What to do with, case where, a tab was suspended in the bg
        # while user ran VSCode, now he goes back to Claude?
        next_state = ChromeInternalState()
        return next_state


class ChromeInternalState(InternalState):
    def __init__(self, active_application, is_chrome, current_tab, session):
        super().__init__(active_application, is_chrome, current_tab, session)

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        if isinstance(next_state, ProgramSessionData):
            return self.handle_change_to_program(next_state)
        else:
            return self.handle_change_tabs(next_state)

    def handle_change_to_program(self, next_state: ProgramSessionData):
        now_on_regular_app = not window_is_chrome(next_state.window_title)
        if now_on_regular_app:
            return self.change_to_new_program(next_state)
        else:
            return self.stay_on_chrome()  # Still on Chrome - Pass

    def handle_change_tabs(self, next_state: ChromeSessionData):
        on_different_tab = self.current_domain != next_state.current_domain
        if on_different_tab:
            self.change_to_new_tab(next_state)
        else:
            self.stay_on_current_tab()

    def change_to_new_program(self, next: ProgramSessionData):
        # TODO: How to implement changing the program?
        # Create a new state that is a Program state
        is_chrome = False
        current_tab = None  # should it be whatever is open in chrome? if Chrome is open
        next_state = ApplicationInternalState(
            next.window_title, is_chrome, current_tab, next.session)
        return next_state

    def stay_on_chrome(self):
        return self  # Explicitly stay the same

    def change_to_new_tab(self, next: ChromeSessionData):
        active_application = "Chrome"
        next_state = ChromeInternalState(active_application,
                                         next.is_chrome, None, next.domain, next.session)
        return next_state

    def stay_on_current_tab(self):
        # Chrome, currentDomain -> Chrome, currentDomain
        # "Skip over" this state change.
        return self  # Explicitly keep the same object as state


# TODO: make ActivityArbiter into a singleton
class RecordKeeperCore:
    def __init__(self):
        pass  # A name I might use


class OverallState:
    def __init__(self):
        self.program_state = None
        self.chrome_state = None


class ActivityArbiter:
    def __init__(self, overlay, chrome_summary_dao: ChromeSummaryDao = None, program_summary_dao: ProgramSummaryDao = None):
        """
        This class exists to prevent the Chrome Service from doing ANYTHING but reporting which tab is active.

        This class exists to prevent the Program Tracker from doing ANYTHING except reporting the active program.

        This way, the Chrome Service doesn't need to know if Chrome is active.
        i.e. "chrome_open_close_handler" before e22d5badb15

        This way, the Program Tracker doesn't need to track if
        the current program is Chrome & do such and such if it is or isn't.
        i.e. "chrome_event_update" and "self.current_is_chrome" before e22d5badb15
        """
        print("ActivityArbiter init starting")
        chrome_service.arbiter.on('tab_change', self._handle_tab_change)

        self.current_program: Optional[ProgramSessionData] = None
        self.tab_state: Optional[ChromeSessionData] = None
        self.overlay = overlay
        self.chrome_summary_dao = chrome_summary_dao
        self.program_summary_dao = program_summary_dao

        self.current_state = None
        self.program_state = None  # Holds a program
        self.chrome_state = None  # Holds a tab
        print("ActivityArbiter init complete")

    async def set_tab_state(self, tab: ChromeSessionData):
        print("Starting set_tab_state")
        try:
            print("HERE 227ru")
            await self._transition_state(tab)
        except Exception as e:
            print(f"Error in set_tab_state: {e}")

    async def set_program_state(self, event: ProgramSessionData):
        await self._transition_state(event)

    def update_overlay_display(self, updated_state: InternalState):
        if isinstance(updated_state, ApplicationInternalState):
            display_text = updated_state.session.window_title
            if display_text == "Alt-tab window":
                print("[LOG]: ", display_text)
            else:
                print("[log]", display_text)
            self.overlay.change_display_text(
                display_text, "lime")  # or whatever color
        else:
            display_text = f"Chrome | {updated_state.session.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")

    # TODO: Separate handling of program state and tab state.

    def update_overlay_display_with_session(self, session: ProgramSessionData | ChromeSessionData):
        print(session)
        if isinstance(session, ProgramSessionData):
            display_text = session.window_title
            if display_text == "Alt-tab window":
                print("[LOG]: ", display_text)
            else:
                print("[log]", display_text)
            self.overlay.change_display_text(
                display_text, "lime")  # or whatever color
        else:
            display_text = f"Chrome | {session.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")

    async def _transition_program(self, program_session):
        pass

    async def _transition_tab(self, chrome_session):
        pass

    async def _transition_state(self, new_session: ChromeSessionData | ProgramSessionData):
        """
        If newly_active = Chrome, start a session for the current tab.
        When Chrome is closed, end the session for the current tab.

        When a program is opened, start a session for the program. And vice versa when it closes.
        """
        now = datetime.now()
        print("\n" + "✦★✦" * 6 + " DEBUG " + "✦★✦" * 6 + "\n")

        if isinstance(new_session, ChromeSessionData):
            print(new_session.domain, "new domain in arbiter")
        else:
            print(new_session.window_title, "new app in arbiter")
        if isinstance(new_session, ProgramSessionData):
            print("[[arbiter]] ", new_session.window_title)
        else:
            print("[[ARB-tab]] ", new_session.domain)
        # print("gggggggggggggggg")
        self.update_overlay_display_with_session(new_session)

        # Record the duration of the previous state
        if self.current_state:
            # ### Calculate the duration that the current state has existed
            duration = now - self.current_state.session.start_time

            # ### Get the current state's session to put into the summary DAO along w/ the time
            old_session = self.current_state.session
            old_session.duration = duration

            temp = duration

            # ### Create the replacement state
            updated_state = self.current_state.compute_next_state(new_session)

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
            if isinstance(old_session, ChromeSessionData):
                await self.chrome_summary_dao.create_if_new_else_update(
                    old_session)
            else:
                assert isinstance(
                    old_session, ProgramSessionData), "Was not a program session"
                await self.program_summary_dao.create_if_new_else_update(
                    old_session)
        else:
            if isinstance(new_session, ProgramSessionData):
                updated_state = ApplicationInternalState(
                    new_session.window_title, False, None, new_session)
            else:
                updated_state = ChromeInternalState(
                    new_session.window_title, True, new_session.detail, new_session)

        # Update the display
        # if isinstance(updated_state, ApplicationInternalState):
        #     display_text = updated_state.session.window_title
        #     if display_text == "Alt-tab window":
        #         print("[LOG]: ", display_text, temp)
        #     else:
        #         print("[log]", display_text, temp)
        #     self.overlay.change_display_text(
        #         display_text, "lime")  # or whatever color
        # else:
        #     display_text = f"Chrome | {updated_state.session.domain}"
        #     self.overlay.change_display_text(display_text, "#4285F4")

        # Set new state
        self.current_state = updated_state

# TODO:
# TODO:
# TODO: Test the state changes,
# TODO: Test the arbiter
# TODO: Test the overlay
# TODO:
# TODO:
