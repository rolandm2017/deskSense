import cv2

from ..config.constants import CHOSEN_CODEC


def get_codec(choice=CHOSEN_CODEC):
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


def get_claude_recommended_ML_codec():
    return get_MJPG_codec()


def get_max_quality_codec():
    """Large file size, probably just ok for recording"""
    return get_XVID_codec()


def get_mp4v_codec():
    """Use this one"""
    # H.264: Good compression, smaller files, industry standard
    return cv2.VideoWriter_fourcc(*'mp4v')


def get_XVID_codec():
    # Xvid: Open source, decent compression, widely compatible
    return cv2.VideoWriter_fourcc(*'XVID')  # Xvid codec


def get_MJPG_codec():
    # Motion JPEG: High quality, large files, good for ML as each frame preserved
    return cv2.VideoWriter_fourcc(*'MJPG')


def get_HFYU_codec():
    return cv2.VideoWriter_fourcc(*'HFYU')  # HuffYUV - lossless


def get_FFV1_codec():
    return cv2.VideoWriter_fourcc(*'FFV1')  # FFV1 - lossless
