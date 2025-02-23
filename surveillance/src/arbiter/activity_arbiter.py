from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from __future__ import annotations
import asyncio

from ..object.classes import ChromeSessionData, ProgramSessionData
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao

from ..util.program_tools import window_is_chrome


class ActivityType(Enum):
    CHROME = "chrome"
    PROGRAM = "program"
    IDLE = "idle"


class Activity:
    def __init__(self, start_time: datetime, is_productive, session):
        self.start_time = start_time
        self.is_productive = is_productive
        self.session = session

    def get_display_info(self):
        raise NotImplementedError

    def get_session_data(self):
        raise NotImplementedError


class ChromeActivity(Activity):
    def __init__(self, domain: str, tab_title: str, start_time: datetime, is_productive, session):
        super().__init__(start_time, is_productive, session)
        self.domain = domain
        self.tab_title = tab_title

    def get_display_info(self):
        return {
            "text": f"Chrome | {self.domain}",
            "color": "#4285F4"
        }


class ProgramActivity(Activity):
    def __init__(self, window_title: str, detail: str, start_time: datetime, is_productive, session):
        super().__init__(start_time, is_productive, session)
        self.window_title = window_title
        self.detail = detail

    def get_display_info(self):
        return {
            "text": self.window_title,
            "color": "lime"  # Could have a color map like the overlay
        }


class InternalState:
    def __init__(self, is_chrome, active_application, current_tab, session):
        self.active_application = active_application
        self.is_chrome = is_chrome
        self.current_tab = current_tab
        self.session = session

    def compute_next_state(self, next_state: Activity):
        raise NotImplementedError


class ApplicationInternalState(InternalState):
    def __init__(self):
        super().__init__()

    def compute_next_state(self, next_state: Activity):
        if isinstance(next_state, ProgramActivity):
            return self.change_to_new_program(next_state)
        else:
            return self.transit_to_chrome_state(next_state)

    def change_to_new_program(self, next: ProgramActivity):
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
                next.window_title, is_chrome, current_tab, next.session)
            return next_state

    def stay_on_same_program(self):
        return self  # No change needed

    def transit_to_chrome_state(self, next: ChromeActivity):
        # FIXME: What to do with the case where, where, there is a new Chrome opening?
        # A new tab opens at the same time as Chrome opens.
        # FIXME: What to do with, case where, a tab was suspended in the bg
        # while user ran VSCode, now he goes back to Claude?
        next_state = ChromeInternalState()
        return next_state


class ChromeInternalState(InternalState):
    def __init__(self):
        super().__init__()

    def compute_next_state(self, next_state: Activity):
        if isinstance(next_state, ProgramActivity):
            return self.handle_change_to_program(next_state)
        else:
            return self.handle_change_tabs(next_state)

    def handle_change_to_program(self, next_state: ProgramActivity):
        now_on_regular_app = not window_is_chrome(next_state.window_title)
        if now_on_regular_app:
            return self.change_to_new_program(next_state)
        else:
            return self.stay_on_chrome()  # Still on Chrome - Pass

    def handle_change_tabs(self, next_state: ChromeActivity):
        on_different_tab = self.current_domain != next_state.current_domain
        if on_different_tab:
            self.change_to_new_tab(next_state)
        else:
            self.stay_on_current_tab()

    def change_to_new_program(self, next: ProgramActivity):
        # TODO: How to implement changing the program?
        # Create a new state that is a Program state
        is_chrome = False
        current_tab = None  # should it be whatever is open in chrome? if Chrome is open
        next_state = ApplicationInternalState(
            next.window_title, is_chrome, current_tab, next.session)
        return next_state

    def stay_on_chrome(self):
        return self  # Explicitly stay the same

    def change_to_new_tab(self, next: ChromeActivity):
        active_application = "Chrome"
        next_state = ChromeInternalState(active_application,
                                         next.is_chrome, None, next.domain, next.session)
        return next_state

    def stay_on_current_tab(self):
        # Chrome, currentDomain -> Chrome, currentDomain
        # "Skip over" this state change.
        return self  # Explicitly keep the same object as state


# TODO: make ActivityArbiter into a singleton


class ActivityArbiter:
    def __init__(self, overlay, chrome_summary_dao: ChromeSummaryDao, program_summary_dao: ProgramSummaryDao):
        """
        This class exists to prevent the Chrome Service from doing ANYTHING but reporting which tab is active.

        This class exists to prevent the Program Tracker from doing ANYTHING except reporting the active program.

        This way, the Chrome Service doesn't need to know if Chrome is active. 
        i.e. "chrome_open_close_handler" before e22d5badb15

        This way, the Program Tracker doesn't need to track if 
        the current program is Chrome & do such and such if it is or isn't.
        i.e. "chrome_event_update" and "self.current_is_chrome" before e22d5badb15
        """
        self.current_program: Optional[ProgramActivity] = None
        self.tab_state: Optional[ChromeActivity] = None
        self.overlay = overlay
        self.chrome_summary_dao = chrome_summary_dao
        self.program_summary_dao = program_summary_dao

        self.current_state = None
        self.previous_state = None

    def set_tab_state(self, tab: ChromeSessionData):
        chrome_state = ChromeActivity(
            domain=tab.domain, tab_title=tab.detail, start_time=tab.start_time, is_productive=tab.productive)
        self._transition_state(chrome_state)

    def set_program_state(self, event: ProgramSessionData):
        program_state = ProgramActivity(
            window_title=event.window_title, detail=event.detail, start_time=event.start_time, is_productive=event.productive)
        self._transition_state(program_state)

    def create_new_internal_obj(self, next: Activity):
        if isinstance(next, ProgramActivity):
            # window title, detail, start time, is productive
            return ApplicationInternalState(next.window_title, next.detail, next.start_time, next.is_productive)
        else:
            # domain, tabtitle, start_time, is_productive
            return ChromeInternalState(next.domain, next.tab_title, next.start_time, next.is_productive)

    def _transition_state(self, new_activity: Activity):
        """
        If newly_active = Chrome, start a session for the current tab.
        When Chrome is closed, end the session for the current tab.

        When a program is opened, start a session for the program. And vice versa when it closes.
        """
        now = datetime.now()

        # Record the duration of the previous state
        if self.current_state:
            # ### Calculate the duration that the current state has existed
            duration = now - self.current_state.start_time

            # ### Get the current state's session to put into the summary DAO along w/ the time
            session = self.current_state.get_session_data()
            session.duration = duration

            # ### Create the replacement state
            updated_state = self.current_state.compute_next_state(new_activity)

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
            if isinstance(session, ChromeSessionData):
                self.chrome_summary_dao.create_if_new_else_update(
                    session)
            else:
                assert isinstance(
                    session, ProgramSessionData), "Was not a program session"
                self.program_summary_dao.create_if_new_else_update(
                    session)

        # Update the display
        display_info = updated_state.get_display_info()
        self.overlay.update_display(
            display_info["text"], display_info["color"])

        # Set new state
        self.current_state = updated_state
