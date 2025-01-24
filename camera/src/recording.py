import cv2
from datetime import datetime
from contextlib import contextmanager

from ..constants import CHOSEN_FPS
from .startup_shutdown import setup_interrupt_handler, shutdown
from .logging import log_finish_video

from .timestamp import add_timestamp


@contextmanager
def interrupt_handler():
    """Context manager for handling interrupts"""
    original_handler = signal.getsignal(signal.SIGINT)
    interrupted = False

    def handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\nCtrl+C detected. Executing graceful stop...")

    try:
        signal.signal(signal.SIGINT, handler)
        yield lambda: interrupted
    finally:
        signal.signal(signal.SIGINT, original_handler)


def init_webcam(chosen_fps):
    cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
    cap.set(cv2.CAP_PROP_FPS, chosen_fps)
    return cap


def setup_frame_writer(chosen_fps, output_dir):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_dir + 'output.avi',
                          fourcc, chosen_fps, (640, 480))
    return out


def initialize_new_vid(name, output_dir, chosen_fps=CHOSEN_FPS):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_dir + name, fourcc, 30, (640, 480))
    return out


def process_frame(frame, frame_count, output_vid):
    """Process a single frame of video"""
    frame = add_timestamp(frame)
    output_vid.write(frame)

    current = datetime.now()
    # Log current time if second has changed
    if current.second != process_frame.last_second:
        print(f"{current.minute:02d}:{current.second:02d}")
        process_frame.last_second = current.second

    return frame_count + 1


def record_n_sec_video(n, title, output_dir="output/", should_continue=lambda: True):
    """
    Record n seconds of video to the specified title.

    Args:
        n (int): Number of seconds to record
        title (str): Output filename (must end in .avi)
        output_dir (str): Directory to save the video
        should_continue (callable): Function that returns False when recording should stop

    Returns:
        str: Path to the recorded video file
    """
    total_frames = n * 30
    if not title.endswith(".avi"):
        raise ValueError("Title must be an .avi file")

    # Initialize recording setup
    capture = init_webcam(CHOSEN_FPS)
    output_vid = initialize_new_vid(title, output_dir)
    frame_count = 0
    last_second = None

    try:
        while frame_count <= total_frames and should_continue():
            ret, frame = capture.read()
            if not ret:
                continue

            frame_count, last_second = process_frame(
                frame,
                frame_count,
                output_vid,
                last_second
            )

        log_finish_video(frame_count, title)
        return output_dir + title
    finally:
        shutdown(capture, output_vid)
