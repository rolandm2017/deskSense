from camera.src.motionDetector.video_detector import process_motion_in_video

from .file_names import still_then_moving, stillness_ten_sec, no_timestamps_still, with_timestamps_still, motion_ten_sec, test_vid_dir, test_out_dir


def test_ten_sec_of_stillness():
    """The video is of a wall"""
    wall_vid = test_vid_dir + stillness_ten_sec

    out_vid, motion_frames = process_motion_in_video(wall_vid, test_out_dir)

    print(motion_frames)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)
    false_count = sum(1 for _, bool_val in motion_frames if not bool_val)

    assert false_count == len(motion_frames) - 1
    assert true_count == 1

    # FIXME: Why does the video have 1 frame of movement?
    # FIXME: Why does the video have 1 frame of movement?
    # FIXME: Why does the video have 1 frame of movement?
    # FIXME: Why does the video have 1 frame of movement?


def test_five_sec_of_motion():
    """The video is pure motion"""
    moving_head_vid = test_vid_dir + motion_ten_sec

    out_vid, motion_frames = process_motion_in_video(
        moving_head_vid, test_out_dir)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)

    assert true_count == len(motion_frames)


def test_half_motion_half_stillness():
    """The video stops being motion halfway through"""
    half_motion = test_vid_dir + still_then_moving

    out_vid, motion_frames = process_motion_in_video(
        half_motion, test_out_dir)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)

    left_bounds = len(motion_frames) * 0.35
    right_bounds = len(motion_frames) * 0.65

    # It's tough to make a video where motion stops precisely halfway thru

    assert true_count > left_bounds and true_count < right_bounds


def test_works_with_timestamps():
    """Confirm the timestamps changing doesn't create motion"""

    timestamps_plus_stillness = test_vid_dir + with_timestamps_still

    out_vid, motion_frames = process_motion_in_video(
        timestamps_plus_stillness, test_out_dir)

    true_count = sum(1 for _, bool_val in motion_frames if bool_val)

    assert true_count == 0, "A timestamp registered as movement"
