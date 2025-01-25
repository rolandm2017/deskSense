import cv2
import numpy as np
from typing import List, Tuple

from ..codecs import get_codec


def make_black_frame(current_frame):
    # Create black frame
    return np.zeros_like(current_frame)


def filter_with_black(video_path: str, motion_frames: List[Tuple[int, bool]]) -> str:
    """
    Process a video file, replacing frames without motion with black frames.

    Args:
        video_path: Path to input video file
        motion_frames: List of tuples containing (frame_number, motion_detected)

    Returns:
        Path to the processed video file
    """
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR-25] " + video_path)
        raise ValueError("Error opening video file")

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create output path by adding '_blackfiltered' before the extension
    output_path = video_path.rsplit(
        '.', 1)[0] + '_blackfiltered.' + video_path.rsplit('.', 1)[1]

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

    return output_path
