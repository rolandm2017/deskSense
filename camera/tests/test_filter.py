import pytest
import numpy as np
import cv2

from camera.src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.v2detector import detect_motion
from camera.src.motionDetector.video_detector import process_motion_in_video
from camera.src.video_util import extract_frame, extract_frames

from .file_names import still_then_moving, stillness_ten_sec, no_timestamps_still, with_timestamps_still, motion_ten_sec, test_vid_dir, test_out_dir


def test_black_is_inserted_automated():
    """Automated checks for black frame"""
    vid_path = test_vid_dir + stillness_ten_sec
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
    """Test that timestamps do not interfere with ... """

    vid_path = test_vid_dir + with_timestamps_still
    print(vid_path, '35ru')
    dump_out_path = test_out_dir + test_five_sec_of_pure_stillness.__name__ + ".avi"

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


def test_five_sec_of_pure_stillness():
    vid_path = test_vid_dir + with_timestamps_still
    print(vid_path, '35ru')
    dump_out_path = test_out_dir + test_five_sec_of_pure_stillness.__name__ + ".avi"

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


# TODO: Test sad paths
# TODO: Test sad paths
# TODO: Test sad paths
# TODO: Test sad paths


def test_five_sec_of_motion():
    pass
