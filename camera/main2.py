from src.recording import record_n_sec_video
from src.startup_shutdown import setup_interrupt_handler

# Global flag for interrupt handling
interrupt_called = False


def signal_handler(sig, frame):
    global interrupt_called
    print("\nCtrl+C detected. Executing graceful stop...")
    interrupt_called = True


def main():
    # Set up the interrupt handler
    setup_interrupt_handler(signal_handler)

    # Pass a lambda that checks the global flag
    video_path = record_n_sec_video(
        10,
        "output.avi",
        should_continue=lambda: not interrupt_called
    )
    print(f"Recorded video saved to: {video_path}")


if __name__ == "__main__":
    main()
