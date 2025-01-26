import cv2
import time
from datetime import datetime

from camera.src.frames.preprocess import preprocess_frame
from src.timestamp import add_timestamp
from src.startup_shutdown import setup_interrupt_handler, shutdown
from camera.src.config.constants import SECONDS_PER_MIN, CHOSEN_CODEC
from camera.src.recording.codecs import get_FFV1_codec, get_HFYU_codec, get_MJPG_codec, get_mp4v_codec, get_XVID_codec


def get_codec(choice):
    if choice == "mp4v":
        return get_mp4v_codec()
    if choice == "XVID":
        return get_XVID_codec()
    if choice == "MJPG":
        return get_MJPG_codec()
    if choice == "HFYU":
        return get_HFYU_codec()
    if choice == "FFV1":
        return get_FFV1_codec()

###############################################
# * * * * * * * * * * * * * * * * * * * * * #
#                                             #
#          For recording new vids             #
#                                             #
# * * * * * * * * * * * * * * * * * * * * * #
###############################################


WARMUP_DURATION = 3  # seconds to wait before starting recording
RECORDING_DURATION = 3  # seconds to record after warmup
CHOSEN_FPS = 30
DISPLAY_WINDOW_NAME = 'Live Recording'


codec = get_codec("HFYU")

base_name = "Lossless-Movement"
output_dir = "output/"


def init_webcam(chosen_fps):
    cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
    cap.set(cv2.CAP_PROP_FPS, chosen_fps)
    return cap


def setup_frame_writer(chosen_fps):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = get_codec(CHOSEN_CODEC)
    out = cv2.VideoWriter(output_dir + 'output.avi',
                          fourcc, chosen_fps, (640, 480))
    return out


def initialize_new_vid(name, chosen_fps=CHOSEN_FPS):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = get_codec(CHOSEN_CODEC)
    out = cv2.VideoWriter(output_dir + name, fourcc, chosen_fps, (640, 480))
    return out


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True
    cv2.destroyAllWindows()  # Clean up display windows


setup_interrupt_handler(signal_handler)


def wait_for_warmup(cap, duration):
    print(f"Warming up camera for {duration} seconds...")
    warmup_start = time.time()
    last_second = None

    while time.time() - warmup_start < duration:
        ret, frame = cap.read()
        if not ret or interrupt_called:
            return False

        current = datetime.now()
        if current.second != last_second:
            print(
                f"Warmup: {int(duration - (time.time() - warmup_start))} seconds remaining")
            last_second = current.second

        cv2.imshow(DISPLAY_WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False
    return True


TOTAL_MIN_FOR_VID = 3 / 60

cap = init_webcam(CHOSEN_FPS)
video_ending = ".avi"

max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN
current_index = 1


def name_new_vid(base_name, index, ending):
    return base_name + str(index) + ending


first_vid_name = name_new_vid(base_name, "", video_ending)
output_vid_name = first_vid_name
print("[LOG] output vid name: " + output_vid_name)
output_vid = initialize_new_vid(output_vid_name)

frames_per_segment = CHOSEN_FPS * max_duration_in_sec
print(f"Need {frames_per_segment} frames for {
      max_duration_in_sec} seconds at {CHOSEN_FPS} FPS")


def log_finish_video(frame_count, output_vid_name, current_index):
    print("[LOG] Ending on frame " + str(frame_count) +
          " for video " + output_vid_name)
    print(f"[LOG] Completed video segment {current_index-1}")


try:
    start_time = time.time()
    frame_count = 0
    interrupt_called = False
    last_second = None

    while True:
        ret, frame = cap.read()
        if interrupt_called:
            cv2.destroyAllWindows()
            shutdown(cap, output_vid)
            break

        if ret:
            frame_count += 1

            # frame = add_timestamp(frame)
            output_vid.write(frame)

            # Display the frame
            try:
                cv2.imshow(DISPLAY_WINDOW_NAME, frame)
                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print(f"Display error: {e}")

            current = datetime.now()
            if current.second != last_second:
                print(f"{current.minute:02d}:{current.second:02d}")
                last_second = current.second

            # Check if we've reached 30 seconds (0.5 minutes)
            if frame_count > frames_per_segment:
                log_finish_video(frame_count, output_vid_name, current_index)
                output_vid.release()
                print("Video released")
                break

except KeyboardInterrupt:
    print("\nRecording interrupted by user")
finally:
    cv2.destroyAllWindows()
    cap.release()
    output_vid.release()
    print("Cleanup complete")
