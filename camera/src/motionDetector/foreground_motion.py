import cv2

import numpy as np

from ..codecs import get_codec


class ForegroundMotionDetector:
    """
    The class uses cv2.createBackgroundSubtractorMOG2, 
    a Gaussian Mixture-based background subtraction algorithm.

    This method maintains a background model and detects 
    changes (foreground) in the video frames, which correspond to motion.
    """

    def __init__(self, min_area=500, blur_size=25, dilate_iterations=2):  # blur 21 -> 25
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=28,  # was 16 before, but too sensitive
            detectShadows=False
        )
        self.min_area = min_area
        self.blur_size = blur_size
        self.dilate_iterations = dilate_iterations
    #     self.min_area = 1000  # Increased from 500
    # self.blur_size = 31   # Increased from 21
    # self.dilate_iterations = 1  # Reduced from 2

    def detect_motion(self, frame):
        """Method assumes the frame is NOT blurred yet"""
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(frame, (self.blur_size, self.blur_size), 0)

        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(blurred)

        # Apply morphological operations to remove small noise and connect nearby motion regions
        kernel = np.ones((3, 3), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(
            fg_mask, kernel, iterations=self.dilate_iterations)

        # Find contours of moving objects
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours based on area to identify significant motion
        significant_motion = False
        motion_regions = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                significant_motion = True
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append((x, y, w, h))
        """Note that the first frame to enter the detector will always register movement"""
        return significant_motion, motion_regions, fg_mask


def process_motion_in_vid_FMD(video_path, output_path):
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
        detector = ForegroundMotionDetector()
        while True:
            ret, current_frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Detect motion
            motion_detected, motion_regions, fg_mask = detector.detect_motion(
                current_frame)

            motion_frames.append((frame_number, motion_detected))

            # Draw rectangles around motion regions
            if motion_detected:
                for (x, y, w, h) in motion_regions:
                    cv2.rectangle(current_frame, (x, y),
                                  (x + w, y + h), (0, 255, 0), 2)

            writer.write(current_frame)
            display_while_processing = False  # Debug
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
