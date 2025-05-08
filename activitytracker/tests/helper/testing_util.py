from activitytracker.config.definitions import keep_alive_cycle_length
from activitytracker.object.classes import ProgramSession, ProgramSessionDict

# TODO: Rename this to a very generic "util" or something


def count_full_loops(duration):
    """
    Counts the number of times window push is called in
    a KeepAliveEngine based on session duration.
    """
    return int(duration // keep_alive_cycle_length)


def convert_back_to_dict(session: ProgramSession, pid) -> ProgramSessionDict:
    return {
        "os": "Windows 11",
        "pid": pid,
        "exe_path": session.exe_path,
        "process_name": session.process_name,
        "window_title": session.detail + " - " + session.window_title,
    }
