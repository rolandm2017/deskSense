from datetime import datetime
import cv2


def add_timestamp(frame):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Get frame dimensions
    height, width = frame.shape[:2]
    # Calculate text size and position
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    text_size = cv2.getTextSize(timestamp, font, font_scale, thickness)[0]
    # Position text in bottom right with padding
    x = width - text_size[0] - 10
    y = height - 10
    # Add black background for better visibility
    cv2.putText(frame, timestamp, (x, y), font,
                font_scale, (0, 0, 0), thickness + 1)
    # Add white text
    cv2.putText(frame, timestamp, (x, y), font,
                font_scale, (255, 255, 255), thickness)
    return frame
