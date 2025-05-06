from surveillance.src.object.classes import ChromeSession, ProgramSession, CompletedChromeSession, CompletedProgramSession


def convert_start_end_times_to_hours(session: ProgramSession | ChromeSession):
    return (session.end_time - session.start_time).total_seconds() / 3600


def convert_duration_to_hours(session: CompletedProgramSession | CompletedChromeSession):
    return session.duration.total_seconds() / 3600.0


def group_logs_by_name(logs):
    grouped_logs = {}
    for log in logs:
        name = log.get_name()
        if name is None:
            print(name, log)
        if name not in grouped_logs:
            grouped_logs[name] = []
        grouped_logs[name].append(log)
    return grouped_logs
