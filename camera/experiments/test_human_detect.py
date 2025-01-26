import cv2

from src.util.video_util import extract_frames

TEST_FILE = "output/raw_recordings/VVVVV_Test0.avi"
TEST_FILE2 = "output/raw_recordings/VV_Test1.avi"

frames = extract_frames(TEST_FILE2)


# Initialize HOG detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

try:
    out = []
    for frame in frames:
        # Read image or video frame
        # Detect people
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes, weights = hog.detectMultiScale(
            gray_frame,
            winStride=(2, 2),  # Smaller stride for more sensitivity
            padding=(16, 16),  # Larger padding for edge detection
            scale=1.01,        # Smaller scale for more sensitivity
            hitThreshold=0     # You can adjust this if needed
        )
        print("len boxes", len(boxes))
        # Draw boxes around detected people
        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        out.append(frame)
except KeyboardInterrupt:
    print("shutting down")
    pass

# Stitch video together
height, width = out[0].shape[:2]
fps = 30  # Set your desired framerate

# Create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
output_video = cv2.VideoWriter(
    'FFFFF_output.avi', fourcc, fps, (width, height))

# Write frames
for frame in out:
    output_video.write(frame)

# Release video writer
output_video.release()
print("release")
