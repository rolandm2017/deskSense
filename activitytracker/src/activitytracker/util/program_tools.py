separator_error_msg = "Error in function: window_title had no ' - '."

####
####
# Tools for the program_tracker to use.
####
####


def contains_space_dash_space(s):
    return " - " in s


def separate_window_name_and_detail(window_title):
    if not isinstance(window_title, str):
        raise TypeError("Input must be a string")
    return window_title.rsplit(" - ", 1)


def is_expected_shape_else_throw(shape):
    if not isinstance(shape, dict):
        raise TypeError("Expected dict, got " + type(shape).__name__)
    # PID is irrelevant
    compliant_shape = "os" in shape and "process_name" in shape and "window_title" in shape
    if not compliant_shape:
        print("os" in shape, "process_name" in shape, "window_title" in shape, shape)
        raise AttributeError("Uncompliant program window shape")
    return compliant_shape


def window_is_chrome(new_window: str | dict):
    if isinstance(new_window, str):
        return new_window.endswith("Google Chrome")
    else:
        # example: 'Fixing datetime.fromisoformat() error - Claude - Google Chrome'
        window_title = new_window["window_title"]
        return window_title.endswith("Google Chrome")


def tab_is_a_productive_tab(tab_name_to_check, productive_sites):
    """Checks if 'any of the productive sites substrings is present?' in the input tab"""
    return any(some_site in tab_name_to_check for some_site in productive_sites)


def is_productive(window_info, productive_apps, productive_sites):
    """Determine if the current window represents productive time."""
    title_with_detail = window_info["window_title"]

    detail, window_name = separate_window_name_and_detail(title_with_detail)

    # Check if it's a known application
    is_a_known_productive_program = window_name in productive_apps
    if is_a_known_productive_program:
        # Could still be a "Maybe" case, i.e. Chrome
        is_a_maybe_case = window_info["process_name"] == "Google Chrome"
        if is_a_maybe_case:
            # access window content to check the sites
            tab_name = detail
            is_productive_site = tab_is_a_productive_tab(tab_name, productive_sites)
            return is_productive_site
        return True

    return False
