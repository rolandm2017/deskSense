import cv2
import time
from datetime import datetime

from src.timestamp import add_timestamp
from src.startup_shutdown import setup_interrupt_handler, shutdown
from src.constants import SECONDS_PER_MIN

###############################################
# * * * * * * * * * * * * * * * * * * * * * #
#                                             #
#          For recording new vids             #
#                                             #
# * * * * * * * * * * * * * * * * * * * * * #
###############################################


CHOSEN_FPS = 30  # Change from 5 to 30
DISPLAY_WINDOW_NAME = 'Live Recording'
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
    cv2.destroyAllWindows()  # Clean up display windows


setup_interrupt_handler(signal_handler)

TOTAL_MIN_FOR_VID = 3 / 60

cap = init_webcam(CHOSEN_FPS)
base_name = "Jan24ffffffffffffffFFFFF"
video_ending = ".avi"

max_duration_in_sec = TOTAL_MIN_FOR_VID * SECONDS_PER_MIN
current_index = 1


def name_new_vid(base_name, index, ending):
    return base_name + str(index) + ending


first_vid_name = name_new_vid(base_name, current_index, video_ending)
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
