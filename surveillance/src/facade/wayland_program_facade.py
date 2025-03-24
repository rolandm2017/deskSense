import subprocess
import time
import psutil
from typing import Dict, Generator


class WaylandProgramFacadeCore:
    def __init__(self):
        # Check if we're running on Wayland
        self._check_wayland()

    def _check_wayland(self):
        """Verify we're running on Wayland"""
        try:
            session_type = subprocess.check_output(
                "echo $XDG_SESSION_TYPE", 
                shell=True, 
                text=True
            ).strip()
            
            if session_type != "wayland":
                print(f"Warning: Current session is {session_type}, not Wayland")
        except Exception as e:
            print(f"Could not determine session type: {e}")

    def read_current_program_info(self) -> Dict:
        """
        Gets information about the currently active window.
        
        Returns:
            Dict: Information about the active window including OS, PID, process name, and window title.
        """
        return self._read_wayland()

    def _read_wayland(self) -> Dict:
        """
        Reads information about the currently active window on Wayland.
        Note: Wayland has stricter security, so we need to use external tools.
        
        Returns:
            Dict: Window information including OS, PID, process name, and window title.
        """
        # We'll use the 'swaymsg' command for Sway WM or 'gdbus' for GNOME
        window_info = {
            "os": "Linux (Wayland)",
            "pid": None,
            "process_name": "Unknown",
            "window_title": "Unknown"
        }
        
        # Try GNOME method first (most common on Ubuntu)
        try:
            output = subprocess.check_output(
                [
                    "gdbus", "call", "--session", 
                    "--dest", "org.gnome.Shell", 
                    "--object-path", "/org/gnome/Shell", 
                    "--method", "org.gnome.Shell.Eval", 
                    "global.display.focus_window.get_title()"
                ], 
                text=True
            )
            
            # Parse the output "(true, 'Window Title')"
            if output.startswith("(true, "):
                title = output.split("'")[1]
                window_info["window_title"] = title
                
                # Try to get PID from window title (this is a fallback and not reliable)
                # Unfortunately, Wayland doesn't expose PIDs easily for security reasons
                active_pids = self._get_active_application_pids()
                if active_pids:
                    window_info["pid"] = active_pids[0]
                    process = psutil.Process(active_pids[0])
                    window_info["process_name"] = process.name()
                
                return window_info
                
        except (subprocess.SubprocessError, IndexError):
            pass
            
        # Try Sway method if GNOME failed
        try:
            output = subprocess.check_output(["swaymsg", "-t", "get_tree"], text=True)
            if "focused" in output and "name" in output:
                import json
                tree = json.loads(output)
                
                # Recursively find the focused window
                def find_focused(node):
                    if node.get("focused") == True:
                        return node
                    
                    for child in node.get("nodes", []):
                        result = find_focused(child)
                        if result:
                            return result
                            
                    for child in node.get("floating_nodes", []):
                        result = find_focused(child)
                        if result:
                            return result
                            
                    return None
                
                focused = find_focused(tree)
                if focused:
                    window_info["window_title"] = focused.get("name", "Unknown")
                    if "pid" in focused:
                        pid = focused["pid"]
                        window_info["pid"] = pid
                        try:
                            process = psutil.Process(pid)
                            window_info["process_name"] = process.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
                    return window_info
        except (subprocess.SubprocessError, json.JSONDecodeError):
            pass
            
        return window_info
        
    def _get_active_application_pids(self):
        """Get a list of likely active application PIDs"""
        active_pids = []
        
        desktop_env = self._get_desktop_environment()
        if desktop_env == "gnome":
            try:
                # Get GNOME Shell PID first
                gnome_shell_pid = subprocess.check_output(
                    ["pgrep", "-f", "gnome-shell"], text=True
                ).strip().split("\n")[0]
                
                if gnome_shell_pid:
                    # Get children of GNOME Shell
                    shell_process = psutil.Process(int(gnome_shell_pid))
                    for child in shell_process.children(recursive=True):
                        if child.name() not in ["gnome-shell-calendar-server", "gnome-shell-wayland"]:
                            active_pids.append(child.pid)
            except (subprocess.SubprocessError, psutil.NoSuchProcess, psutil.AccessDenied, IndexError):
                pass
                
        # Fallback: Get GUI applications with high CPU or recent start time
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent']):
            try:
                # Skip system processes
                if proc.username() != 'root' and proc.terminal() is None:
                    # Check if it seems like a GUI app
                    if any(x in proc.name().lower() for x in ['firefox', 'chrome', 'terminal', 'gedit', 'libreoffice']):
                        active_pids.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        return active_pids

    def _get_desktop_environment(self):
        """Determine the desktop environment"""
        try:
            output = subprocess.check_output("echo $XDG_CURRENT_DESKTOP", shell=True, text=True).strip().lower()
            if "gnome" in output:
                return "gnome"
            elif "kde" in output:
                return "kde"
            else:
                return output
        except subprocess.SubprocessError:
            return "unknown"

    def listen_for_window_changes(self) -> Generator[Dict, None, None]:
        """
        Listens for window focus changes using polling and yields window information when changes occur.
        This is the fallback method for Wayland which doesn't expose a clean event API.
        
        Yields:
            Dict: Information about the new active window after each focus change.
        """
        previous_window_title = self.read_current_program_info()["window_title"]
        
        while True:
            time.sleep(0.5)  # Check every half second
            
            current_info = self.read_current_program_info()
            current_window_title = current_info["window_title"]
            
            # If the window has changed
            if current_window_title != previous_window_title:
                previous_window_title = current_window_title
                print(f"Window changed: {current_info['window_title']} ({current_info['process_name']})")
                yield current_info

    def setup_window_hook(self) -> Generator[Dict, None, None]:
        """
        For Wayland, we need to use a DBus monitor or polling since there's no direct hook API.
        This attempts to use DBus monitoring when possible, falling back to polling.
        
        Yields:
            Dict: Information about the new active window after each focus change.
        """
        desktop_env = self._get_desktop_environment()
        
        # For GNOME, we can monitor DBus signals
        if desktop_env == "gnome":
            try:
                # Set up DBus monitoring process
                process = subprocess.Popen(
                    [
                        "dbus-monitor", 
                        "--session",
                        "type='signal',interface='org.gnome.Shell',member='WindowsChanged'"
                    ],
                    stdout=subprocess.PIPE,
                    text=True
                )
                
                while True:
                    line = process.stdout.readline()
                    if "WindowsChanged" in line:
                        # Wait a tiny bit for the change to fully propagate
                        time.sleep(0.1)
                        window_info = self._read_wayland()
                        print(f"Window changed: {window_info['window_title']} ({window_info['process_name']})")
                        yield window_info
                        
            except (subprocess.SubprocessError, KeyboardInterrupt):
                # Fall back to polling method if DBus monitoring fails
                yield from self.listen_for_window_changes()
        else:
            # For other Wayland compositors, use polling
            yield from self.listen_for_window_changes()


# Example usage
if __name__ == "__main__":
    monitor = WaylandProgramFacadeCore()
    
    print("Starting window focus monitoring on Wayland...")
    print("Initial window:", monitor.read_current_program_info())
    
    try:
        for window_info in monitor.setup_window_hook():
            print(f"Active window: {window_info['window_title']} ({window_info['process_name']})")
            
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")