import cv2
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Tuple, List, Dict, Set

# https://claude.ai/chat/1991fac6-66ed-485b-b9ea-4c31fb0afe29


@dataclass
class ExitEvent:
    object_id: int
    direction: str
    last_position: Tuple[int, int]
    frame_number: int


class StreamExitDetector:
    def __init__(self, min_area=500, margin=20, tracking_history=20):
        """
        Initialize the stream-based exit detector.

        Args:
            min_area (int): Minimum area of objects to track
            margin (int): Distance from edge to consider as exit zone
            tracking_history (int): Number of positions to remember per object
        """
        self.min_area = min_area
        self.margin = margin
        self.tracking_history = tracking_history

        # Initialize tracking state
        self.frame_count = 0
        self.object_histories = {}
        self.next_object_id = 0
        self.frame_shape = None

        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )

    def _get_contours(self, frame: np.ndarray) -> List:
        """Process frame and get motion contours."""
        # Preprocess frame
        blurred = cv2.GaussianBlur(frame, (21, 21), 0)
        fg_mask = self.bg_subtractor.apply(blurred)

        # Clean up mask
        kernel = np.ones((3, 3), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(
            fg_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        return contours

    def _calculate_centroid(self, x: int, y: int, w: int, h: int) -> Tuple[int, int]:
        """Calculate center point of a bounding box."""
        return (x + w//2, y + h//2)

    def _match_object(self, centroid: Tuple[int, int],
                      current_objects: Set[int]) -> int:
        """Match centroid to existing object or create new one."""
        min_distance = float('inf')
        matched_id = None

        # Try to match with existing objects
        for obj_id, history in self.object_histories.items():
            if history and obj_id not in current_objects:
                # Get position from (pos, frame) tuple
                last_position = history[-1][0]
                distance = np.sqrt(
                    (centroid[0] - last_position[0])**2 +
                    (centroid[1] - last_position[1])**2
                )
                if distance < min_distance and distance < 100:  # Max distance threshold
                    min_distance = distance
                    matched_id = obj_id

        if matched_id is None:
            # Create new object
            matched_id = self.next_object_id
            self.next_object_id += 1
            self.object_histories[matched_id] = deque(
                maxlen=self.tracking_history)

        # Store position and frame number
        self.object_histories[matched_id].append((centroid, self.frame_count))
        current_objects.add(matched_id)
        return matched_id

    def _check_exits(self, current_objects: Set[int]) -> List[ExitEvent]:
        """Check for objects that have exited the frame."""
        exits = []

        for obj_id in list(self.object_histories.keys()):
            if obj_id not in current_objects and len(self.object_histories[obj_id]) > 0:
                last_position, last_frame = self.object_histories[obj_id][-1]

                # Only consider recent disappearances
                if self.frame_count - last_frame > 5:
                    continue

                # Check if object was near edge
                x, y = last_position
                direction = None

                if x < self.margin:
                    direction = "left"
                elif x > self.frame_shape[1] - self.margin:
                    direction = "right"
                elif y < self.margin:
                    direction = "top"
                elif y > self.frame_shape[0] - self.margin:
                    direction = "bottom"

                if direction:
                    exits.append(ExitEvent(
                        object_id=obj_id,
                        direction=direction,
                        last_position=last_position,
                        frame_number=last_frame
                    ))
                    del self.object_histories[obj_id]

        return exits

    def process_frame(self, frame: np.ndarray) -> Tuple[List[ExitEvent], Dict]:
        """
        Process a single frame and detect exits.

        Args:
            frame: numpy array of frame image

        Returns:
            Tuple containing:
            - List of ExitEvent objects for any exits detected
            - Dictionary of current object positions {id: (x,y)}
        """
        if self.frame_shape is None:
            self.frame_shape = frame.shape[:2]

        self.frame_count += 1
        current_objects = set()
        object_positions = {}

        # Get contours from frame
        contours = self._get_contours(frame)

        # Process each contour
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                centroid = self._calculate_centroid(x, y, w, h)

                # Track object
                obj_id = self._match_object(centroid, current_objects)
                object_positions[obj_id] = centroid

        # Check for exits
        exits = self._check_exits(current_objects)

        return exits, object_positions

    def draw_debug(self, frame: np.ndarray,
                   object_positions: Dict[int, Tuple[int, int]],
                   exits: List[ExitEvent]) -> np.ndarray:
        """
        Draw debug visualization on frame.

        Args:
            frame: Input frame
            object_positions: Dictionary of current object positions
            exits: List of exit events

        Returns:
            Frame with debug visualization drawn on it
        """
        debug_frame = frame.copy()

        # Draw margin zones
        cv2.rectangle(debug_frame,
                      (0, 0),
                      (self.frame_shape[1], self.frame_shape[0]),
                      (0, 255, 0), 2)
        cv2.rectangle(debug_frame,
                      (self.margin, self.margin),
                      (self.frame_shape[1] - self.margin,
                          self.frame_shape[0] - self.margin),
                      (0, 255, 0), 1)

        # Draw tracked objects
        for obj_id, pos in object_positions.items():
            cv2.circle(debug_frame, pos, 4, (0, 0, 255), -1)
            cv2.putText(debug_frame, f"ID: {obj_id}",
                        (pos[0] - 10, pos[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Draw exit events
        for exit_event in exits:
            pos = exit_event.last_position
            cv2.putText(debug_frame,
                        f"Exit: {exit_event.direction}",
                        (pos[0] - 20, pos[1] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return debug_frame

# Example usage:


def main():
    cap = cv2.VideoCapture(0)
    detector = StreamExitDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        exits, positions = detector.process_frame(frame)

        # Draw debug visualization
        debug_frame = detector.draw_debug(frame, positions, exits)

        # Print exits
        for exit_event in exits:
            print(f"Object {exit_event.object_id} exited through "
                  f"{exit_event.direction} at frame {exit_event.frame_number}")

        # Display result
        cv2.imshow('Debug View', debug_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
