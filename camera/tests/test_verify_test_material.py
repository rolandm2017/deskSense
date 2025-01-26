import os

from ..debug import get_frame_timestamps, get_video_length

from .file_names import still_then_moving,  no_timestamps_still, with_timestamps_still


###############################################################################
#                                                                             #
#   File verifies that test material has the right length and frame count     #
#                                                                             #
###############################################################################


def get_full_path(file_name):
    return os.path.join(test_videos_dir, file_name)


# Get the current directory of the test file
current_dir = os.path.dirname(os.path.abspath(
    __file__))  # This gets camera/tests/

# Go up one directory to camera/ and then down to test_videos
test_videos_dir = os.path.join(os.path.dirname(current_dir), 'samples')

# Create the full path to your test video
# motion_ten_sec = get_full_path(motion_ten_sec)
no_timestamps_still = get_full_path(no_timestamps_still)
with_timestamps_still = get_full_path(with_timestamps_still)
still_then_moving = get_full_path(still_then_moving)


def test_video_lenths():

    timestamps_5_sec = get_video_length(no_timestamps_still)
    timestamps_5_sec_2 = get_video_length(with_timestamps_still)

    assert timestamps_5_sec == 3.0  # used to be 5 but the video changed
    assert timestamps_5_sec_2 == 5

    still_moving_len = get_video_length(still_then_moving)

    assert still_moving_len == 10


def test_video_frames():
    _, frame_count3 = get_frame_timestamps(no_timestamps_still)

    assert frame_count3 == 90
