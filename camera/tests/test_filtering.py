import pytest
import numpy as np
import cv2

from camera.src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.v2detector import detect_motion
from camera.src.motionDetector.motion_detector import process_motion_in_video
from camera.src.video_util import extract_frame, extract_frames

from .util.frames import assert_frames_equal

from .file_names import stillness_ten_sec,  with_timestamps_still, motion_ten_sec, test_vid_dir, test_out_dir, three_sec_motion, three_sec_stillness


def test_black_is_inserted_automated():
    """Automated checks for black frame"""
    vid_path = test_vid_dir + three_sec_stillness
    some_frame = 120
    frame_k = extract_frame(vid_path, some_frame)
    filtered = make_black_frame(frame_k)

    assert filtered.shape[0] == frame_k.shape[0], "The heights disagreed"
    assert filtered.shape[1] == frame_k.shape[1], "The widths disagreed"
    assert np.all(filtered == 0), "Frame is not all zeros"


# TODO: Somehow, make the jet black frame visually inspectable


# TODO: Complete the below func
# TODO: Test motion detect on the timestamp vid

def test_works_with_timestamps():
    """Test that timestamps do not interfere with black frame replacement"""

    vid_path = test_vid_dir + with_timestamps_still
    dump_out_path = test_out_dir + test_works_with_timestamps.__name__ + ".avi"

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


def test_three_sec_of_pure_stillness():
    vid_path = test_vid_dir + three_sec_stillness

    dump_out_path = test_out_dir + test_three_sec_of_pure_stillness.__name__ + ".avi"

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


# TODO: Test sad paths
# TODO: Test sad paths
# TODO: Test sad paths
# TODO: Test sad paths


def test_three_sec_of_motion():
    vid_path = test_vid_dir + three_sec_motion

    dump_out_path = test_out_dir + \
        test_three_sec_of_motion.__name__ + ".avi"
    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == True for x in motion_frames)

    path_to_check = filter_with_black(out, motion_frames)

    start_frames = extract_frames(vid_path)
    result = extract_frames(path_to_check)
    # # Debug visualization - comment out when not needed
    # import cv2
    # fps = 30  # Adjust this to match your video's fps
    # for frame in result:
    #     cv2.imshow('Video Playback', frame)
    #     if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):  # Press 'q' to exit
    #         break
    # cv2.destroyAllWindows()

    assert assert_frames_equal(start_frames[110], result[110], 0.05)
    assert assert_frames_equal(start_frames[220], result[220], 0.05)
    assert assert_frames_equal(start_frames[330], result[330], 0.05)
