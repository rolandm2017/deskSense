import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_TIME_ZONE = os.getenv("LOCAL_TIME_ZONE")

power_on_off_debug_file = "march10_on_off_times.txt"

if LOCAL_TIME_ZONE is None or LOCAL_TIME_ZONE == "":
    raise ValueError(
        "LOCAL_TIME_ZONE environment variable is not set or is empty")


local_time_zone = LOCAL_TIME_ZONE

MAX_QUEUE_LENGTH = 40

max_content_len = 120

# Define productive applications
productive_apps = ['Chrome', "Google Chrome", 'File Explorer',  # Chrome determined by window title
                   'Postman', 'Terminal', 'Visual Studio Code']

# TODO: allow user to mark certain servers "productive" i.e. Slack analogues
# mostly a temp holder for later exploration by channel
unproductive_apps = ["Discord"]

productive_categories = {
    'File Explorer': True,
    'Google Chrome': None,  # Will be determined by window title
    'Mozilla Firefox': None,  # Will be determined by window title
    'Alt-tab window': None,  # Determined by destination of the alt-tab.
    'Postman': True,
    'Terminal': True,
    'Visual Studio Code': True
}

# Productive website patterns (for Chrome)
productive_sites = [
    'github.com',
    'stackoverflow.com',
    'docs.',
    'jira.',
    'confluence.',
    'claude.ai',
    'chatgpt.com',
    'www.google.com',
    'localhost',
    'extensions'
]


social_media = ['www.facebook.com', 'www.tiktok.com', 'x.com', ]

misc_sites = ['newtab', 'chatgpt.com']

# Keyboard tracker stuff (not used)
average_char_per_word = 5
wpm = 90
char_per_min = 540  # 5 char per word * 90 word per min -> 540 char per min
char_per_sec = 9  # 540 char / 60 sec -> 9 char per sec
required_delay_per_char = 0.08  # 1 sec / 9 char -> 0.111 sec per char

DELAY_TO_AVOID_CPU_HOGGING = required_delay_per_char
