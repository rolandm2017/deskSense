# import cv2
# import time
# from datetime import datetime

# from src.timestamp import add_timestamp
# from src.compression import convert_for_ml, VideoConverter
# from src.motionDetector.v2detector import detect_motion
# from src.startup_shutdown import setup_interrupt_handler, shutdown
# from src.util import get_compressed_name_for_vid, get_filtered_vid_name, get_loop_index_from_video, name_new_vid
# from src.recording import init_webcam, initialize_new_vid
# from src.logging import log_finish_video, log_ending
# from constants import SECONDS_PER_MIN

# CHOSEN_FPS = 30
# TOTAL_MIN_FOR_VID = 0.16666666  # 10 sec vid
# output_dir = "output/"

# # Global state
# interrupt_called = False


# def signal_handler(sig, frame):
#     global interrupt_called
#     print("\nCtrl+C detected. Executing graceful stop...")
#     interrupt_called = True


# def send_to_castle(video_path):
#     # TODO: Send the content to Castle for processing
#     print(video_path)


# def compress_finished_vid(finished_vid_name, on_finish):
#     black_filtered_vid = get_filtered_vid_name(finished_vid_name)
#     compressed_out_name = get_compressed_name_for_vid(black_filtered_vid)
#     names = {"filtered": black_filtered_vid, "compressed": compressed_out_name}
#     converter = VideoConverter(finished_vid_name, names, on_finish)
#     converter.start()


# def process_frame(frame, frame_count, output_vid):
#     """Process a single frame of video"""
#     frame = add_timestamp(frame)
#     output_vid.write(frame)

#     current = datetime.now()
#     # Log current time if second has changed
#     if current.second != process_frame.last_second:
#         print(f"{current.minute:02d}:{current.second:02d}")
#         process_frame.last_second = current.second

#     return frame_count + 1


# # Initialize static variable for process_frame
# process_frame.last_second = None


# def run_recording_process():
#     # Initialize recording setup
#     base_name = "output"
#     video_ending = ".avi"
#     current_index = 1
#     max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN
#     frames_per_segment = CHOSEN_FPS * max_duration_in_sec

#     print(f"Need {frames_per_segment} frames for {
#           max_duration_in_sec} seconds at {CHOSEN_FPS} FPS")

#     # Initialize capture and first video
#     capture = init_webcam(CHOSEN_FPS)
#     output_vid_name = name_new_vid(base_name, current_index, video_ending)
#     output_vid = initialize_new_vid(output_vid_name)

#     frame_count = 0
#     # start_time = time.time()

#     try:
#         while not interrupt_called:
#             ret, frame = capture.read()
#             if not ret:
#                 continue

#             frame_count = process_frame(frame, frame_count, output_vid)

#             # Check if we've reached the frame limit for current segment
#             if frame_count > frames_per_segment:
#                 log_finish_video(frame_count, output_vid_name, current_index)
#                 output_vid.release()
#                 current_index += 1

#                 # Compress the finished video
#                 compress_finished_vid(output_vid_name, send_to_castle)

#                 # Setup for next video segment
#                 frame_count = 0
#                 # start_time = time.time()
#                 output_vid_name = name_new_vid(
#                     base_name, current_index, video_ending)
#                 output_vid = initialize_new_vid(output_vid_name)

#     finally:
#         shutdown(capture, output_vid)


# if __name__ == "__main__":
#     setup_interrupt_handler(signal_handler)
#     run_recording_process()
