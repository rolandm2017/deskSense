def get_total_in_sec(item_name, verified_sessions, expected_durations):
    """Gets the durations that correspond to the arg's test_session positions"""
    chosen_indexes = []
    for i in range(0, len(verified_sessions)):
        if i == len(verified_sessions) - 2:
            break  # Ignore the final entry
        if verified_sessions[i].get_name() == item_name:
            chosen_indexes.append(i)
    # Turn the indexes into durations
    durations = []
    for index in chosen_indexes:
        durations.append(expected_durations[index])
    return sum(durations)


def get_logs_total(item_name, logs_arr):
    relevant_picks = []
    for entry in logs_arr:
        if item_name == entry.get_name():
            relevant_picks.append(entry)
    total_time = sum([x.end_time - x.start_time for x in relevant_picks])
    return total_time
