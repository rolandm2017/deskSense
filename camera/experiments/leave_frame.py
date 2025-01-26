import cv2
import numpy as np
from collections import deque

# ╔════════════════════════════════════════════════════════════════════╗
# ║                                                                    ║
# ║     ██████╗ ███████╗████████╗███████╗ ██████╗ ████████╗███████╗    ║
# ║    ██╔═══██╗██╔════╝╚══██╔══╝██╔════╝██╔═══██╗╚══██╔══╝██╔════╝    ║
# ║    ██║   ██║███████╗   ██║   █████╗  ██║   ██║   ██║   █████╗      ║
# ║    ██║   ██║╚════██║   ██║   ██╔══╝  ██║   ██║   ██║   ██╔══╝      ║
# ║    ╚██████╔╝███████║   ██║   ███████╗╚██████╔╝   ██║   ███████╗    ║
# ║     ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝    ╚═╝   ╚══════╝    ║
# ║                                                                    ║
# ║   Functionality: Detects when an object leaves the frame of the    ║
# ║   video feed or image sequence. Useful for motion tracking,        ║
# ║   security systems, or machine vision applications.                ║
# ║                                                                    ║
# ╚════════════════════════════════════════════════════════════════════╝


class ExitDetector:
    def __init__(self, min_area=500, blur_size=21, dilate_iterations=2, tracking_history=20):
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        self.min_area = min_area
        self.blur_size = blur_size
        self.dilate_iterations = dilate_iterations
        self.tracking_history = tracking_history
        self.object_histories = {}  # Track object positions over time
        self.next_object_id = 0
        self.frame_dimensions = None

    def _calculate_centroid(self, x, y, w, h):
        return (x + w//2, y + h//2)

    def _assign_or_update_object(self, centroid, current_objects):
        min_distance = float('inf')
        matched_id = None

        # Try to match with existing objects
        for obj_id, history in self.object_histories.items():
            if history and obj_id not in current_objects:
                last_position = history[-1]
                distance = np.sqrt((centroid[0] - last_position[0])**2 +
                                   (centroid[1] - last_position[1])**2)
                if distance < min_distance and distance < 100:  # Max distance threshold
                    min_distance = distance
                    matched_id = obj_id

        if matched_id is None:
            # New object
            matched_id = self.next_object_id
            self.next_object_id += 1
            self.object_histories[matched_id] = deque(
                maxlen=self.tracking_history)

        self.object_histories[matched_id].append(centroid)
        current_objects.add(matched_id)
        return matched_id

    def _check_for_exits(self, current_objects, frame_shape):
        exits = []
        margin = 20  # Pixels from edge to consider as exit

        for obj_id in list(self.object_histories.keys()):
            if obj_id not in current_objects and len(self.object_histories[obj_id]) > 0:
                history = self.object_histories[obj_id]
                last_position = history[-1]

                # Check if the object was near the frame edges
                near_edge = (
                    last_position[0] < margin or  # Left edge
                    last_position[0] > frame_shape[1] - margin or  # Right edge
                    last_position[1] < margin or  # Top edge
                    last_position[1] > frame_shape[0] - margin  # Bottom edge
                )

                if near_edge:
                    # Determine exit direction
                    if last_position[0] < margin:
                        direction = "left"
                    elif last_position[0] > frame_shape[1] - margin:
                        direction = "right"
                    elif last_position[1] < margin:
                        direction = "top"
                    else:
                        direction = "bottom"

                    exits.append((obj_id, direction, last_position))
                    del self.object_histories[obj_id]

        return exits

    def detect_motion_and_exits(self, frame):
        if self.frame_dimensions is None:
            self.frame_dimensions = frame.shape[:2]

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(frame, (self.blur_size, self.blur_size), 0)

        # Background subtraction
        fg_mask = self.background_subtractor.apply(blurred)

        # Morphological operations
        kernel = np.ones((3, 3), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(
            fg_mask, kernel, iterations=self.dilate_iterations)

        # Find contours
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_objects = set()
        motion_regions = []
        object_centroids = {}

        # Process each contour
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append((x, y, w, h))

                # Calculate and track centroid
                centroid = self._calculate_centroid(x, y, w, h)
                obj_id = self._assign_or_update_object(
                    centroid, current_objects)
                object_centroids[obj_id] = centroid

        # Check for objects that have exited
        exits = self._check_for_exits(current_objects, frame.shape)

        return motion_regions, object_centroids, exits, fg_mask


def main():
    cap = cv2.VideoCapture(0)
    detector = ExitDetector(min_area=500)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect motion and exits
        regions, centroids, exits, mask = detector.detect_motion_and_exits(
            frame)

        # Draw motion regions and object IDs
        for x, y, w, h in regions:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        for obj_id, centroid in centroids.items():
            cv2.circle(frame, centroid, 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID: {obj_id}", (centroid[0] - 10, centroid[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Display exit events
        for obj_id, direction, position in exits:
            print(f"Object {obj_id} exited through {direction} edge")
            cv2.putText(frame, f"Exit: {direction}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display results
        cv2.imshow('Motion and Exit Detection', frame)
        cv2.imshow('Foreground Mask', mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
