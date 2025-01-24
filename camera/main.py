import cv2
import time
from datetime import datetime

from src.timestamp import add_timestamp
from src.compression import convert_for_ml, VideoConverter
from src.motionDetector.v2detector import detect_motion
from src.startup_shutdown import setup_interrupt_handler, shutdown
from src.util import get_compressed_name_for_vid, get_filtered_vid_name, get_loop_index_from_video, name_new_vid
from src.recording import init_webcam, initialize_new_vid
from constants import SECONDS_PER_MIN, CHOSEN_FPS


output_dir = "output/"


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


setup_interrupt_handler(signal_handler)

OUT_FILE = 'outputffff.avi'
COMPRESSED_FILE = "compressed.avi"

TOTAL_MIN_FOR_VID = 0.16666666  # 10 sec vid


capture = init_webcam(CHOSEN_FPS)
# output_vid = setup_frame_writer(CHOSEN_FPS)


base_name = "output"
video_ending = ".avi"


max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN

# GOAL: Record ten videos that are a minute long each
current_index = 1


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
    black_filtered_vid = get_filtered_vid_name(finished_vid_name)
    compressed_out_name = get_compressed_name_for_vid(black_filtered_vid)
    names = {"filtered": black_filtered_vid, "compressed": compressed_out_name}
    converter = VideoConverter(
        finished_vid_name, names, on_finish)
    converter.start()


start_time = time.time()
# FIXME: Frame counter looks bunk
# FIXME: Timestamp bottom right is bunk
frame_count = 0
interrupt_called = False
last_second = None


def run_recording_process():
    while True:
        ret, frame = capture.read()
        if interrupt_called:
            shutdown(capture, output_vid)
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

# Fantasy footbal

# record_video(vid_name).fill_black_on_still_frames().compress()
# TODO: Something like a log of what video file covers from when to when?
