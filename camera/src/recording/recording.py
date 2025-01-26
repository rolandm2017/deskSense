import cv2
from datetime import datetime
from contextlib import contextmanager
import signal

from ..config.constants import CHOSEN_FPS, CHOSEN_CODEC
from ..startup_shutdown import setup_interrupt_handler, shutdown
from ..util.logging import log_ending
from .codecs import get_codec

from ..frames.timestamp import add_timestamp


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
    fourcc = get_codec()
    out = cv2.VideoWriter(output_dir + 'output.avi',
                          fourcc, chosen_fps, (640, 480))
    return out


def initialize_new_vid(name, output_dir, chosen_fps=CHOSEN_FPS):
    """VideoWriter object manages writing video frames to a file"""
    fourcc = get_codec()
    print(output_dir, '49ru')
    out = cv2.VideoWriter(str(output_dir / name),
                          fourcc, chosen_fps, (640, 480))
    return out


def process_frame(frame, frame_count, output_vid):
    """Process a single frame of video"""
    frame = add_timestamp(frame)
    output_vid.write(frame)

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

    try:
        while frame_count <= total_frames and should_continue():
            ret, frame = capture.read()
            if not ret:
                continue

            frame_count = process_frame(
                frame,
                frame_count,
                output_vid,
            )

        log_ending(frame_count, title)
        return output_dir + title
    finally:
        shutdown(capture, output_vid)
