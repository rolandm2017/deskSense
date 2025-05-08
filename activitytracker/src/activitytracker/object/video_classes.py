from abc import ABC, abstractmethod

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


class VideoContent(ABC):
    """Base class for all video sessions that should never be instantiated directly."""

    # Start time, end time exist on the container class
    player_state: PlayerState

    def __init__(self, player_state):
        self.player_state = player_state


class YouTubeContent(VideoContent):
    def __init__(self, channel_name, player_state) -> None:
        super().__init__(player_state)

        self.channel_name = channel_name


class NetflixContent(VideoContent):

    def __init__(self, title, player_state) -> None:
        super().__init__(player_state)
        self.title = title


class VlcContent(VideoContent):
    """For VLC Media Player"""

    def __init__(self, file, folder, player_state) -> None:
        super().__init__(player_state)
        self.file = file
        self.folder = folder
