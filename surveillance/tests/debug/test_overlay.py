# test_overlay.py
import pytest

from src.debug.debug_overlay import Overlay


def test_get_color_for_window():
    # Arrange
    overlay = Overlay()
    chrome = "Chrome"
    code = "Code"
    terminal = "Terminal"
    cinema_4d = "Cinema 4D"  # Not in color map

    # Act
    chrome_color = overlay.get_color_for_window(chrome)
    code_color = overlay.get_color_for_window(code)
    terminal_color = overlay.get_color_for_window(terminal)
    c4d_color = overlay.get_color_for_window(cinema_4d)

    # Assert
    assert chrome_color == overlay.color_map["Chrome"]
    assert code_color == overlay.color_map["Code"]
    assert terminal_color == overlay.color_map["Terminal"]
    assert c4d_color == overlay.default_color


def test_format_title():
    overlay = Overlay()

    terminal_pattern1 = "devil@hades: ~/Code"
    terminal_pattern2 = "zeus@olympus: /var/www/mysite.com"

    chrome_window = "Claude.ai - Google Chrome"
    chrome_window2 = "Stackoverflow.com - Google Chrome"

    vscode = "Visual Studio Code"
    vscode2 = "Visual Studio Code - myfile.py"

    plain_terminal = "Foo foo Terminal foo"

    long_val = "This doesn't match any condition"

    default = "foo bar baz"

    terminal_formatted_1 = overlay.format_title(terminal_pattern1)
    terminal_formatted_2 = overlay.format_title(terminal_pattern2)

    chrome1 = overlay.format_title(chrome_window)
    chrome2 = overlay.format_title(chrome_window2)

    just_vscode1 = overlay.format_title(vscode)
    just_vscode2 = overlay.format_title(vscode2)

    just_terminal = overlay.format_title(plain_terminal)

    truncated = overlay.format_title(long_val)

    default_response = overlay.format_title(default)

    assert terminal_formatted_1 == "devil@hades"
    assert terminal_formatted_2 == "zeus@olympus"

    assert chrome1 == "Chrome | Claude.ai"
    assert chrome2 == "Chrome | Stackoverflow.com"

    assert just_vscode1 == "VSCode"
    assert just_vscode2 == "VSCode"

    assert just_terminal == "Terminal"

    assert truncated == long_val[:27] + "..."

    assert default_response == default
