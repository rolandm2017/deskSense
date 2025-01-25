import numpy as np


def assert_frames_equal(frame1, frame2, tolerance=0):
    """
    Assert that two video frames are identical pixel by pixel.

    Parameters:
    frame1, frame2: numpy arrays representing video frames
    tolerance: optional float for allowing small differences (useful for compression artifacts)

    Raises:
    AssertionError if frames are not equal within tolerance
    ValueError if frames have different shapes
    """
    # Check if frames have same shape
    if frame1.shape != frame2.shape:
        raise ValueError(f"Frames have different shapes: {
                         frame1.shape} vs {frame2.shape}")
    if not 0 <= tolerance <= 1.0:
        raise ValueError("Tolerance must be between 0 and 1")
    if tolerance == 0:
        # Direct equality check for exact matching
        np.testing.assert_array_equal(
            frame1,
            frame2,
            err_msg="Frames are not identical pixel-by-pixel"
        )
    else:
        # Allow for small differences within tolerance
        np.testing.assert_allclose(
            frame1,
            frame2,
            rtol=tolerance,
            err_msg=f"Frames differ by more than {
                tolerance} relative tolerance"
        )

# Example usage:


def compare_video_frames(video1_frames, video2_frames, tolerance=0):
    """
    Compare two arrays of video frames.

    Parameters:
    video1_frames, video2_frames: lists/arrays of frames
    tolerance: optional float for allowing small differences

    Raises:
    AssertionError if any frames don't match
    ValueError if videos have different lengths
    """
    if len(video1_frames) != len(video2_frames):
        raise ValueError(f"Videos have different lengths: {
                         len(video1_frames)} vs {len(video2_frames)}")

    for i, (frame1, frame2) in enumerate(zip(video1_frames, video2_frames)):
        try:
            assert_frames_equal(frame1, frame2, tolerance)
        except (AssertionError, ValueError) as e:
            raise AssertionError(f"Frame {i} mismatch: {str(e)}")
