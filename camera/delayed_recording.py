import cv2
import time
from datetime import datetime
from camera.src.frames.preprocess import preprocess_frame
from src.timestamp import add_timestamp
from src.startup_shutdown import setup_interrupt_handler, shutdown
from camera.src.config.constants import SECONDS_PER_MIN, CHOSEN_CODEC
from camera.src.recording.codecs import get_FFV1_codec, get_HFYU_codec, get_MJPG_codec, get_mp4v_codec, get_XVID_codec

WARMUP_DURATION = 3  # seconds
RECORDING_DURATION = 3  # seconds
CHOSEN_FPS = 30
DISPLAY_WINDOW_NAME = 'Live Recording'


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


output_dir = "output/"
base_name = "MY_STILLNESS_VID"
video_ending = ".avi"


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


def record_video(cap, output_vid, duration):
    print("Starting recording...")
    recording_start = time.time()
    frame_count = 0
    frames_needed = duration * CHOSEN_FPS
    last_second = None

    while frame_count < frames_needed:
        ret, frame = cap.read()
        if not ret or interrupt_called:
            return False

        frame_count += 1
        output_vid.write(frame)

        current = datetime.now()
        if current.second != last_second:
            print(f"Recording: {
                  int(duration - (time.time() - recording_start))} seconds remaining")
            last_second = current.second

        cv2.imshow(DISPLAY_WINDOW_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False

    return frame_count


def main():
    global interrupt_called
    interrupt_called = False

    cap = init_webcam(CHOSEN_FPS)
    output_vid_name = base_name + video_ending
    print("[LOG] output vid name: " + output_vid_name)

    try:
        if not wait_for_warmup(cap, WARMUP_DURATION):
            return

        output_vid = initialize_new_vid(output_vid_name)
        frame_count = record_video(cap, output_vid, RECORDING_DURATION)

        if frame_count:
            print(f"Recording complete. Captured {frame_count} frames")

    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        cv2.destroyAllWindows()
        cap.release()
        if 'output_vid' in locals():
            output_vid.release()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
