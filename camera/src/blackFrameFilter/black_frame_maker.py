import cv2
import numpy as np
from typing import List, Tuple
import os

from ..recording.codecs import get_codec
from ..util.video_util import extract_frames


def make_black_frame(current_frame):
    # Create black frame
    return np.zeros_like(current_frame)


def insert_filter_indicator_into_file_name(video_path):
    if isinstance(video_path, str):
        src = video_path.rsplit('.', 1)
        return src[0] + '_blackout.' + src[1]
    else:
        src = video_path.name.rsplit(".", 1)
        return src[0] + '_blackout.' + src[1]


def filter_with_black(video_path: str, motion_frames: List[Tuple[int, bool]], path_manager) -> str:
    """
    Process a video file, replacing frames without motion with black frames.

    Args:
        video_path: Path to input video file
        motion_frames: List of tuples containing (frame_number, motion_detected)

    Returns:
        Path to the processed video file
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR-25] " + video_path)
        raise ValueError("Error opening video file")

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # FIXME: Make this line come from a function, that is configured to
    # FIXME: ...always put the file in the right folder
    # Create output path by adding '_blackfiltered' before the extension
    output_name = insert_filter_indicator_into_file_name(video_path)
    output_path = path_manager.processed_path(output_name)

    # Setup video writer
    fourcc = get_codec()
    writer = cv2.VideoWriter(
        output_path, fourcc, fps, (frame_width, frame_height))

    frame_number = 0
    motion_dict = dict(motion_frames)  # Convert to dictionary for O(1) lookup

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        # Check if current frame has motion
        has_motion = motion_dict.get(frame_number, False)

        if not has_motion:
            # Replace with black frame if no motion detected
            frame = make_black_frame(frame)

        writer.write(frame)

    # Cleanup
    cap.release()
    writer.release()
    print("[log] black filter video at " / output_path)
    return output_path
