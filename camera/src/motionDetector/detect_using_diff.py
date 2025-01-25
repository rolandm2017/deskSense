import cv2
import numpy as np

from ..constants import MOTION_THRESHOLD


def detect_motion_using_diff(current_frame, previous_frame, threshold=MOTION_THRESHOLD, min_motion_pixels=500):
    # Convert frames to grayscale
    curr_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference
    frame_diff = cv2.absdiff(curr_gray, prev_gray)

    # Apply threshold
    motion_mask = cv2.threshold(
        # "Mask" is like saying "filter"
        frame_diff, threshold, 255, cv2.THRESH_BINARY)[1]

    # Clean up noise
    motion_mask = cv2.dilate(motion_mask, None, iterations=2)

    # Find motion contours
    contours, _ = cv2.findContours(
        motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_regions = []
    movement_detected = False

    for contour in contours:
        sufficient_area_shows_movement = cv2.contourArea(
            contour) > min_motion_pixels
        if sufficient_area_shows_movement:
            movement_detected = True
            (x, y, w, h) = cv2.boundingRect(contour)
            motion_regions.append((x, y, w, h))

    # "Mask" is like saying "filter"
    return movement_detected, motion_regions, motion_mask


def detect_motion_top_90_using_diff(current_frame, previous_frame, threshold=30, min_motion_pixels=500):
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


if __name__ == "__main__":

    # Usage example:
    cap = cv2.VideoCapture(0)  # Use 0 for webcam or video path
    ret, previous_frame = cap.read()

    while True:
        ret, current_frame = cap.read()
        if not ret:
            break

        movement_detected, movement_regions, mask = detect_motion(
            current_frame, previous_frame)

        if movement_detected:
            for (x, y, w, h) in movement_regions:
                # Draw frame around movement
                cv2.rectangle(current_frame, (x, y),
                              (x + w, y + h), (0, 255, 0), 2)
        else:
            current_frame = np.zeros_like(current_frame)  # Create black frame

        cv2.imshow('Motion Detection', current_frame)
        previous_frame = current_frame.copy()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
