import pytest
import numpy as np
import cv2
import os

from camera.src.motionDetector.process_motion_in_video import process_motion_in_video
from src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.detect_using_diff import detect_motion
from src.video_util import extract_frame, extract_frames

from tests.file_names import with_timestamps_still, test_vid_dir

# cv2.startWindowThread()
# cv2.namedWindow('Motion Detection', cv2.WINDOW_NORMAL)

print(f"DISPLAY env var: {os.getenv('DISPLAY')}")

#
# #
# # # Test that the timestamps are not caught in mo detect
# #
# #
#

path = test_vid_dir + with_timestamps_still

print(path)

process_motion_in_video(
    video_path=path,
    output_path="output.avi",
    threshold=30,
    min_motion_pixels=500,
    display_while_processing=True  # Set this to True
)

print("Have a nice day")
