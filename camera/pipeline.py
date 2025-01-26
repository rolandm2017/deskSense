import cv2
import time
from datetime import datetime, timedelta

from src.frames.timestamp import add_timestamp
from src.video_converter import VideoConverter
from src.startup_shutdown import setup_interrupt_handler, shutdown
from src.util.file_util import get_compressed_name_for_vid, get_filtered_vid_name, name_new_vid
from src.recording.recording import init_webcam, initialize_new_vid
from src.config.constants import SECONDS_PER_MIN, CHOSEN_FPS
from src.util.path_manager import VideoPathManager
from src.util.logging import log_finish_video


interrupt_called = None


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True
    cv2.destroyAllWindows()  # Cleanup display windows


setup_interrupt_handler(signal_handler)

DISPLAY_WINDOW_NAME = 'Live Recording'


def activate_pipeline(finished_vid_name, path_manager):
    black_filtered_vid = get_filtered_vid_name(finished_vid_name)
    compressed_out_name = get_compressed_name_for_vid(finished_vid_name)
    discard_name = "discard-" + finished_vid_name
    out_names = {"filtered": black_filtered_vid,
                 "compressed": compressed_out_name, "discard": discard_name}
    converter = VideoConverter(finished_vid_name, out_names, path_manager)
    converter.start()


def run_recording_process(min_of_test, vid_duration_in_sec):
    current_index = 0

    base_name = "VVVVV_Test"
    video_ending = ".avi"

    path_manager = VideoPathManager(project_root=".")

    frames_per_segment = CHOSEN_FPS * vid_duration_in_sec

    first_vid_name = name_new_vid(base_name, current_index, video_ending)
    print("Look for " + first_vid_name)
    output_vid_name = first_vid_name

    output_vid = initialize_new_vid(
        output_vid_name, path_manager.raw)

    capture = init_webcam(CHOSEN_FPS)

    frame_count = 0

    last_second = None

    end_time = datetime.now() + timedelta(minutes=min_of_test)

    waiting_for_test_to_conclude = datetime.now() < end_time
    try:
        while waiting_for_test_to_conclude:
            ret, frame = capture.read()
            if interrupt_called:
                cv2.destroyAllWindows()
                shutdown(capture, output_vid)
                break

            if ret:
                frame_count += 1
                frame_with_timestamp = add_timestamp(frame)
                output_vid.write(frame_with_timestamp)

                try:
                    window_name = "@@@ " + DISPLAY_WINDOW_NAME + \
                        "_-_" + str(current_index)
                    cv2.imshow(window_name, frame_with_timestamp)
                    # Press 'q' to quit
                    # FIXME: auto close window when the uh, when the video ends
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
                    # Cleanup window
                    cv2.destroyAllWindows()
                    log_finish_video(
                        frame_count, output_vid_name, current_index)
                    output_vid.release()
                    current_index += 1

                    frame_count = 0

                    activate_pipeline(output_vid_name, path_manager)

                    output_vid_name = name_new_vid(
                        base_name, current_index, video_ending)
                    output_vid = initialize_new_vid(
                        output_vid_name, path_manager.raw)

                    waiting_for_test_to_conclude = datetime.now() < end_time

    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        shutdown(capture, output_vid)
    finally:
        print("done! \n\n ++ ++ \n \n ++ ++")
        cv2.destroyAllWindows()


if __name__ == "__main__":
    min_of_test = 1
    duration_of_video_in_sec = 10
    yielded_videos = min_of_test * 60 / duration_of_video_in_sec

    print(f"Getting {yielded_videos} videos in {min_of_test} min")

    run_recording_process(min_of_test, duration_of_video_in_sec)
