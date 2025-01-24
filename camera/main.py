import cv2
import time
from datetime import datetime

from src.timestamp import add_timestamp
from src.compression import convert_for_ml, VideoConverter
from src.motionDetector.v2detector import detect_motion
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
    out = cv2.VideoWriter(output_dir + name, fourcc, 30, (640, 480))
    return out


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


setup_interrupt_handler(signal_handler)

OUT_FILE = 'outputffff.avi'
COMPRESSED_FILE = "compressed.avi"

TOTAL_MIN_FOR_VID = 0.16666666  # 10 sec vid


cap = init_webcam(CHOSEN_FPS)
# output_vid = setup_frame_writer(CHOSEN_FPS)


base_name = "output"
video_ending = ".avi"


def join_video_name(base_name, middle, ending):
    return base_name + middle + ending


max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN

# GOAL: Record ten videos that are a minute long each
current_index = 1


def get_loop_index_from_video(video_name):
    split_up = video_name.split("_")
    iteration = int(split_up[1].split(".")[0])
    return iteration


def name_new_vid(base_name, index, ending):
    return base_name + str(index) + ending


def get_compressed_name_for_vid(s):
    name, extension = s.split(".")
    return name + "_compressed" + "." + extension


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


def send_to_castle(video_path):
    # TODO: Send the content to Castle for processing
    print(video_path)


def compress_finished_vid(finished_vid_name, on_finish):
    compressed_out_name = get_compressed_name_for_vid(finished_vid_name)
    converter = VideoConverter(
        finished_vid_name, compressed_out_name, on_finish)
    converter.start()


start_time = time.time()
# FIXME: Frame counter looks bunk
# FIXME: Timestamp bottom right is bunk
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

        # TODO: detect whether I am present in the screen or not using um, um, motion detection

        current = datetime.now()
        if current.second != last_second:
            print(f"{current.minute:02d}:{current.second:02d}")
            last_second = current.second

        # Check if we've reached 30 seconds (0.5 minutes)
        if frame_count > frames_per_segment:
            log_finish_video(frame_count, output_vid_name, current_index)
            output_vid.release()
            current_index += 1

            # Cleanup starting circumstances
            start_time = time.time()  # Reset timer
            frame_count = 0  # Reset frame count

            check_for_motion()
            if no_motion:
                black_square(frame)
                # Handle compression
            compress_finished_vid(output_vid_name, send_to_castle)
            # to_be_compressed = output_vid_name
            # compressed_out_name = get_compressed_name_for_vid(output_vid_name)
            # converter = VideoConverter(to_be_compressed, compressed_out_name)
            # converter.start()

            # Update video name for next round
            output_vid_name = name_new_vid(
                base_name, current_index, video_ending)
            # Update for next loop
            output_vid = initialize_new_vid(output_vid_name)
