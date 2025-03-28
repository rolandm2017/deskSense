import pytest

from src.object.arbiter_classes import InternalState, ChromeInternalState, ApplicationInternalState


class TestInternalState:
    def test_lacks_current_tab(self):
        state = InternalState("PyCharm", False, {})

        assert not hasattr(
            state, 'current_tab'), "Internal state is not supposed to have a current tab"


class TestApplicationState:
    def test_lacks_current_tab(self):
        state = ApplicationInternalState("Postman", False, {})

        assert not hasattr(
            state, 'current_tab'), "Application state is not supposed to have a current tab"


class TestChromeState:
    def test_has_current_tab(self):
        state = ChromeInternalState("Google Chrome", True, "Claude.ai", {})

        assert hasattr(
            state, "current_tab"), "Chrome state did not have a current tab"
