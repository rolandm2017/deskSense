import cv2
import numpy as np

from src.motionDetector.foreground_motion import ForegroundMotionDetector


def main():
    cap = cv2.VideoCapture(0)  # Use default camera
    detector = ForegroundMotionDetector(
        min_area=500)  # Adjust min_area as needed

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect motion
        motion_detected, regions, mask = detector.detect_motion(frame)

        # Draw rectangles around motion regions
        if motion_detected:
            for (x, y, w, h) in regions:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "Motion Detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display results
        cv2.imshow('Motion Detection', frame)
        cv2.imshow('Foreground Mask', mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
