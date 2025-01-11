import win32gui
import win32process
import psutil
import time
from datetime import datetime
import json
from pathlib import Path
import csv

from src.productivity_tracker import ProductivityTracker



def main():
    tracker = ProductivityTracker()
    print("Starting productivity tracking...")
    print("Press Ctrl+C to stop and generate report.")
    
    try:
        while True:
            tracker.track_window()
            time.sleep(1)  # Check every second
    except KeyboardInterrupt:
         # Log final session before exiting
        tracker.log_session()
        
        # Generate and display productivity report
        report = tracker.generate_report()
        print("\nToday's Productivity Report:")
        print(f"Date: {report['date']}")
        print(f"Productive Time: {report['productive_time']} hours")
        print(f"Unproductive Time: {report['unproductive_time']} hours")
        print(f"Productivity Rate: {report['productive_percentage']}%")

        # Generate and display mouse movement report
        mouse_report = tracker.mouse_tracker.generate_movement_report()
        if isinstance(mouse_report, dict):  # Check if we got actual data
            print("\nMouse Movement Report:")
            print(f"Total movements: {mouse_report['total_movements']}")
            print(f"Average movement duration: {mouse_report['avg_movement_duration']} seconds")
            print(f"Total movement time: {mouse_report['total_movement_time']} seconds")

        # Generate and display keyboard report
        keyboard_report = tracker.keyboard_tracker.generate_keyboard_report()
        if isinstance(keyboard_report, dict):
            print("\nKeyboard Input Report:")
            print(f"Total keystrokes: {keyboard_report['total_inputs']}")
        else:
            print("Failed to get keyboard report")

        # Clean up
        tracker.cleanup()  # This will call mouse_tracker.stop()

if __name__ == "__main__":
    main()