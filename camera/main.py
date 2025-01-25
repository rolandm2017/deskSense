import cv2
import time
from datetime import datetime

from src.timestamp import add_timestamp
from src.compression.compressor import convert_for_ml
from src.video_converter import VideoConverter
from camera.src.motionDetector.detect_using_diff import detect_motion
from src.startup_shutdown import setup_interrupt_handler, shutdown
from src.file_util import get_compressed_name_for_vid, get_filtered_vid_name, get_loop_index_from_video, name_new_vid
from src.recording import init_webcam, initialize_new_vid
from src.constants import SECONDS_PER_MIN, CHOSEN_FPS


output_dir = "output/"

interrupt_called = None


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True
    cv2.destroyAllWindows()  # Cleanup display windows


setup_interrupt_handler(signal_handler)

COMPRESSED_FILE = "compressed.avi"
TOTAL_MIN_FOR_VID = 3 / 60  # 10 sec vid
DISPLAY_WINDOW_NAME = 'Live Recording'

capture = init_webcam(CHOSEN_FPS)
base_name = "3sec_Motion"
video_ending = ".avi"
max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN
current_index = 1

first_vid_name = name_new_vid(base_name, current_index, video_ending)
output_vid_name = first_vid_name
output_vid = initialize_new_vid(output_vid_name, output_dir)

frames_per_segment = CHOSEN_FPS * max_duration_in_sec
print(f"Need {frames_per_segment} frames for {
      max_duration_in_sec} seconds at {CHOSEN_FPS} FPS")


def log_finish_video(frame_count, output_vid_name, current_index):
    print("[LOG] Ending on frame " + str(frame_count) +
          " for video " + output_vid_name)
    print(f"[LOG] Completed video segment {current_index-1}")


def send_to_castle(video_path):
    print(video_path)


def compress_finished_vid(finished_vid_name, on_finish):
    black_filtered_vid = get_filtered_vid_name(finished_vid_name)
    compressed_out_name = get_compressed_name_for_vid(black_filtered_vid)
    names = {"filtered": black_filtered_vid, "compressed": compressed_out_name}
    converter = VideoConverter(finished_vid_name, names, on_finish)
    converter.start()


def run_recording_process(display_while_recording=True):
    global current_index, output_vid, output_vid_name
    frame_count = 0
    start_time = time.time()
    last_second = None

    try:
        while True:
            ret, frame = capture.read()
            if interrupt_called:
                cv2.destroyAllWindows()
                shutdown(capture, output_vid)
                break

            if ret:
                frame_count += 1
                frame_with_timestamp = add_timestamp(frame)
                output_vid.write(frame_with_timestamp)

                if display_while_recording:
                    try:
                        cv2.imshow(DISPLAY_WINDOW_NAME, frame_with_timestamp)
                        # Press 'q' to quit
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            cv2.destroyAllWindows()
                            shutdown(capture, output_vid)
                            break
                    except Exception as e:
                        print(f"Display error: {e}")

                current = datetime.now()
                if current.second != last_second:
                    print(f"{current.minute:02d}:{current.second:02d}")
                    last_second = current.second

                if frame_count > frames_per_segment:
                    log_finish_video(
                        frame_count, output_vid_name, current_index)
                    output_vid.release()
                    current_index += 1

                    start_time = time.time()
                    frame_count = 0

                    compress_finished_vid(output_vid_name, send_to_castle)

                    output_vid_name = name_new_vid(
                        base_name, current_index, video_ending)
                    output_vid = initialize_new_vid(
                        output_vid_name, output_dir)
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        shutdown(capture, output_vid)
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run_recording_process(display_while_recording=True)
