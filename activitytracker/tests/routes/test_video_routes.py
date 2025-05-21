# Import the route handler functions

import pytest
from unittest.mock import MagicMock, patch

from datetime import datetime, timezone

from activitytracker.object.classes import (
    PlayerStateChangeEventWithLtz,
    TabChangeEventWithLtz,
)
from activitytracker.object.enums import PlayerState
from activitytracker.object.pydantic_dto import (
    NetflixPlayerChange,
    NetflixTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
)
from activitytracker.routes.video_routes import (
    receive_netflix_player_state,
    receive_netflix_tab_change_event,
    receive_youtube_player_state,
    receive_youtube_tab_change_event,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.tiny_services import TimezoneService


class TestVideoRoutes:
    @pytest.fixture
    def mock_chrome_service(self):
        """Create a mock ChromeService that we can spy on"""
        mock_service = MagicMock(spec=ChromeService)
        mock_service.tab_queue = MagicMock()
        mock_service.tab_queue.add_to_arrival_queue = MagicMock()
        mock_service.log_player_state_event = MagicMock()
        return mock_service

    @pytest.fixture
    def timezone_service(self):
        """Use the real TimezoneService for integration testing"""
        return TimezoneService()

    @pytest.mark.asyncio
    async def test_receive_youtube_tab_change_event(
        self, mock_chrome_service, timezone_service
    ):
        # Create a valid YouTube tab change event with UTC timezone
        event = YouTubeTabChange(
            tabTitle="Test YouTube Video",
            url="https://www.youtube.com/watch?v=abcdef",
            startTime=datetime.now(timezone.utc),
            channel="TestChannel",
            playerState=PlayerState.PLAYING,
        )

        # Call the route handler directly
        result = await receive_youtube_tab_change_event(
            tab_change_event=event,
            chrome_service=mock_chrome_service,
            timezone_service=timezone_service,
        )

        # Verify the ChromeService was called correctly
        mock_chrome_service.tab_queue.add_to_arrival_queue.assert_called_once()
        # Check that the argument was a TabChangeEventWithLtz
        args, _ = mock_chrome_service.tab_queue.add_to_arrival_queue.call_args
        assert isinstance(args[0], TabChangeEventWithLtz)
        assert args[0].tab_title == "Test YouTube Video"
        assert args[0].youtube_info.channel_name == "TestChannel"
        assert args[0].youtube_info.player_state == PlayerState.PLAYING

        # Verify the response is None (which means 204 No Content)
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_youtube_player_state(self, mock_chrome_service, timezone_service):
        # Create a valid YouTube player state change event with UTC timezone
        event = YouTubePlayerChange(
            tabTitle="Test Video",
            channel="Elysse Davega",
            eventTime=datetime.now(timezone.utc),
            videoId="abcdef",
            playerState=PlayerState.PLAYING,
        )

        # Call the route handler directly
        result = await receive_youtube_player_state(
            tab_change_event=event,
            chrome_service=mock_chrome_service,
            timezone_service=timezone_service,
        )

        # Verify the ChromeService was called correctly
        mock_chrome_service.log_player_state_event.assert_called_once()
        # Check that the argument was a PlayerStateChangeEventWithLtz
        args, _ = mock_chrome_service.log_player_state_event.call_args
        assert isinstance(args[0], PlayerStateChangeEventWithLtz)
        assert args[0].youtube_info.player_state == PlayerState.PLAYING
        assert args[0].youtube_info.channel_name == "Elysse Davega"

        # Verify the response is None (which means 204 No Content)
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_netflix_event(self, mock_chrome_service, timezone_service):
        # Create a valid Netflix tab change event with UTC timezone
        event = NetflixTabChange(
            tabTitle="Unknown",
            url="https://www.netflix.com/watch/12345",
            startTime=datetime.now(timezone.utc),
            videoId="12345",
        )

        # Call the route handler directly
        result = await receive_netflix_tab_change_event(
            tab_change_event=event,
            chrome_service=mock_chrome_service,
            timezone_service=timezone_service,
        )

        # Verify the ChromeService was called correctly
        mock_chrome_service.tab_queue.add_to_arrival_queue.assert_called_once()
        # Check that the argument was a TabChangeEventWithLtz
        args, _ = mock_chrome_service.tab_queue.add_to_arrival_queue.call_args
        assert isinstance(args[0], TabChangeEventWithLtz)
        assert args[0].tab_title == "Unknown"
        assert args[0].netflix_info.video_id == "12345"

        # Verify the response is None (which means 204 No Content)
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_netflix_player_state(self, mock_chrome_service, timezone_service):
        # Create a valid Netflix player state change event with UTC timezone
        event = NetflixPlayerChange(
            tabTitle="Hilda Episode 1 - The Guardian",
            eventTime=datetime.now(timezone.utc),
            videoId="12345",
            showName="Test Show",
            playerState=PlayerState.PLAYING,
        )

        # Call the route handler directly
        result = await receive_netflix_player_state(
            tab_change_event=event,
            chrome_service=mock_chrome_service,
            timezone_service=timezone_service,
        )

        # Verify the ChromeService was called correctly
        mock_chrome_service.log_player_state_event.assert_called_once()
        # Check that the argument was a PlayerStateChangeEventWithLtz
        args, _ = mock_chrome_service.log_player_state_event.call_args
        assert isinstance(args[0], PlayerStateChangeEventWithLtz)
        assert args[0].tab_title == "Hilda Episode 1 - The Guardian"
        assert args[0].netflix_info.video_id == "12345"

        # Verify the response is None (which means 204 No Content)
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_utc_timezone_raises_error(
        self, mock_chrome_service, timezone_service
    ):
        # Create an event without UTC timezone info
        event = YouTubeTabChange(
            tabTitle="Test YouTube Video",
            url="https://www.youtube.com/watch?v=abcdef",
            startTime=datetime.now(),  # No timezone info
            channel="TestChannel",
            playerState=PlayerState.PAUSED,
        )

        # Test should raise HTTPException due to missing timezone
        with pytest.raises(
            Exception
        ):  # This could be MustHaveUtcTzInfoError or HTTPException
            await receive_youtube_tab_change_event(
                tab_change_event=event,
                chrome_service=mock_chrome_service,
                timezone_service=timezone_service,
            )
