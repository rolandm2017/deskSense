from datetime import datetime
import cv2


def preprocess_frame(frame):
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    # Convert to grayscale
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    return gray


def preprocess_blurring(frame):
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    return blurred
