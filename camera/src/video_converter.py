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
    def __init__(self, input_path, output_path, path_manager, on_finish=None):
        #
        # # # Is a pipeline
        #
        super().__init__()
        self.input_path = input_path
        self.filtered_name = output_path["filtered"]
        self.compressed_name = output_path["compressed"]
        self.discard_name = output_path["discard"]
        self.finish_handler = on_finish
        self.path_manager = path_manager
        self.foreground_motion_detector = ForegroundMotionDetector()
        self.daemon = True  # Allow program to exit even if thread is running

    def run(self):
        try:

            with open('/tmp/video_conversion.status', 'w') as f:
                f.write('running')

            frames = extract_frames(
                self.path_manager.raw_path(self.input_path))
            # TODO:
            # TODO:
            # TODO: ... use the Exit Detector.
            # TODO: Run Exit Detector continually.
            # TODO:  # if the motion stops, AND objects have left the frame, insert black
            # TODO: If motion stops, BUT no objects have left the frame, presume Obj still in frame.
            # TODO:
            motion_frames = get_frames_with_motion(
                frames, self.foreground_motion_detector)
            # FIXME: I think it's at 999 fps these frames
            put_still_frames_into_discard(
                frames, motion_frames, self.discard_name, self.path_manager.discard)

            black_frame_filter_vid = filter_with_black(
                self.path_manager.raw_path(self.input_path), motion_frames, self.path_manager)

            compressed_file_path = self.path_manager.processed_path(
                self.compressed_name)
            compressed_file = convert_for_ml(
                black_frame_filter_vid, compressed_file_path)

            if self.finish_handler:
                self.finish_handler(compressed_file)

            with open('/tmp/video_conversion.status', 'w') as f:
                f.write('done')
        except Exception as e:
            with open('/tmp/video_conversion.status', 'w') as f:
                f.write(f'error: {str(e)}')
            print(traceback.print_exc())
            print(f"[err] Error converting video: {e}")
