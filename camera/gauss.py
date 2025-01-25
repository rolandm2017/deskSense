import cv2
import numpy as np


class MotionDetector:
    def __init__(self, min_area=500, blur_size=21, dilate_iterations=2):
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        self.min_area = min_area
        self.blur_size = blur_size
        self.dilate_iterations = dilate_iterations

    def detect_motion(self, frame):
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


def main():
    cap = cv2.VideoCapture(0)  # Use default camera
    detector = MotionDetector(min_area=500)  # Adjust min_area as needed

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
