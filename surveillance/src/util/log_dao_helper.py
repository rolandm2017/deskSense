from ..object.classes import ChromeSessionData, ProgramSessionData


def convert_start_end_times_to_hours(session: ProgramSessionData | ChromeSessionData):
     return (session.end_time - session.start_time).total_seconds() / 3600

def convert_duration_to_hours(session: ProgramSessionData | ChromeSessionData):
     return session.duration.total_seconds() / 3600.0