import pytest
import numpy as np
import cv2

from camera.src.blackFrameFilter.black_frame_maker import make_black_frame, filter_with_black
from camera.src.motionDetector.v2detector import detect_motion
from camera.src.motionDetector.video_detector import process_motion_in_video
from camera.src.video_util import extract_frame, extract_frames

from tests.file_names import with_timestamps_still

#
# #
# # # Test that the timestamps are not caught in mo detect
# #
# #
#
