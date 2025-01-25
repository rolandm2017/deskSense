import cv2
import numpy as np

from src.motionDetector.foreground_motion import ForegroundMotionDetector, process_motion_in_vid_FMD
from src.video_util import extract_frames


from tests.file_names import (
    test_vid_dir,
    lossless_static
)


vid_path = test_vid_dir + lossless_static
out_path = "TEMPvvvvvZZ" + ".avi"

frames = extract_frames(vid_path)
out, motion_frames = process_motion_in_vid_FMD(vid_path, out_path)

print(motion_frames, '20ru')
