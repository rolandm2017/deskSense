import cv2
import numpy as np


def detect_motion(video_path, threshold=30):
    cap = cv2.VideoCapture(video_path)
    ret, prev_frame = cap.read()
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break

        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

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

        # Draw rectangles around motion areas
        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Minimum area threshold
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(curr_frame, (x, y),
                              (x + w, y + h), (0, 255, 0), 2)

        # Display result
        cv2.imshow('Motion Detection', curr_frame)

        prev_gray = curr_gray

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Usage example
detect_motion("path_to_your_video.mp4", threshold=30)
