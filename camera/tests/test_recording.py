import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2

from camera.src.constants import CHOSEN_FPS
from camera.src.recording import initialize_new_vid, init_webcam, record_n_sec_video
from camera.debug import get_frame_timestamps, get_video_length


#
# #
# # # These tests proved to be misleading? Then:
# # # See https://claude.ai/chat/2247e129-5c73-4ee3-aa8f-424049a115b5
# #
#

@pytest.fixture
def mock_camera():
    """Fixture to provide a mocked camera that returns valid frames"""
    with patch('cv2.VideoCapture') as mock_cap:
        # Create a fake frame (black image)
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.return_value.read.return_value = (True, fake_frame)
        mock_cap.return_value.isOpened.return_value = True
        yield mock_cap


@pytest.fixture
def mock_video_writer():
    """Fixture to provide a mocked video writer"""
    with patch('cv2.VideoWriter') as mock_writer:
        mock_writer.return_value.isOpened.return_value = True
        yield mock_writer


def test_recording_three_sec(mock_camera, mock_video_writer):
    """Test recording a 3-second video"""
    # Setup
    out_file = "test_2_sec_vid.avi"
    vid_length_in_sec = 2
    out_dir = "test_videos/running/"

    # Act
    with patch('camera.src.startup_shutdown.sys.exit') as mock_exit:  # Prevent actual system exit
        vid_path = record_n_sec_video(vid_length_in_sec, out_file, out_dir)

    # Assert
    expected_frames = vid_length_in_sec * CHOSEN_FPS + 1
    assert mock_camera.return_value.read.call_count == expected_frames
    assert mock_video_writer.return_value.write.call_count == expected_frames


def test_recording_seven_sec(mock_camera, mock_video_writer):
    """Test recording a 7-second video"""
    # Setup
    out_file = "test_3_sec_vid.avi"
    vid_length_in_sec = 3
    out_dir = "test_videos/running/"

    # Act
    with patch('camera.src.startup_shutdown.sys.exit') as mock_exit:  # Prevent actual system exit
        vid_path = record_n_sec_video(vid_length_in_sec, out_file, out_dir)

    # Assert
    expected_frames = (vid_length_in_sec * CHOSEN_FPS) + 1
    assert mock_camera.return_value.read.call_count == expected_frames
    assert mock_video_writer.return_value.write.call_count == expected_frames
