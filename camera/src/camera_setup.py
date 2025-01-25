import cv2

from ..main import CHOSEN_FPS
from .constants import CHOSEN_CODEC
from .codecs import get_FFV1_codec, get_HFYU_codec, get_MJPG_codec, get_mp4v_codec, get_XVID_codec


def get_codec(choice):
    if choice == "mp4v":
        return get_mp4v_codec()
    if choice == "XVID":
        return get_XVID_codec()
    if choice == "MJPG":
        return get_MJPG_codec()
    if choice == "HFYU":
        return get_HFYU_codec()
    if choice == "FFV1":
        return get_FFV1_codec()


def init_webcam(chosen_fps):
    cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
    cap.set(cv2.CAP_PROP_FPS, chosen_fps)
    return cap


def setup_frame_writer(chosen_fps):
    fourcc = get_codec(CHOSEN_CODEC)
    # Add explicit isColor parameter
    out = cv2.VideoWriter('output.avi', fourcc,
                          chosen_fps, (640, 480), isColor=True)
    if not out.isOpened():
        print("Failed to initialize VideoWriter")
        return None
    return out


def initialize_new_vid(name, chosen_fps=CHOSEN_FPS):
    fourcc = get_codec(CHOSEN_CODEC)
    # Add explicit isColor parameter)
    out = cv2.VideoWriter(name, fourcc, chosen_fps, (640, 480), isColor=True)

    return out

#
# #
# # # Initially was like this in main.py:
#
# cap = cv2.VideoCapture(0)  # 0 is usually the built-in webcam
# cap.set(cv2.CAP_PROP_FPS, CHOSEN_FPS)
# fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('output.avi', fourcc, CHOSEN_FPS, (640, 480))
