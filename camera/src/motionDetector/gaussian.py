import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

# https://claude.ai/chat/1991fac6-66ed-485b-b9ea-4c31fb0afe29


@dataclass
class MotionRegion:
    x: int
    y: int
    width: int
    height: int
    area: float


@dataclass
class MotionFrame:
    motion_detected: bool
    regions: List[MotionRegion]
    mask: np.ndarray
    filtered_mask: Optional[np.ndarray] = None


class StreamMotionDetector:
    def __init__(
        self,
        min_area: int = 500,
        blur_size: int = 21,
        dilate_iterations: int = 2,
        threshold: int = 25
    ):
        """
        Initialize the motion detector for processing frame streams.

        Args:
            min_area: Minimum pixel area to consider as significant motion
            blur_size: Size of Gaussian blur kernel (must be odd)
            dilate_iterations: Number of dilation iterations for noise reduction
            threshold: Threshold for motion detection (0-255)
        """
        if blur_size % 2 == 0:
            blur_size += 1  # Ensure odd number for Gaussian kernel

        self.min_area = min_area
        self.blur_size = blur_size
        self.dilate_iterations = dilate_iterations
        self.threshold = threshold

        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )

        # Store previous frame for delta calculation
        self.prev_frame = None

    def _apply_gaussian(self, frame: np.ndarray) -> np.ndarray:
        """Apply Gaussian blur to reduce noise."""
        return cv2.GaussianBlur(
            frame,
            (self.blur_size, self.blur_size),
            0
        )

    def _get_frame_delta(self, frame: np.ndarray) -> np.ndarray:
        """Calculate frame difference and threshold."""
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Initialize first frame
        if self.prev_frame is None:
            self.prev_frame = gray
            return np.zeros_like(gray)

        # Calculate absolute difference
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        self.prev_frame = gray

        # Threshold the delta
        thresh = cv2.threshold(
            frame_delta,
            self.threshold,
            255,
            cv2.THRESH_BINARY
        )[1]

        return thresh

    def _apply_noise_reduction(self, mask: np.ndarray) -> np.ndarray:
        """Apply morphological operations to reduce noise."""
        # Create kernel for morphological operations
        kernel = np.ones((3, 3), np.uint8)

        # Apply opening to remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Dilate to connect nearby motion regions
        if self.dilate_iterations > 0:
            mask = cv2.dilate(mask, kernel,
                              iterations=self.dilate_iterations)

        return mask

    def _find_motion_regions(self,
                             mask: np.ndarray) -> List[MotionRegion]:
        """Find and filter motion regions from mask."""
        regions = []

        # Find contours
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Process each contour
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                regions.append(MotionRegion(x, y, w, h, area))

        return regions

    def process_frame(self, frame: np.ndarray) -> MotionFrame:
        """
        Process a single frame to detect motion.

        Args:
            frame: Input frame as numpy array

        Returns:
            MotionFrame object containing detection results
        """
        # Apply Gaussian blur
        blurred = self._apply_gaussian(frame)

        # Get frame delta and background subtraction
        delta_mask = self._get_frame_delta(blurred)
        bg_mask = self.bg_subtractor.apply(blurred)

        # Combine masks
        combined_mask = cv2.bitwise_or(delta_mask, bg_mask)

        # Apply noise reduction
        filtered_mask = self._apply_noise_reduction(combined_mask)

        # Find motion regions
        regions = self._find_motion_regions(filtered_mask)

        return MotionFrame(
            motion_detected=len(regions) > 0,
            regions=regions,
            mask=combined_mask,
            filtered_mask=filtered_mask
        )

    def draw_debug(self,
                   frame: np.ndarray,
                   motion_frame: MotionFrame) -> np.ndarray:
        """
        Draw debug visualization on frame.

        Args:
            frame: Input frame
            motion_frame: MotionFrame object from process_frame()

        Returns:
            Frame with debug visualization
        """
        debug_frame = frame.copy()

        # Draw rectangles around motion regions
        for region in motion_frame.regions:
            cv2.rectangle(
                debug_frame,
                (region.x, region.y),
                (region.x + region.width, region.y + region.height),
                (0, 255, 0),
                2
            )

            # Add area label
            cv2.putText(
                debug_frame,
                f"Area: {int(region.area)}",
                (region.x, region.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        # Add motion status
        if motion_frame.motion_detected:
            cv2.putText(
                debug_frame,
                "Motion Detected",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        return debug_frame

# Example usage:


def main():
    cap = cv2.VideoCapture(0)
    detector = StreamMotionDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        motion_frame = detector.process_frame(frame)

        # Draw debug visualization
        debug_frame = detector.draw_debug(frame, motion_frame)

        # Display results
        cv2.imshow('Motion Detection', debug_frame)
        cv2.imshow('Motion Mask', motion_frame.filtered_mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
