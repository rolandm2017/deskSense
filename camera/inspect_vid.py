import cv2
import numpy as np
from datetime import datetime
import os


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


def detect_motion(current_frame, previous_frame, threshold=MOTION_THRESHOLD, min_motion_pixels=500):
    """Detect motion between two frames"""
    # Convert frames to grayscale
    curr_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference
    frame_diff = cv2.absdiff(curr_gray, prev_gray)

    # Apply threshold
    motion_mask = cv2.threshold(
        frame_diff, threshold, 255, cv2.THRESH_BINARY)[1]

    # Clean up noise
    motion_mask = cv2.dilate(motion_mask, None, iterations=2)

    # Find motion contours
    contours, _ = cv2.findContours(
        motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_regions = []
    movement_detected = False

    for contour in contours:
        if cv2.contourArea(contour) > min_motion_pixels:
            movement_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            motion_regions.append((x, y, w, h))

    return movement_detected, motion_regions, motion_mask


def detect_motion_top_90(current_frame, previous_frame, threshold=30, min_motion_pixels=500):
    """Detect motion only in the top 90% of the frame"""
    # Calculate the bottom 10% cutoff point
    bottom_cutoff = int(current_frame.shape[0] * 0.9)

    # Create masked versions of the frames
    curr_masked = current_frame.copy()
    prev_masked = previous_frame.copy()

    # Black out the bottom 10%
    curr_masked[bottom_cutoff:, :] = 0
    prev_masked[bottom_cutoff:, :] = 0

    # Convert frames to grayscale
    curr_gray = cv2.cvtColor(curr_masked, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.cvtColor(prev_masked, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference
    frame_diff = cv2.absdiff(curr_gray, prev_gray)

    # Apply threshold
    motion_mask = cv2.threshold(
        frame_diff, threshold, 255, cv2.THRESH_BINARY)[1]

    # Clean up noise
    motion_mask = cv2.dilate(motion_mask, None, iterations=2)

    # Find motion contours
    contours, _ = cv2.findContours(
        motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_regions = []
    movement_detected = False

    for contour in contours:
        if cv2.contourArea(contour) > min_motion_pixels:
            (x, y, w, h) = cv2.boundingRect(contour)
            # Only include regions that start above the cutoff line
            if y < bottom_cutoff:
                movement_detected = True
                motion_regions.append((x, y, w, h))

    return movement_detected, motion_regions, motion_mask


def main():
    # Initialize video file
    # Replace with your actual file path
    # video_path = 'test_videos/3sec_Still.avi'
    # video_path = 'test_videos/STILLVID.avi'
    # video_path = 'test_videos/PURE_motion2.avi'
    video_path = 'test_videos/me_using_pc1.avi'
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

            # Detect motion
            movement_detected, movement_regions, mask = detect_motion(
                current_frame,
                previous_frame, threshold=30
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
