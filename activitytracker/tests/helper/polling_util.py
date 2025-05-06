from activitytracker.config.definitions import keep_alive_cycle_length


def count_full_loops(duration):
    """
    Counts the number of times window push is called in 
    a KeepAliveEngine based on session duration.
    """
    return int(duration // keep_alive_cycle_length)
