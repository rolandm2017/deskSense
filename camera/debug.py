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
    return timestamps


# Usage
video_file = "output/output.avi"
timestamps = get_frame_timestamps(video_file)
for i, ts in enumerate(timestamps):
    print(f"Frame {i}: {ts:.1f} seconds")
