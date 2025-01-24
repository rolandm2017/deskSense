
import signal
import sys
import cv2


def shutdown(cap, out):
    """Clean up resources and exit gracefully"""
    if cap is not None:
        cap.release()        # Release webcam to make it available for other applications
    if out is not None:
        out.release()           # Close video file to ensure it's properly saved
    cv2.destroyAllWindows()         # Clean up any OpenCV windows to free memory

    # Only exit if we're not in a test environment
    if not hasattr(sys, '_called_from_test'):
        sys.exit(0)                 # Exit program with success status code


# def shutdown(cap, out):
#     cap.release()
#     out.release()
#     cv2.destroyAllWindows()  # Clean up any OpenCV windows to free memory
#     sys.exit(0)              # Exit program with success status code


def setup_interrupt_handler(signal_handler):
    """
    Registers a SIGINT (Ctrl+C) handler for graceful program termination.
    This ensures video files are properly closed and resources released when
    the user interrupts recording.
    """
    signal.signal(signal.SIGINT, signal_handler)
