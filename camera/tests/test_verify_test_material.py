import os

from ..debug import get_frame_timestamps, get_video_length


###############################################################################
#                                                                             #
#   File verifies that test material has the right length and frame count     #
#                                                                             #
###############################################################################

motion_ten_sec = "test_output1-Motion_TenSec.avi"
stillness_ten_sec = "test_output-Stillness_TenSec.avi"
no_timestamps_still = "test_out-Stillness_No_Timestamps1.avi"
with_timestamps_still = "test_out-Stillness-With-Timestamps1.avi"
still_then_moving = "test_out-Still_Then_Moving1.avi"


def get_full_path(file_name):
    return os.path.join(test_videos_dir, file_name)


# Get the current directory of the test file
current_dir = os.path.dirname(os.path.abspath(
    __file__))  # This gets camera/tests/

# Go up one directory to camera/ and then down to test_videos
test_videos_dir = os.path.join(os.path.dirname(current_dir), 'test_videos')

# Create the full path to your test video
motion_ten_sec = get_full_path(motion_ten_sec)
stillness_ten_sec = get_full_path(stillness_ten_sec)
no_timestamps_still = get_full_path(no_timestamps_still)
with_timestamps_still = get_full_path(with_timestamps_still)
still_then_moving = get_full_path(still_then_moving)


def test_video_lenths():
    ten_sec = get_video_length(motion_ten_sec)
    ten_sec_again = get_video_length(stillness_ten_sec)

    # pretty_darn_close_to_ten_sec = x > 9.5 and x < 10.5
    assert ten_sec == 10
    assert ten_sec_again == 10

    timestamps_5_sec = get_video_length(no_timestamps_still)
    timestamps_5_sec_2 = get_video_length(with_timestamps_still)

    assert timestamps_5_sec == 5
    assert timestamps_5_sec_2 == 5

    still_moving_len = get_video_length(still_then_moving)

    assert still_moving_len == 10


def test_video_frames():
    _, frame_count = get_frame_timestamps(motion_ten_sec)
    _, frame_count2 = get_frame_timestamps(stillness_ten_sec)
    _, frame_count3 = get_frame_timestamps(no_timestamps_still)

    assert frame_count == 300
    assert frame_count2 == 300
    assert frame_count3 == 150
