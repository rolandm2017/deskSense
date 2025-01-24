import cv2
import time
import signal
import sys


from .src.compression import convert_for_ml


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


def shutdown():
    cap.release()            # Release webcam to make it available for other applications
    out.release()            # Close video file to ensure it's properly saved
    cv2.destroyAllWindows()  # Clean up any OpenCV windows to free memory
    sys.exit(0)              # Exit program with success status code


def setup_interrupt_handler():
    """
    Registers a SIGINT (Ctrl+C) handler for graceful program termination.
    This ensures video files are properly closed and resources released when
    the user interrupts recording.
    """
    signal.signal(signal.SIGINT, signal_handler)


setup_interrupt_handler()


OUT_FILE = 'output.avi'
COMPRESSED_FILE = "compressed.avi"

duration_in_minutes = 30

total_frames_per_duration_dict = {
    "5 min": 1500,  # 5 min * 60 sec * 5 fps
    "10 min": 3000,  # 10 min * 60 sec * 5 fps
    "15 min": 4500,  # 15 min * 60 sec * 5 fps
    "20 min": 6000,  # 20 min * 60 sec * 5 fps
    "25 min": 7500,  # 25 min * 60 sec * 5 fps
    "30 min": 9000
}

# See Claude.md before changing above 5
CHOSEN_FPS = 5  # Set to 5 FPS
MAX_EVER = 5

if CHOSEN_FPS > MAX_EVER:
    raise ValueError("Five is the max FPS")


cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
cap.set(cv2.CAP_PROP_FPS, CHOSEN_FPS)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, CHOSEN_FPS, (640, 480))


start_time = time.time()

# Create video writermax_duration
# TOTAL_MIN_FOR_VID = 30
# SECONDS_PER_MIN = 60
total_seconds_per_vid = 1800  # 30 * 60 = 1,800
# TOTAL_FRAMES = total_frames_per_duration_dict["30 min"]

seconds_per_min = 60

max_duration = duration_in_minutes * seconds_per_min

frame_count = 0
interrupt_called = False
while True:
    ret, frame = cap.read()
    if interrupt_called:
        shutdown()
    if ret:
        frame_count += 1
        out.write(frame)

        current_time = time.time()
        elapsed_time = current_time - start_time

        if elapsed_time > max_duration:  # Check if 60 minutes have passed
            print("60 minutes reached. Stopping the recording.")
            break


# #
# ### Make a separate process compress the video
# #
compressed_file_path = convert_for_ml(OUT_FILE, COMPRESSED_FILE)

# TODO: Send the content to Castle for processing


def send_video_to_castle(video_path):
    print(video_path)


# TODO: detect whether I am present in the screen or not using um, um, motion detection
