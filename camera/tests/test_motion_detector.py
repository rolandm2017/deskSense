import cv2
import numpy as np

from camera.src.motionDetector.process_motion_in_video import process_motion_in_video

from .file_names import still_then_moving,  with_timestamps_still, test_vid_dir, test_out_dir, three_sec_stillness, three_sec_motion, no_timestamps_still, lossless_movement, lossless_static


# def test_3s_of_stillness():
#     """The video is of a wall"""
#     wall_vid = test_vid_dir + three_sec_stillness
#     print(wall_vid, '9ru')
#     out_vid, motion_frames = process_motion_in_video(
#         wall_vid, test_out_dir, threshold=30, display_while_processing=False)

#     print(motion_frames)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)
#     false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

#     print(true_count, false_count, '18ru')
#     assert false_count == len(motion_frames)
#     assert true_count == 0

#     # FIXME: Why does the video sometimes have 1 frame of movement?


# def test_three_sec_of_motion():
#     """The video is pure motion"""
#     moving_head_vid = test_vid_dir + three_sec_motion

#     out_vid, motion_frames = process_motion_in_video(
#         moving_head_vid, test_out_dir, threshold=40)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)

#     assert true_count == len(motion_frames)


# def test_half_motion_half_stillness():
#     """The video stops being motion halfway through"""
#     half_motion = test_vid_dir + still_then_moving

#     name = test_half_motion_half_stillness.__name__ + ".avi"
#     output_to = test_out_dir + name

#     out_vid, motion_frames = process_motion_in_video(
#         half_motion, output_to, threshold=50)
#     print(out_vid, '49ru')
#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)

#     left_bounds = len(motion_frames) * 0.20
#     right_bounds = len(motion_frames) * 0.80

#     # It's tough to make a video where motion stops precisely halfway thru

#     assert left_bounds < true_count

#     assert true_count < right_bounds


# def test_works_with_timestamps():
#     """Confirm the timestamps changing doesn't create motion"""

#     timestamps_plus_stillness = test_vid_dir + with_timestamps_still

#     out_vid, motion_frames = process_motion_in_video(
#         timestamps_plus_stillness, test_out_dir)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)

#     assert true_count == 0, "A timestamp registered as movement"


# def test_3s_of_stillness_with_LOW_threshold():
#     """The video is of a wall"""
#     wall_vid = test_vid_dir + three_sec_stillness

#     extremely_low_threshold = 1

#     out_vid, motion_frames = process_motion_in_video(
#         wall_vid, test_out_dir, threshold=extremely_low_threshold, display_while_processing=False)

#     print(motion_frames)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)
#     false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

#     print(true_count, false_count, '18ru')
#     assert true_count == len(motion_frames)
#     assert false_count == 0

#     # ###
#     # ### And then...
#     # ###
#     med_low_threshold = 30

#     out_vid, motion_frames = process_motion_in_video(
#         wall_vid, test_out_dir, threshold=med_low_threshold, display_while_processing=False)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)
#     false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

#     assert true_count == 0
#     assert false_count == len(motion_frames)

#     # FIXME: Why does the video sometimes have 1 frame of movement?


####
####
# ## # Test all videos
####
####
# no_timestamps_still      ✅
# with_timestamps_still      ✅
# still_then_moving          ✅

# three_sec_stillness       ✅
# three_sec_motion          ✅

# pure_motion

# lossless_movement     ✅
# lossless_static       ✅

low_threshold = 20


# def test_no_timestamps_still():
#     vid_path = test_vid_dir + no_timestamps_still

#     dump_out_path = test_out_dir + \
#         test_three_sec_of_motion.__name__ + ".avi"
#     out, motion_frames = process_motion_in_video(
#         vid_path, dump_out_path, threshold=low_threshold * 2, draw_green_boxes=False)

#     true_count = sum(1 for _, bool_val in motion_frames if bool_val)
#     false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

#     assert true_count == 0, "Expected zero movement"
#     assert false_count == len(motion_frames)


def test_lossless_movement():
    vid_path = test_vid_dir + lossless_movement

    extremely_low_threshold = low_threshold / 2
    dump_out_path = test_out_dir + \
        test_three_sec_of_motion.__name__ + ".avi"
    out, motion_frames = process_motion_in_video(
        vid_path, dump_out_path, threshold=50, draw_green_boxes=False)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)
    false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

    assert true_count == len(motion_frames), "Something was still in the video"
    assert false_count == 0


def test_lossless_static():
    vid_path = test_vid_dir + lossless_static

    dump_out_path = test_out_dir + \
        test_three_sec_of_motion.__name__ + ".avi"
    out, motion_frames = process_motion_in_video(
        vid_path, dump_out_path, threshold=low_threshold, draw_green_boxes=False)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)
    false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

    assert true_count == 0, "Something was moving"
    assert false_count == len(motion_frames)
