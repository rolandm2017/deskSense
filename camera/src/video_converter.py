import cv2
import os
import traceback

import numpy as np

import threading

from .motionDetector.motion_detector import process_motion_in_video
from .blackFrameFilter.black_frame_maker import filter_with_black
from .compression.compressor import convert_for_ml


class VideoConverter(threading.Thread):
    def __init__(self, input_path, output_path, on_finish=None):
        super().__init__()
        self.input_path = input_path
        self.filtered_name = output_path["filtered"]
        self.compressed_name = output_path["compressed"]
        self.finish_handler = on_finish
        self.daemon = True  # Allow program to exit even if thread is running

    def run(self):
        try:
            #
            # # # Is a pipeline
            #
            motion_vid, motion_frames = process_motion_in_video(
                self.input_path, self.filtered_name)
            black_frame_filter_vid = filter_with_black(
                motion_vid, motion_frames)
            compressed_file = convert_for_ml(
                black_frame_filter_vid, self.compressed_name)
            if self.finish_handler:
                # Likely sends it to Castle
                self.finish_handler(compressed_file)
        except Exception as e:
            print(traceback.print_exc())
            print(f"[err] Error converting video: {e}")
