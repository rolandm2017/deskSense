separator_error_msg = "Error in function: window_title had no ' - '."


def separate_window_name_and_detail(window_title):
    if not isinstance(window_title, str):
        raise TypeError("Input must be a string")
    if " - " in window_title:
        return window_title.rsplit(" - ", 1)
    return separator_error_msg, window_title


def is_expected_shape_else_throw(dict):
    # PID is irrelevant
    compliant_shape = "os" in dict and "process_name" in dict and "window_title" in dict
    if not compliant_shape:
        raise AttributeError("Uncompliant program window shape")
    return compliant_shape


def window_is_chrome(new_window):
    # example: 'Fixing datetime.fromisoformat() error - Claude - Google Chrome'
    window_title = new_window["window_title"]
    return window_title.endswith('Google Chrome')


def tab_is_a_productive_tab(tab_name_to_check, productive_sites):
    """Checks if 'any of the productive sites substrings is present?' in the input tab"""
    return any(
        some_site in tab_name_to_check for some_site in productive_sites)
