from Xlib import X, display
from datetime import datetime
import time

#
# Example program for getting window name etc in ubuntu
#

def get_active_window():
    try:
        # Connect to the X server
        d = display.Display()
        root = d.screen().root

        # Get the active window ID
        active_window_id = root.get_full_property(
            d.intern_atom('_NET_ACTIVE_WINDOW'), X.AnyPropertyType
        ).value[0]

        # Get the window object
        window_obj = d.create_resource_object('window', active_window_id)
        window_name = window_obj.get_full_property(
            d.intern_atom('_NET_WM_NAME'), 0
        )

        if window_name:
            return window_name.value
        else:
            return "Unnamed window"
    except Exception as e:
        return f"Error: {str(e)}"

SECONDS_TO_RUN = 23

def main():
    print("Starting window monitoring...")
    start_time = time.time()

    while time.time() - start_time < SECONDS_TO_RUN:
        active = get_active_window()
        print(f"{datetime.now()}: Active window - {active}")
        time.sleep(1)

if __name__ == "__main__":
    main()
