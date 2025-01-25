import cv2

import numpy as np

path = "test_videos/me_using_pcV-Lossless.avi"


def analyze_video_characteristics(video_path: str):
    cap = cv2.VideoCapture(video_path)
    frame_diffs = []
    prev_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if prev_frame is not None:
            # Convert to grayscale for simpler analysis
            gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(gray1, gray2)

            # Get statistics
            avg_diff = np.mean(diff)
            max_diff = np.max(diff)
            frame_diffs.append((avg_diff, max_diff))

        prev_frame = frame.copy()

    cap.release()
    return frame_diffs


def summarize_diffs(frame_diffs):
    avg_diffs, max_diffs = zip(*frame_diffs)
    print(f"Average difference: {np.mean(avg_diffs):.2f}")
    print(f"Max difference ever: {np.max(max_diffs)}")
    print(f"95th percentile diff: {np.percentile(max_diffs, 95):.2f}")


diffs = analyze_video_characteristics(path)
summarize_diffs(diffs)
