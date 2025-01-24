import cv2
import time

from src.timestamp import add_timestamp
from src.compression import convert_for_ml
from src.startup_shutdown import setup_interrupt_handler, shutdown
# from src.camera_setup import setup_frame_writer, init_webcam, initialize_new_vid
from constants import video_duration_in_minutes, SECONDS_PER_MIN


# See Claude.md before changing above 5
CHOSEN_FPS = 5  # Set to 5 FPS
MAX_EVER = 5  # Do not change this

if CHOSEN_FPS > MAX_EVER:
    raise ValueError("Five is the max FPS")

output_dir = "output/"


def init_webcam(chosen_fps):
    cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
    cap.set(cv2.CAP_PROP_FPS, chosen_fps)
    return cap


def setup_frame_writer(chosen_fps):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_dir + 'output.avi',
                          fourcc, chosen_fps, (640, 480))
    return out


def initialize_new_vid(name, chosen_fps=CHOSEN_FPS):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_dir + name, fourcc, chosen_fps, (640, 480))
    return out


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


setup_interrupt_handler(signal_handler)

OUT_FILE = 'outputffff.avi'
COMPRESSED_FILE = "compressed.avi"

TOTAL_MIN_FOR_VID = 0.5


cap = init_webcam(CHOSEN_FPS)
output_vid = setup_frame_writer(CHOSEN_FPS)


base_name = "output"
video_ending = ".avi"


def join_video_name(base_name, middle, ending):
    return base_name + middle + ending


current_vid = initialize_new_vid(base_name)

# Create video writermax_duration


max_duration = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN

# GOAL: Record ten videos that are a minute long each


def get_loop_index_from_video(video_name):
    split_up = video_name.split("_")
    iteration = int(split_up[1].split(".")[0])
    return iteration


def make_name_of_new_vid(base_name, loop_idx, ending):
    return base_name + str(loop_idx) + video_ending


start_time = time.time()
# FIXME: Frame counter looks bunk
# FIXME: Timestamp bottom right is bunk
current_index = 1
frame_count = 0
interrupt_called = False
while True:
    ret, frame = cap.read()
    if interrupt_called:
        shutdown(cap, output_vid)
    if ret:
        frame_count += 1
        frame = add_timestamp(frame)
        output_vid.write(frame)

        # TODO: detect whether I am present in the screen or not using um, um, motion detection

        current_time = time.time()
        elapsed_time = current_time - start_time

        # Print progress every 5 seconds without sleeping
        if int(elapsed_time) % 5 == 0:
            minutes = int(elapsed_time / 60)
            seconds = int(elapsed_time % 60)
            print(f"{minutes}m{seconds:02d} on frame {frame_count}")

        # Check if we've reached 30 seconds (0.5 minutes)
        if elapsed_time >= max_duration:
            current_index += 1
            output_vid.release()

            print(f"Completed video segment {current_index-1}")

            output_vid_name = make_name_of_new_vid(
                base_name, current_index, video_ending)
            output_vid = initialize_new_vid(output_vid_name)

            start_time = time.time()  # Reset timer
            frame_count = 0  # Reset frame count


# #
# ### Make a separate process compress the video
# #
compressed_file_path = convert_for_ml(OUT_FILE, COMPRESSED_FILE)


def send_video_to_castle(video_path):
    # TODO: Send the content to Castle for processing
    print(video_path)
