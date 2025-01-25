import pytest
import numpy as np
import cv2

from camera.src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.detect_using_diff import detect_motion
from camera.src.motionDetector.process_motion_in_video import process_motion_in_video
from camera.src.video_util import extract_frame, extract_frames

from .util.frames import assert_frames_equal

from .file_names import with_timestamps_still, test_vid_dir, test_out_dir, pure_motion, three_sec_stillness, lossless_movement

# ##############
# ############## debug tool
# ##############


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
    """Analyze a video with pure motion, expecting the filter_with_black to change nothing."""
    vid_path = test_vid_dir + lossless_movement

    fps = 30  # Adjust this to match your video's fps

    first_frame = int(90 * 0.1)
    second_frame = int(90 * 0.2)
    third_frame = int(90 * 0.3)
    print("FOO\n\nfoo\nf\nf\nf\nf96ru")
    dump_out_path = test_out_dir + \
        test_three_sec_of_motion.__name__ + ".avi"
    out, motion_frames = process_motion_in_video(
        vid_path, dump_out_path, threshold=20, draw_green_boxes=False)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)
    false_count = sum(1 for _, bool_val in motion_frames if not bool_val)
    print(true_count, false_count, '104ru')
    # FIXME: The video doesnt REALLY have no motion
    assert true_count == len(motion_frames) - 1, "Some frame had no motion"

    path_to_check = filter_with_black(out, motion_frames)

    start_frames = extract_frames(vid_path)
    result = extract_frames(path_to_check)

    print("First frame shapes:")
    # print(f"Original: {start_frames[first_frame].shape}")
    # print(f"Result: {result[first_frame].shape}")

    print("\nFirst frame sample pixels (top-left corner):")
    print(f"Original:\n{start_frames[first_frame][0:3, 0:3]}")
    print(f"Result:\n{result[first_frame][0:3, 0:3]}")

    # Calculate absolute difference to see where frames differ
    diff = np.abs(start_frames[first_frame].astype(
        float) - result[first_frame].astype(float))
    print(f"\nMax difference: {np.max(diff)}")
    print(f"Mean difference: {np.mean(diff)}")

    first = (start_frames[first_frame], result[first_frame])
    second = (start_frames[second_frame], result[second_frame])
    third = (start_frames[third_frame], result[third_frame])

    # visualize_differences(first[0], first[1])
    print("128ru")
    threshold = 0.35
    try:
        assert_frames_equal(
            start_frames[first_frame], result[first_frame], threshold)
    except AssertionError as e:
        print(f"\nAssertion Error Details:\n{str(e)}")
        raise  # Re-raise the exception after printing details
    # # # Debug visualization - comment out when not needed
    # # import cv2
    # # fps = 30  # Adjust this to match your video's fps
    # # for frame in result:
    # #     cv2.imshow('Video Playback', frame)
    # #     if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):  # Press 'q' to exit
    # #         break
    # # cv2.destroyAllWindows()
    # print(start_frames[0], result[0], '94ru')
    # print(first_frame, second_frame, third_frame)

    # print(first, '105ru')
    # assert_frames_equal(first[0], first[1], threshold)
    # assert_frames_equal(second[0], second[1], threshold)
    # assert_frames_equal(third[0], third[1], threshold)
