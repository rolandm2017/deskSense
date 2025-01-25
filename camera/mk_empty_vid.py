import cv2
import numpy as np


def create_empty_video(output_path, num_frames=0):
    # Create black frame (zeros)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Create video writer
    writer = cv2.VideoWriter(output_path,
                             cv2.VideoWriter_fourcc(*'XVID'),
                             30,  # fps
                             (640, 480))

    # Write black frames
    for _ in range(num_frames):
        writer.write(frame)

    writer.release()


create_empty_video("empty.avi")
