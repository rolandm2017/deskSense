
import pytest
from unittest.mock import MagicMock, patch
from src.recording import record_n_sec_video, process_frame
from constants import CHOSEN_FPS

from ..src.recording import initialize_new_vid, init_webcam, record_n_sec_video
from ..debug import get_frame_timestamps, get_video_length
# TODO: test recording a 3 sec vid
# TODO: Test a 7 sec vid


@patch('cv2.VideoCapture')
@patch('cv2.VideoWriter')
def test_record_n_sec_video_stops_on_flag(mock_writer, mock_capture):
    # Setup mocks
    mock_capture.return_value.read.return_value = (True, MagicMock())
    mock_writer.return_value = MagicMock()

    # Counter for controlling the loop
    counter = 0

    def should_continue():
        nonlocal counter
        counter += 1
        return counter < 5  # Stop after 5 frames

    # Run recording with our custom continue function
    output_path = record_n_sec_video(
        10,
        "test.avi",
        should_continue=should_continue
    )

    # Should have stopped after 5 frames
    assert mock_capture.return_value.read.call_count == 5


def test_recording_three_sec():
    out_file = "test_3_sec_vid.avi"
    vid_length_in_sec = 3
    out_dir = "test_videos/running/"

    capture = init_webcam(CHOSEN_FPS)
    output_vid = initialize_new_vid(out_file)

    # ### Act
    vid = record_n_sec_video(vid_length_in_sec, out_file, out_dir)
    vid.release()

    # ### assert
    assert get_video_length(vid) == vid_length_in_sec
    # Tear down, clean up

    pass


def test_recording_seven_sec():
    out_file = "test_7_sec_vid.avi"
    vid_length_in_sec = 7
    out_dir = "test_videos/running/"

    capture = init_webcam(CHOSEN_FPS)
    output_vid = initialize_new_vid(out_file)

    # ### Act
    vid = record_n_sec_video(vid_length_in_sec, out_file, out_dir)
    vid.release()

    # ### Assert
    assert get_video_length(vid) == vid_length_in_sec
    pass
