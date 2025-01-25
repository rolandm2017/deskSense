import cv2
import numpy as np
from datetime import datetime
import os

from src.motionDetector.v2detector import detect_motion, detect_motion_top_90
from src.preprocess import preprocess_frame, preprocess_blurring
from src.constants import MOTION_THRESHOLD


###################################################
#                                                 #
#     For viewing motion detect thru a video      #
#                                                 #
###################################################


def add_timestamp(frame):
    """Add timestamp to frame"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cv2.putText(frame, timestamp, (frame.shape[1] - 200, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame


def main():
    # Initialize video file
    # Replace with your actual file path
    # video_path = 'test_videos/3sec_Still.avi'
    # video_path = 'test_videos/STILLVID.avi'
    video_path = 'test_videos/LONG_VID.avi'
    # video_path = 'test_videos/PURE_motion2.avi'
    # video_path = 'test_videos/me_using_pc1.avi'
    # video_path = 'test_videos/me_using_pcV-Lossless.avi'
    # video_path = 'test_videos/me_using_pcV-Lossless.avi'

    # video_path = 'test_videos/StillnessV-Lossless.avi'
    # video_path = 'test_videos/TenSec_Stillness.avi'
    print(video_path, '50ru')
    cap = cv2.VideoCapture(video_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    # Read first frame
    ret, previous_frame = cap.read()
    if not ret:
        print("Failed to grab first frame")
        return

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"Video FPS: {fps}")

    print("Press 'q' to quit")
    movement_count = 0
    try:
        while True:
            ret, current_frame = cap.read()
            if not ret:
                print("End of video file")
                break

            # Add timestamp
            current_frame = add_timestamp(current_frame)

            blurred_frame = preprocess_blurring(current_frame)
            # Detect motion
            movement_detected, movement_regions, mask = detect_motion_top_90(
                blurred_frame,
                previous_frame, threshold=60
            )

            if movement_detected:
                movement_count += 1

            # Draw rectangles around motion regions
            for (x, y, w, h) in movement_regions:
                cv2.rectangle(current_frame, (x, y),
                              (x + w, y + h), (0, 255, 0), 2)
                # cutoff_y = int(current_frame.shape[0] * 0.9)
                # cv2.line(current_frame, (0, cutoff_y),
                #          (current_frame.shape[1], cutoff_y), (255, 0, 0), 2)

            # Show the frame
            cv2.imshow('Motion Detection', current_frame)

            # Update previous frame
            previous_frame = current_frame.copy()

            # Add delay to maintain original video speed
            if cv2.waitKey(1000//fps) & 0xFF == ord('q'):
                break

    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("[log] movements: " + str(movement_count) + " or " +
              str(round(movement_count / total_frames, 2)))


if __name__ == "__main__":
    main()
