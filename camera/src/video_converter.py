import cv2
import os
import traceback

import numpy as np

import threading

# FIXME: This is the bad one, use FMD
from .motionDetector.foreground_motion import ForegroundMotionDetector, get_frames_with_motion
from .blackFrameFilter.black_frame_maker import filter_with_black
from .util.video_util import extract_frames, put_still_frames_into_discard
from .compression.compressor import convert_for_ml


class VideoConverter(threading.Thread):
    def __init__(self, input_path, output_path, on_finish):
        super().__init__()
        self.input_path = input_path
        self.filtered_name = output_path["filtered"]
        self.compressed_name = output_path["compressed"]
        self.discard_name = output_path["discard"]
        self.finish_handler = on_finish
        self.foreground_motion_detector = ForegroundMotionDetector()
        self.daemon = True  # Allow program to exit even if thread is running

    def run(self):
        try:
            #
            # # # Is a pipeline
            #
            with open('/tmp/video_conversion.status', 'w') as f:
                f.write('running')

            frames = extract_frames(self.input_path)

            motion_frames = get_frames_with_motion(
                frames, self.foreground_motion_detector)

            put_still_frames_into_discard(
                frames, motion_frames, self.discard_name)

            black_frame_filter_vid = filter_with_black(
                self.input_path, motion_frames)

            compressed_file = convert_for_ml(
                black_frame_filter_vid, self.compressed_name)

            if self.finish_handler:
                self.finish_handler(compressed_file)

            with open('/tmp/video_conversion.status', 'w') as f:
                f.write('done')
        except Exception as e:
            with open('/tmp/video_conversion.status', 'w') as f:
                f.write(f'error: {str(e)}')
            print(traceback.print_exc())
            print(f"[err] Error converting video: {e}")
