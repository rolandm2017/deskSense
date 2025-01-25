import cv2
import numpy as np

print("OpenCV version:", cv2.__version__)

# Create a simple black image
img = np.zeros((300, 300, 3), dtype=np.uint8)

try:
    print("Attempting to create window...")
    cv2.namedWindow('test', cv2.WINDOW_NORMAL)  # Use NORMAL instead of OPENGL
    print("Window created, attempting to show image...")
    cv2.imshow('test', img)
    print("Image shown, waiting for key...")
    cv2.waitKey(2000)  # Wait 2 seconds
    print("Cleanup...")
    cv2.destroyAllWindows()
except Exception as e:
    print(f"Error: {str(e)}")
