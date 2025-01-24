import cv2
import time

from .src.compression import convert_for_ml
from src.startup_shutdown import setup_interrupt_handler, shutdown
from src.camera_setup import setup_frame_writer, init_webcam
from constants import video_duration_in_minutes


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


setup_interrupt_handler(signal_handler)

OUT_FILE = 'output.avi'
COMPRESSED_FILE = "compressed.avi"


# See Claude.md before changing above 5
CHOSEN_FPS = 5  # Set to 5 FPS
MAX_EVER = 5

if CHOSEN_FPS > MAX_EVER:
    raise ValueError("Five is the max FPS")


cap = init_webcam(CHOSEN_FPS)
out = setup_frame_writer(CHOSEN_FPS)


start_time = time.time()

# Create video writermax_duration
# TOTAL_MIN_FOR_VID = 30
# SECONDS_PER_MIN = 60
total_seconds_per_vid = 1800  # 30 * 60 = 1,800
# TOTAL_FRAMES = total_frames_per_duration_dict["30 min"]

seconds_per_min = 60

max_duration = video_duration_in_minutes * seconds_per_min

frame_count = 0
interrupt_called = False
while True:
    ret, frame = cap.read()
    if interrupt_called:
        shutdown()
    if ret:
        frame_count += 1
        out.write(frame)

        # TODO: detect whether I am present in the screen or not using um, um, motion detection

        current_time = time.time()
        elapsed_time = current_time - start_time

        if elapsed_time > max_duration:  # Check if 60 minutes have passed
            print("60 minutes reached. Stopping the recording.")
            break


# #
# ### Make a separate process compress the video
# #
compressed_file_path = convert_for_ml(OUT_FILE, COMPRESSED_FILE)


def send_video_to_castle(video_path):
    # TODO: Send the content to Castle for processing
    print(video_path)
