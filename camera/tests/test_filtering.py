import pytest
import numpy as np
import cv2
import os


from camera.src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.detect_using_diff import detect_motion_using_diff, detect_motion_top_90_using_diff
from camera.src.motionDetector.process_motion_in_video import process_motion_in_video
from camera.src.motionDetector.foreground_motion import ForegroundMotionDetector, process_motion_in_vid_FMD
from camera.src.util.video_util import extract_frame, extract_frames
from camera.src.util.path_manager import VideoPathManager

from .util.frames import assert_frames_equal

from .file_names import with_timestamps_still, test_vid_dir, test_out_dir, pure_motion, three_sec_stillness, lossless_movement, empty_vid

# ##############
# ############## debug tool
# ##############


def has_zero_black_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Check if frame is all zeros (black)
        if np.all(frame == 0):
            cap.release()
            return False

    cap.release()
    return True


def play_video(vid_path):
    cap = cv2.VideoCapture(vid_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow('Filtered Video', frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def visualize_differences(frame1, frame2):
    diff = np.abs(frame1.astype(float) - frame2.astype(float))
    diff_normalized = (diff * 255 / diff.max()).astype(np.uint8)

    import cv2
    cv2.imshow('Difference Map', diff_normalized)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def test_black_is_inserted_automated():
    """Automated checks for black frame"""
    vid_path = test_vid_dir + three_sec_stillness
    some_frame = 80
    print(vid_path, '19ru')
    frame_k = extract_frame(vid_path, some_frame)
    print(frame_k, '20ru')
    filtered = make_black_frame(frame_k)
    print(filtered, '21ru')

    assert filtered.shape[0] == frame_k.shape[0], "The heights disagreed"
    assert filtered.shape[1] == frame_k.shape[1], "The widths disagreed"
    assert np.all(filtered == 0), "Frame is not all zeros"


def test_works_with_timestamps():
    """Test that timestamps do not interfere with black frame replacement"""

    vid_path = test_vid_dir + with_timestamps_still
    dump_out_path = test_out_dir + test_works_with_timestamps.__name__ + ".avi"
    path_mgmt = VideoPathManager()

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames, path_mgmt)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


def test_three_sec_of_pure_stillness():
    vid_path = test_vid_dir + three_sec_stillness

    dump_out_path = test_out_dir + test_three_sec_of_pure_stillness.__name__ + ".avi"
    path_mgmt = VideoPathManager()

    out, motion_frames = process_motion_in_video(vid_path, dump_out_path)

    assert all(x[1] == False for x in motion_frames)  # Test setup

    path_to_check = filter_with_black(out, motion_frames, path_mgmt)

    frames = extract_frames(path_to_check)

    assert all(np.all(frame == 0) for frame in frames)


# FIXME: This test should use the FMD
def test_three_sec_of_motion():
    """Analyze a video with pure motion, expecting the filter_with_black to change nothing."""
    input_path = test_vid_dir + lossless_movement

    dump_out_path = test_out_dir + \
        test_three_sec_of_motion.__name__ + ".avi"

    detector = ForegroundMotionDetector()

    path_mgmt = VideoPathManager()

    out, motion_frames = process_motion_in_vid_FMD(input_path, dump_out_path)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)

    # Testing setup conditions
    assert true_count == len(motion_frames), "Some frame had no motion"

    black_filtered_path = filter_with_black(out, motion_frames, path_mgmt)

    assert has_zero_black_frames(
        black_filtered_path), "The video had black inserted somewhere"
