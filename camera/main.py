import cv2

cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
cap.set(cv2.CAP_PROP_FPS, 4)  # Set to 4 FPS

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 4.0, (640,480))

while True:
    ret, frame = cap.read()
    if ret:
        out.write(frame)

# TODO: Make a separate process compress the video

# TODO: Send the content to Castle for processing