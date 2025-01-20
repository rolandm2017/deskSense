import win32gui
import win32process
import psutil
import time
from datetime import datetime
import json
from pathlib import Path
import csv

from surveillance.src.surveillance_manager import SurveillanceManager


def main():
    surveillance_manager = SurveillanceManager()
    # print("Starting productivity tracking...")
    print("Press Ctrl+C to stop and generate report.")

    try:
        while True:
            # surveillance_manager.program_tracker.track_window()
            surveillance_manager.program_tracker.attach_listener()
            time.sleep(1)  # Check every second
    except KeyboardInterrupt:
        # Log final session before exiting
        surveillance_manager.program_tracker.log_session()

        # Generate and display productivity report
        report = surveillance_manager.program_tracker.generate_report()  # deprecated
        print("\nToday's Productivity Report:")
        print(f"Date: {report['date']}")
        print(f"Productive Time: {report['productive_time']} hours")
        print(f"Unproductive Time: {report['unproductive_time']} hours")
        print(f"Productivity Rate: {report['productive_percentage']}%")

        # Generate and display mouse movement report
        mouse_report = surveillance_manager.mouse_tracker.generate_movement_report()
        if isinstance(mouse_report, dict):  # Check if we got actual data
            print("\nMouse Movement Report:")
            print(f"Total movements: {mouse_report['total_movements']}")
            print(f"Average movement duration: {
                  mouse_report['avg_movement_duration']} seconds")
            print(f"Total movement time: {
                  mouse_report['total_movement_time']} seconds")

        # Generate and display keyboard report
        keyboard_report = surveillance_manager.keyboard_tracker.generate_keyboard_report()
        if isinstance(keyboard_report, dict):
            print("\nKeyboard Input Report:")
            print(f"Total keystrokes: {keyboard_report['total_inputs']}")
        else:
            print("Failed to get keyboard report")

        # Clean up
        surveillance_manager.cleanup()  # This will call mouse_tracker.stop()


if __name__ == "__main__":
    main()
