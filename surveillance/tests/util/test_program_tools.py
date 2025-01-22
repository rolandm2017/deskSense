import pytest

from src.config.definitions import productive_sites
from src.util.program_tools import separate_window_name_and_detail, is_expected_shape_else_throw, tab_is_a_productive_tab,  separator_error_msg, window_is_chrome


def test_separate_window_name_and_detail():
    chrome = "Google Chrome"

    window1 = "Squashing Commits with Git Rebase - Claude - Google Chrome"

    detail, title = separate_window_name_and_detail(window1)

    assert title == chrome
    assert detail == "Squashing Commits with Git Rebase - Claude"

    window3 = "H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome"

    detail, title = separate_window_name_and_detail(window3)

    assert title == chrome
    assert detail == "H&M | Online Fashion, Homeware & Kids Clothes | H&M CA"

    window4 = "Vite + React + TS - Google Chrome"
    detail, title = separate_window_name_and_detail(window4)
    assert title == chrome
    assert detail == "Vite + React + TS"

    window5 = "program_tracker.py - deskSense - Visual Studio Code"
    detail, title = separate_window_name_and_detail(window5)
    assert title == "Visual Studio Code"
    assert detail == "program_tracker.py - deskSense"

    window6 = "rlm@kingdom: ~/Code/deskSense/surveillance"
    response = separate_window_name_and_detail(window6)
    assert response[0] == window6
    assert len(response) == 1

    window7 = "Alt-tab window"
    response = separate_window_name_and_detail(window7)

    assert response[0] == window7
    assert len(response) == 1


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

    assert tab_is_a_productive_tab(
        productive_tab_name_1, productive_sites) is True
    assert tab_is_a_productive_tab(
        productive_tab_name_2, productive_sites) is True
    assert tab_is_a_productive_tab(
        productive_tab_name_3, productive_sites) is True

    assert tab_is_a_productive_tab(
        questionable_tab_name_4, productive_sites) is False
    assert tab_is_a_productive_tab(
        questionable_tab_name_5, productive_sites) is False
    assert tab_is_a_productive_tab(
        questionable_tab_name_6, productive_sites) is False


my_chrome_example = {'os': 'Ubuntu', 'pid': 129614, 'process_name': 'chrome',
                     'window_title': 'Squashing Commits with Git Rebase - Claude - Google Chrome'}


def test_window_is_chrome():
    assert window_is_chrome(my_chrome_example) is True
    assert window_is_chrome({"window_title": "foo bar baz"}) is False


ex1 = {'os': 'Ubuntu', 'pid': 129614, 'process_name': 'chrome',
       'window_title': 'Squashing Commits with Git Rebase - Claude - Google Chrome'}
ex2 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'Vite + React + TS - Google Chrome'}
ex3 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome'}
ex4 = {'os': 'Ubuntu', 'pid': 128216,
       'process_name': 'Xorg', 'window_title': 'Alt-tab window'}
ex5 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'}
ex6 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}


def test_is_expected_shape_else_throw():
    assert is_expected_shape_else_throw(ex1)
    assert is_expected_shape_else_throw(ex2)
    assert is_expected_shape_else_throw(ex3)
    assert is_expected_shape_else_throw(ex4)
    assert is_expected_shape_else_throw(ex5)
    assert is_expected_shape_else_throw(ex6)


def test_is_expected_shape_else_throw_actually_throws():

    with pytest.raises(AttributeError, match="Uncompliant program window shape"):
        # Call your function here that should raise the error
        is_expected_shape_else_throw({"foo": "bar"})

    with pytest.raises(AttributeError, match="Uncompliant program window shape"):
        # Call your function here that should raise the error
        is_expected_shape_else_throw({"james": "bond"})
