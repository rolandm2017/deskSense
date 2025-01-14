import win32gui
import win32process
import psutil

# class ActiveProgramInfo:
#     def __init__(self, process_name, title, pid, timestamp):
#         self.process_name = process_name
#         self.title = title
#         self.pid = pid

class ProgramApiFacade:

    def __init__(self, os):
        self.read_current_program_info = None
        if os.is_windows:
            self.read_current_program_info = self.read_current_program_info_windows
        else:
            self.read_current_program_info = self.read_current_program_info_ubuntu

    def read_current_program_info_windows(self):
        window = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(window)[1]
        process = psutil.Process(pid)
        window_title = win32gui.GetWindowText(window)

        # "window": window, -> not used
        return { "os": "windows", "pid": pid, "process_name": process, "window_title": window_title}    

    def read_current_program_info_ubuntu(self):
        # Get all running processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Get process info
                process_info = proc.info
                
                print(process_info, '37rm')
                # Filter out system processes and get user applications
                if process_info['cmdline'] and process_info['name']:
                    # 'cmdline': ' '.join(process_info['cmdline'])
                    print(' '.join(process_info['cmdline']))
                    processes.append({
                        "os": "ubuntu",
                        'pid': process_info['pid'],
                        'process_name': process_info['name'],
                        'window_title': "TODO"
                        
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return processes