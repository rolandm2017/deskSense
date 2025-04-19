from surveillance.src.object.classes import ChromeSession, ProgramSession


def convert_start_end_times_to_hours(session: ProgramSession | ChromeSession):
    return (session.end_time - session.start_time).total_seconds() / 3600


def convert_duration_to_hours(session: ProgramSession | ChromeSession):
    return session.duration.total_seconds() / 3600.0
