import cv2
import numpy as np
from typing import Tuple, List

from .detect_using_diff import detect_motion_using_diff
from ..recording.codecs import get_codec
from ..config.constants import MOTION_THRESHOLD


def process_motion_in_video(video_path: str,
                            output_path: str,
                            threshold: int = MOTION_THRESHOLD,
                            min_motion_pixels: int = 500,
                            draw_green_boxes: bool = True,
                            display_while_processing: bool = False) -> List[Tuple[int, bool]]:
    """
    Process video file for motion detection.

    Args:
        video_path: Path to input video file
        threshold: Pixel difference threshold for motion detection
        min_motion_pixels: Minimum area of motion region
        output_path: Path to save processed video (optional)
        display: Whether to display video during processing

    Returns:
        List of tuples containing (frame_number, motion_detected)
    """
    # At the start of the function, add:
    print("Starting video processing...")
    print(f"Display enabled: {display_while_processing}")
    cap = None
    writer = None
    try:
        print(video_path, '32ru')
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("[ERROR-28] " + video_path)
            raise ValueError("Error opening video file")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Setup video writer
        fourcc = get_codec()
        print(output_path, '44ru')
        writer = cv2.VideoWriter(
            output_path, fourcc, fps, (frame_width, frame_height))

        # Read first frame
        ret, prev_frame = cap.read()
        if not ret:
            raise ValueError("[ERROR-52] Error reading first frame")

        frame_number = 0
        motion_frames = []

        while True:
            ret, current_frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Detect motion
            motion_detected, regions_with_motion, mask = detect_motion_using_diff(
                current_frame, prev_frame, threshold, min_motion_pixels
            )

            motion_frames.append((frame_number, motion_detected))

            # Draw rectangles around motion regions
            if motion_detected and draw_green_boxes:
                for (x, y, w, h) in regions_with_motion:
                    cv2.rectangle(current_frame, (x, y),
                                  (x + w, y + h), (0, 255, 0), 2)

            writer.write(current_frame)

            if display_while_processing:
                print("Attempting to display frame...")
                try:
                    cv2.imshow('Motion Detection', current_frame)
                    # Set wait time to maintain approximately 30 FPS display
                    output_fps = 30
                    wait_time = max(1, int(1000/output_fps))  # in milliseconds
                    cv2.waitKey(wait_time)
                except Exception as e:
                    print(f"Display error: {e}")

            prev_frame = current_frame.copy()

    except ValueError as e:
        print("A ValueError occurred")

    finally:
        # Cleanup
        print("Cleaning up...")
        print(cap, '99ru')
        print(writer, "100ru")
        cap.release()
        writer.release()
        cv2.destroyAllWindows()
        for i in range(4):  # Sometimes needed to fully clean up windows
            cv2.waitKey(1)
    print(output_path, len(motion_frames), '108ru')
    return output_path, motion_frames  # the finished vid


# Example usage:
if __name__ == "__main__":
    video_file = "path/to/your/video.mp4"
    motion_frames = process_motion_in_video(
        video_file,
        threshold=30,
        min_motion_pixels=500,
        output_path="output.mp4",
        display=True
    )

    # Print frames where motion was detected
    for frame_num, has_motion in motion_frames:
        if has_motion:
            print(f"Motion detected in frame {frame_num}")
