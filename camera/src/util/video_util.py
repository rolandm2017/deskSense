import cv2
import numpy as np

from ..recording.recording import init_webcam, initialize_new_vid


def extract_frame(video_path, frame_number):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not cap.isOpened():
        print("[err 13] Could not open video file")
        return None

    # Get total number of frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Check if frame_number is valid
    if frame_number >= total_frames:
        print(f"[err 21] Video has only {total_frames} frames")
        cap.release()
        return None

    # Set frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    # Read the frame
    ret, frame = cap.read()

    # Release the video capture object
    cap.release()

    if ret:
        return frame
    else:
        print("Error: Could not read frame")
        return None


def extract_frames(video_path):
    """
    Extract all frames from a video file.

    Args:
        video_path (str): Path to the video file

    Returns:
        list: List of numpy arrays, where each array is a frame
              Returns empty list if video cannot be opened
    """
    frames = []

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not cap.isOpened():
        print(f"[err 59]: Could not open video file {video_path}")
        return frames

    while True:
        # Read a frame
        ret, frame = cap.read()

        # If frame is read correctly ret is True
        if not ret:
            break

        frames.append(frame)

    # Release the video capture object
    cap.release()

    return frames

# Example usage:
# video_frames = extract_frames('path/to/your/video.mp4')
# print(f"Extracted {len(video_frames)} frames")
#
# # To access individual frames:
# first_frame = video_frames[0]  # First frame
# last_frame = video_frames[-1]  # Last frame

# # Example usage
# if __name__ == "__main__":
#     video_path = "path/to/your/video.mp4"
#     n = 100  # Extract the 100th frame

#     frame = extract_frame(video_path, n)

#     if frame is not None:
#         # Save the frame as an image
#         cv2.imwrite(f"frame_{n}.jpg", frame)

#         # Or display it (press any key to close)
#         cv2.imshow(f"Frame {n}", frame)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()


def put_still_frames_into_discard(src_frames, motion_frames, discard_name, out_dir):
    discard_vid = initialize_new_vid(discard_name, out_dir)

    for frame in motion_frames:
        print(frame, '107ru')
        if not frame[1]:
            to_write = src_frames[frame[0]]
            discard_vid.write(to_write)

    # Writing is done, should be all stillness
    discard_vid.release()
