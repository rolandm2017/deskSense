import pytest

from src.util.program_tools import separate_window_name_and_detail, is_expected_shape_else_throw, tab_is_a_productive_tab, separator_error_msg

window1 = "Squashing Commits with Git Rebase - Claude - Google Chrome"
window3 = "H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome"
window4 = "Vite + React + TS - Google Chrome"
window5 = "program_tracker.py - deskSense - Visual Studio Code"
window6 = "rlm@kingdom: ~/Code/deskSense/surveillance"
window7 = "Alt-tab window"


def test_separate_window_name_and_detail():
    chrome = "Google Chrome"

    detail, title = separate_window_name_and_detail(window1)

    assert title == chrome
    assert detail == "Squashing Commits with Git Rebase - Claude"

    detail, title = separate_window_name_and_detail(window3)

    assert title == chrome
    assert detail == "H&M | Online Fashion, Homeware & Kids Clothes | H&M CA"

    detail, title = separate_window_name_and_detail(window4)

    assert title == chrome
    assert detail == "Vite + React + TS"

    detail, title = separate_window_name_and_detail(window5)

    assert title == "Visual Studio Code"
    assert detail == "program_tracker.py - deskSense"

    detail, title = separate_window_name_and_detail(window6)

    assert detail == window6
    assert title == separator_error_msg

    detail, title = separate_window_name_and_detail(window7)

    assert detail == window7
    assert title == separator_error_msg


def test_tab_is_a_productive_tab_validation():
    # PRODUCTIVE
    productive_tab_name_1 = "www.github.com/sama"  # github.com is present
    productive_tab_name_2 = "https://stackoverflow.com/questions/455338/how-do-i-check-if-an-object-has-a-key-in-javascript"  # stackoverflow.com
    productive_tab_name_3 = "https://claude.ai/chat/db4a35ae-3b3c-4fae-a251-82c0bdc261f1"  # claude.ai

    # UNPRODUCTIVE
    questionable_tab_name_4 = "https://www.youtube.com/watch?v=vu4dsCtsocE"  # youtube
    questionable_tab_name_5 = "https://x.com/yacineMTB"  # twitter
    questionable_tab_name_6 = "https://www.tiktok.com/foryou?kref=vGWRdzLJnjYf&kuid=31b6d78a-c086-437f-9ab0-df56eaf7fd8b"  # Tiktok
    # clock = MockClock([datetime.now()])
    # facade = Mock()
    # tracker = ProgramTrackerCore(clock, facade, Mock())

    assert tab_is_a_productive_tab(productive_tab_name_1) is True
    assert tab_is_a_productive_tab(productive_tab_name_2) is True
    assert tab_is_a_productive_tab(productive_tab_name_3) is True

    assert tab_is_a_productive_tab(questionable_tab_name_4) is False
    assert tab_is_a_productive_tab(questionable_tab_name_5) is False
    assert tab_is_a_productive_tab(questionable_tab_name_6) is False
