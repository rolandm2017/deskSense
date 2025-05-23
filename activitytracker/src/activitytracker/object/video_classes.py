from abc import ABC, abstractmethod

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


class VideoInfo(ABC):
    """Base class for all video sessions that should never be instantiated directly."""

    # Start time, end time exist on the container class
    video_id: str
    player_state: PlayerState
    # player_position_in_sec: int  # Don't care

    def __init__(self, video_id, player_state):
        self.video_id = video_id
        self.player_state = player_state
        # self.player_position_in_sec = player_position_in_sec

    @abstractmethod
    def get_name(self):
        """Grab some identifying info"""
        pass

    @abstractmethod
    def get_name_with_platform(self):
        pass

    @abstractmethod
    def get_platform_title(self):
        pass


class YouTubeInfo(VideoInfo):

    def __init__(
        self,
        video_id,
        player_state,
        channel_name,
    ) -> None:
        super().__init__(video_id, player_state)

        self.channel_name = channel_name

    def get_name(self):
        return f"{self.channel_name}"

    def get_name_with_platform(self):
        return f"YouTube Info: {self.channel_name}"

    def get_platform_title(self):
        return "YouTube"

    def __str__(self) -> str:
        return self.get_name()


class NetflixInfo(VideoInfo):

    def __init__(self, media_title, video_id, player_state) -> None:
        # The media title will be "Unknown Watch Page" until the user
        # sets the media title manually
        super().__init__(video_id, player_state)
        self.media_title = media_title

    def get_name(self):
        return f"{self.media_title}"

    def get_name_with_platform(self):
        return f"Netflix Info: {self.video_id}"

    def get_platform_title(self):
        return "Netflix"

    def __str__(self) -> str:
        return self.get_name()


class VlcInfo(VideoInfo):
    """For VLC Media Player"""

    def __init__(self, video_id, file, folder, player_state) -> None:
        # video_id is just the filename
        super().__init__(video_id, player_state)
        self.file = file
        self.folder = folder

    def get_name(self):
        return f"{self.file}"

    def get_name_with_platform(self):
        return f"VLC Info: {self.file}"

    def get_platform_title(self):
        return "VLC Media Player"

    def __str__(self) -> str:
        return f"{self.file}, {self.folder}, {self.player_state}"
