import cv2
import numpy as np
from typing import Tuple, List

from .v2detector import detect_motion

cv2.setBackend(cv2.CAP_V4L2)  # Use V4L2 backend
cv2.ocl.setUseOpenCL(False)   # Disable OpenCL


def process_motion_in_video(video_path: str,
                            output_path: str,
                            threshold: int = 30,
                            min_motion_pixels: int = 500,
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
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("[ERROR-28] " + video_path)
            raise ValueError("Error opening video file")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(
            output_path, fourcc, fps, (frame_width, frame_height))

        # Read first frame
        ret, prev_frame = cap.read()
        if not ret:
            raise ValueError("Error reading first frame")

        frame_number = 0
        motion_frames = []

        while True:
            ret, current_frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Detect motion
            motion_detected, regions_with_motion, mask = detect_motion(
                current_frame, prev_frame, threshold, min_motion_pixels
            )

            #
            # #
            # TODO: process a video, so, detect motion
            # TODO: If motion, keep frame
            # TODO: No motion -> Replace with black square
            # TODO: After black square replacement, compress
            # #
            #

            motion_frames.append((frame_number, motion_detected))

            # Draw rectangles around motion regions
            if motion_detected:
                for (x, y, w, h) in regions_with_motion:
                    cv2.rectangle(current_frame, (x, y),
                                  (x + w, y + h), (0, 255, 0), 2)

            writer.write(current_frame)

            if display_while_processing:
                print("Attempting to display frame...")
                try:
                    cv2.imshow('Motion Detection', current_frame)
                    cv2.waitKey(1)
                except Exception as e:
                    print(f"Display error: {e}")

            prev_frame = current_frame.copy()

    finally:
        # Cleanup
        print("Cleaning up...")
        cap.release()
        writer.release()
        cv2.destroyAllWindows()
        for i in range(4):  # Sometimes needed to fully clean up windows
            cv2.waitKey(1)

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
