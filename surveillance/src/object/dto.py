from datetime import datetime



class KeystrokeDto:

    id: int
    timestamp: datetime
    def __init__(self, id, timestamp):
        self.id = id
        self.timestamp = timestamp

class MouseMoveDto:
    def __init__(self, id, start_time, end_time):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time


class ProgramDto:
    def __init__(self, id, window, start, end, productive):
        self.id = id
        self.window = window
        self.start_time = start
        self.end_time = end
        self.productive = productive
