import cv2


def get_claude_recommended_ML_codec():
    # Motion JPEG: High quality, large files, good for ML as each frame preserved
    return cv2.VideoWriter_fourcc(*'MJPG')


def get_max_quality_codec():
    """Large file size, probably just ok for recording"""
    return cv2.VideoWriter_fourcc(*'XVID')  # Xvid codec


def get_high_compression_codec_one():
    """Use this one"""
    # H.264: Good compression, smaller files, industry standard
    return cv2.VideoWriter_fourcc(*'mp4v')


def get_high_compression_codec_two():
    # Xvid: Open source, decent compression, widely compatible
    return cv2.VideoWriter_fourcc(*'XVID')
