import unittest
import platform
import psutil

import os

@unittest.skipIf(platform.system() != "Windows", "Windows-only tests")
class TestWindowsPsutilValidation(unittest.TestCase):
    def test_compare_psutil_with_win32(self):
        import win32gui
        import win32api
        import win32process

        """Compare psutil process info with win32 API results."""
        # Get foreground window via win32
        hwnd = win32gui.GetForegroundWindow()
        thread_id, win32_pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Get process info via win32
        win32_process_name = os.path.basename(
            win32process.GetModuleFileNameEx(
                win32api.OpenProcess(0x0400, False, win32_pid), 0
            )
        )
        
        # Get same process via psutil
        psutil_process = psutil.Process(win32_pid)
        psutil_name = psutil_process.name()
        
        # Compare
        self.assertEqual(
            psutil_name.lower(), 
            win32_process_name.lower(),
            f"Process name mismatch: psutil={psutil_name}, win32={win32_process_name}"
        )



@unittest.skipIf(platform.system() != "Linux", "Linux-only tests")
class TestLinuxPsutilValidation(unittest.TestCase):
    def test_compare_psutil_with_proc(self):
        """Compare psutil process info with /proc filesystem results."""
        import subprocess
        # Get pid of current process
        current_pid = os.getpid()
        
        # Get process name via psutil
        psutil_process = psutil.Process(current_pid)
        psutil_name = psutil_process.name()
        
        # Get process name via /proc
        proc_name = subprocess.check_output(
            f"cat /proc/{current_pid}/comm", 
            shell=True
        ).decode().strip()
        
        # Compare
        self.assertEqual(
            psutil_name.lower(), 
            proc_name.lower(),
            f"Process name mismatch: psutil={psutil_name}, proc={proc_name}"
        )