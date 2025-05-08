def make_os_output(exe_path, process_name, pid, window_title):
    return {
        "os": "Windows",
        "exe_path": exe_path,
        "process_name": process_name,
        "pid": pid,
        "window_title": window_title,
    }


program_facade_data = [
    make_os_output("C:/TestFiles/ableton/Ableton.exe", "Ableton.exe", 294, "Ableton Live"),
    make_os_output(
        "C:/ProgramFiles/adobe/Photoshop.exe", "Photoshop.exe", 5992, "Adobe Photoshop"
    ),
    make_os_output(
        "C:/ProgramFiles/slack/Slack.exe",
        "Slack.exe",
        883,
        "Slack - Outfusion Sprint Planning",
    ),
]
