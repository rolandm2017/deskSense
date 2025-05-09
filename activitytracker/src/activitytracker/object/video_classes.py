from abc import ABC, abstractmethod

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


class VideoInfo(ABC):
    """Base class for all video sessions that should never be instantiated directly."""

    # Start time, end time exist on the container class
    player_state: PlayerState
    player_position_in_sec: int

    def __init__(self, player_state, player_position_in_sec):
        self.player_state = player_state
        self.player_position_in_sec = player_position_in_sec

    @abstractmethod
    def get_name(self):
        """Grab some identifying info"""
        pass


class YouTubeInfo(VideoInfo):
    def __init__(self, channel_name, player_state, player_position_in_sec) -> None:
        super().__init__(player_state, player_position_in_sec)

        self.channel_name = channel_name

    def get_name(self):
        return f"YouTube: {self.channel_name}"


class NetflixInfo(VideoInfo):

    def __init__(self, title, player_state, player_position_in_sec) -> None:
        super().__init__(player_state, player_position_in_sec)
        self.title = title

    def get_name(self):
        return f"Netflix: {self.title}"


class VlcInfo(VideoInfo):
    """For VLC Media Player"""

    def __init__(self, file, folder, player_state, player_position_in_sec) -> None:
        super().__init__(player_state, player_position_in_sec)
        self.file = file
        self.folder = folder

    def get_name(self):
        return f"VLC: {self.file}"

    def __str__(self) -> str:
        return (
            f"{self.file}, {self.folder}, {self.player_state}, {self.player_position_in_sec}"
        )
