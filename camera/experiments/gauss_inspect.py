import cv2
import numpy as np
import time

from src.motionDetector.foreground_motion import ForegroundMotionDetector


def main():
    detector = ForegroundMotionDetector(
        min_area=500)  # Adjust min_area as needed
    video_path = 'samples/LONG_VID.avi'
    video_path = 'samples/TenSec_Stillness.avi'  # ✅
    video_path = 'samples/3sec_Still2.avi'
    video_path = 'samples/3sec_Still2.avi'
    video_path = 'samples/Stillness_No_Timestamps1.avi'
    video_path = 'samples/Lossless-me_using_pcV.avi'
    video_path = "samples/Lossless-StillnessV.avi"

    cap = cv2.VideoCapture(video_path)

    # Get the actual FPS of the video
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0:  # If FPS cannot be determined, default to 30
        fps = 30

    # Calculate frame delay (in milliseconds)
    frame_delay = int(1000/fps)

    detector = ForegroundMotionDetector(min_area=500)
    while True:
        start_time = time.time()  # Start timing this frame
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
        # Position first window at (0,0)
        cv2.moveWindow('Motion Detection', 0, 0)
        # Position second window next to first
        cv2.moveWindow('Foreground Mask', frame.shape[1] + 100, 0)

        # Calculate how long to wait
        processing_time = int((time.time() - start_time) * 1000)
        wait_time = max(1, frame_delay - processing_time)

        # Wait and check for 'q' key
        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
