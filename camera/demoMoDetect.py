import cv2
import numpy as np
from datetime import datetime

import os
print("Display:", os.getenv('DISPLAY'))
print("XDG_SESSION_TYPE:", os.getenv('XDG_SESSION_TYPE'))
print("WAYLAND_DISPLAY:", os.getenv('WAYLAND_DISPLAY'))

# cv2.setBackend(cv2.CAP_V4L2)  # Use V4L2 backend
# cv2.ocl.setUseOpenCL(False)   # Disable OpenCL


def add_timestamp(frame):
    """Add timestamp to frame"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cv2.putText(frame, timestamp, (frame.shape[1] - 200, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame


def detect_motion(current_frame, previous_frame, threshold=30, min_motion_pixels=500):
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


def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    # Read first frame
    ret, previous_frame = cap.read()
    if not ret:
        print("Failed to grab first frame")
        return

    print("Press 'q' to quit")

    try:
        while True:
            ret, current_frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Add timestamp
            current_frame = add_timestamp(current_frame)

            # Detect motion
            movement_detected, movement_regions, mask = detect_motion(
                current_frame,
                previous_frame
            )

            # Draw rectangles around motion regions
            for (x, y, w, h) in movement_regions:
                cv2.rectangle(current_frame, (x, y),
                              (x + w, y + h), (0, 255, 0), 2)

            # Show the frame
            cv2.imshow('Motion Detection', current_frame)

            # Update previous frame
            previous_frame = current_frame.copy()

            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
