import cv2
import numpy as np

from camera.src.motionDetector.foreground_motion import ForegroundMotionDetector, process_motion_in_vid_FMD
from camera.src.util.video_util import extract_frames


from .file_names import (
    still_then_moving,
    with_timestamps_still,
    test_vid_dir,
    test_out_dir,
    three_sec_stillness,
    three_sec_motion,
    no_timestamps_still,
    lossless_movement,
    lossless_static
)


def count_frames_with_motion(frames, detector):
    has_motion_count = 0
    motion_frames = []
    for i in range(0, len(frames)):
        significant_motion, motion_regions, fg_mask = detector.detect_motion(
            frames[i])
        if significant_motion and i > 0:  # Disregard first frame
            motion_frames.append(i)
            has_motion_count += 1
    return has_motion_count, motion_frames


def find_missing_numbers(your_arr, n):
    # Convert array to set for O(1) lookups
    number_set = set(your_arr)

    # Create list of all missing numbers
    missing = [num for num in range(n + 1) if num not in number_set]

    return missing


class TestForegroundMotionDetector:
    def test_3s_of_stillness(self):
        print("40ru")
        wall_vid = test_vid_dir + three_sec_stillness

        detector = ForegroundMotionDetector()

        frames = extract_frames(wall_vid)

        has_motion_count, _ = count_frames_with_motion(frames, detector)

        assert has_motion_count == 0

    def test_three_sec_of_motion(self):
        moving_head_vid = test_vid_dir + three_sec_motion

        detector = ForegroundMotionDetector()

        frames = extract_frames(moving_head_vid)

        has_motion_count, _ = count_frames_with_motion(frames, detector)

        # the first frame always moves
        assert has_motion_count == len(frames) - 1

    def test_half_motion_half_stillness(self):
        """The video stops being motion halfway through"""
        half_motion = test_vid_dir + still_then_moving

        detector = ForegroundMotionDetector()
        frames = extract_frames(half_motion)

        has_motion_count, _ = count_frames_with_motion(frames, detector)

        about_the_right_num_of_Frames = 180
        assert has_motion_count == about_the_right_num_of_Frames

    def test_works_with_timestamps(self):
        """Confirm the timestamps changing doesn't create motion"""
        timestamps_plus_stillness = test_vid_dir + with_timestamps_still

        detector = ForegroundMotionDetector()
        frames = extract_frames(timestamps_plus_stillness)

        has_motion_count, _ = count_frames_with_motion(frames, detector)

        assert has_motion_count == 0, "A timestamp registered as movement"

    def test_no_timestamps_still(self):
        vid_path = test_vid_dir + no_timestamps_still

        detector = ForegroundMotionDetector()
        frames = extract_frames(vid_path)

        has_motion_count, motion_frames = count_frames_with_motion(
            frames, detector)
        print(motion_frames)
        assert has_motion_count == 0, "Expected zero movement"

    def test_lossless_movement(self):
        vid_path = test_vid_dir + lossless_movement

        detector = ForegroundMotionDetector()
        frames = extract_frames(vid_path)

        has_motion_count, mo_frames = count_frames_with_motion(
            frames, detector)
        print(mo_frames, '99ru')

        assert has_motion_count == len(
            frames) - 1, "Something was still in the video"

    def test_lossless_static(self):

        vid_path = test_vid_dir + lossless_static

        detector = ForegroundMotionDetector()
        frames = extract_frames(vid_path)

        has_motion_count, _ = count_frames_with_motion(frames, detector)

        assert has_motion_count == 0, "Something was moving"

    # TODO:
    def test_process_motion_in_vid_FMD_static(self):
        vid_path = test_vid_dir + lossless_static
        out_path = self.test_process_motion_in_vid_FMD_static.__name__ + ".avi"

        out, motion_frames = process_motion_in_vid_FMD(vid_path, out_path)

        true_count = sum(1 for _, bool_val in motion_frames if bool_val)

        # Accept 1 frame because the first frame tends to register as movement.
        assert true_count == 0 or true_count == 1, "Some frame had movement"

    def test_process_motion_in_vid_FMD_movement(self):
        vid_path = test_vid_dir + lossless_movement
        out_path = self.test_process_motion_in_vid_FMD_movement.__name__ + ".avi"

        frames = extract_frames(vid_path)
        out, motion_frames = process_motion_in_vid_FMD(vid_path, out_path)

        assert len(motion_frames) == len(
            frames) - 1, "Some frame didn't have movement"
