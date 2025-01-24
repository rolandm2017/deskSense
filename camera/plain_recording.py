import cv2
import time
from datetime import datetime

from src.timestamp import add_timestamp
from src.startup_shutdown import setup_interrupt_handler, shutdown
from constants import SECONDS_PER_MIN


CHOSEN_FPS = 30  # Change from 5 to 30

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

# OUT_FILE = 'test_material.avi'

TOTAL_MIN_FOR_VID = 0.16666666  # 10 sec vid


cap = init_webcam(CHOSEN_FPS)
# output_vid = setup_frame_writer(CHOSEN_FPS)


base_name = "test_out-Still_Then_Moving"
video_ending = ".avi"


max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN

# GOAL: Record ten videos that are a minute long each
current_index = 1


def name_new_vid(base_name, index, ending):
    return base_name + str(index) + ending


first_vid_name = name_new_vid(
    base_name, current_index, video_ending)

output_vid_name = first_vid_name

output_vid = initialize_new_vid(output_vid_name)

frames_per_segment = CHOSEN_FPS * max_duration_in_sec
# Right after frames_per_segment calculation
print(f"Need {frames_per_segment} frames for {
      max_duration_in_sec} seconds at {CHOSEN_FPS} FPS")


def log_finish_video(frame_count, output_vid_name, current_index):
    print("[LOG] Ending on frame " + str(frame_count) +
          " for video " + output_vid_name)
    print(f"[LOG] Completed video segment {current_index-1}")


start_time = time.time()
frame_count = 0
interrupt_called = False
last_second = None

while True:
    ret, frame = cap.read()
    if interrupt_called:
        shutdown(cap, output_vid)
    if ret:
        frame_count += 1
        frame = add_timestamp(frame)
        output_vid.write(frame)

        current = datetime.now()
        if current.second != last_second:
            print(f"{current.minute:02d}:{current.second:02d}")
            last_second = current.second

        # Check if we've reached 30 seconds (0.5 minutes)
        if frame_count > frames_per_segment:
            log_finish_video(frame_count, output_vid_name, current_index)
            output_vid.release()
            print("Video released")
            exit()
