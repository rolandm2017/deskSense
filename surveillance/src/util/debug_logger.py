def write_to_debug_log(name, hours_spent, time):
    minutes_seconds = hours_to_minutes_seconds_ms(hours_spent)
    print("writing to debug log: " + str(minutes_seconds))
    with open("debug_logging.txt", "a") as f:
        f.write(f"{name} - {minutes_seconds} - {time}\n")


def hours_to_minutes_seconds_ms(hours):
    # Convert hours to total seconds and milliseconds
    total_seconds = hours * 3600  # 3600 seconds in an hour

    # Extract whole minutes and remaining seconds
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    # Extract milliseconds
    milliseconds = int((total_seconds % 1) * 1000)

    # Format as mm:ss:mmm
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"
