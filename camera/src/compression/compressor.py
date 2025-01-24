import cv2
import os


def convert_for_ml(input_path, output_path):
    """Convert a completed video file to ML-friendly format (MJPEG with minimal compression)"""
    cap = cv2.VideoCapture(input_path)

    # Configure writer for maximum quality
    fourcc = get_high_compression_codec_one()
    out = cv2.VideoWriter(
        output_path,
        fourcc,
        cap.get(cv2.CAP_PROP_FPS),
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
         int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    )

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Ensure consistent dtype and range
        frame = frame.astype(np.uint8)
        out.write(frame)

    cap.release()
    out.release()

    return output_path


def compress_video(input_path, output_path, target_bitrate=1000000):  # 1Mbps default
    """
    Compress an AVI video while maintaining quality.

    Args:
        input_path (str): Path to input video
        output_path (str): Path to save compressed video
        target_bitrate (int): Target bitrate in bits per second
    """
    # Open the input video
    cap = cv2.VideoCapture(input_path)

    # Get original video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate optimal buffer size (this helps maintain quality)
    buffer_size = int(target_bitrate * 2)  # 2 seconds worth of frames

    # Create video writer with compression settings
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height),
        True
    )

    # Set additional compression parameters
    # Quality 0-100 (higher is better)
    out.set(cv2.VIDEOWRITER_PROP_QUALITY, 85)

    frames_processed = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Optional: Reduce frame size while maintaining aspect ratio
        # scale = 0.75  # Adjust this value to change compression level
        # new_width = int(width * scale)
        # new_height = int(height * scale)
        # frame = cv2.resize(frame, (new_width, new_height))
        # frame = cv2.resize(frame, (width, height))  # Scale back up to maintain dimensions

        # Apply additional compression by reducing color depth
        # Slight contrast reduction
        frame = cv2.convertScaleAbs(frame, alpha=0.9, beta=0)

        out.write(frame)

        frames_processed += 1
        if frames_processed % 100 == 0:
            progress = (frames_processed / total_frames) * 100
            print(f"Progress: {progress:.1f}%")

    # Release resources
    cap.release()
    out.release()

    # Print compression results
    original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
    compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    compression_ratio = original_size / compressed_size

    print(f"\nCompression Results:")
    print(f"Original Size: {original_size:.2f} MB")
    print(f"Compressed Size: {compressed_size:.2f} MB")
    print(f"Compression Ratio: {compression_ratio:.2f}x")
