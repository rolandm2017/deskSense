import cv2

import numpy as np


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

        return significant_motion, motion_regions, fg_mask
