import cv2


def get_frame_timestamps(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    timestamps = []
    frame_count = 0

    while cap.isOpened():
        ret, _ = cap.read()
        if not ret:
            break

        timestamp = frame_count / fps
        timestamps.append(timestamp)
        frame_count += 1

    cap.release()
    return timestamps, frame_count


def get_video_length(video_path):
    """
    Get the total duration of a video file in seconds

    Args:
        video_path (str): Path to the video file

    Returns:
        float: Duration of video in seconds
    """
    cap = cv2.VideoCapture(video_path)

    # Get frame count and fps
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Calculate duration
    duration = frame_count / fps

    cap.release()
    return duration


if __name__ == "__main__":

    # Usage
    video_file = "output/output1.avi"
    timestamps = get_frame_timestamps(video_file)
    for i, ts in enumerate(timestamps):
        print(f"Frame {i}: {ts:.1f} seconds")
