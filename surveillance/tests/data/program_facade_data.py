
class PsutilMock:
    def __init__(self, exe, name):
        self.exe = exe
        self.name = name

    def name(self):
        return self.name
    
    def exe(self):
        return self.exe

def make_os_output(exe_path, process_name, pid):
    return {
        "exe_path": exe_path,
        "process_name": process_name,
        "pid": pid
    }


program_facade_data = [
    {

    }
]