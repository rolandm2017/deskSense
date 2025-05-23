import json
import os
import urllib.parse

from dotenv import load_dotenv

load_dotenv

import requests
from requests.auth import HTTPBasicAuth

from activitytracker.object.video_classes import VlcInfo

# VLC config
VLC_HOST = "http://localhost:8080"
VLC_PASSWORD = os.getenv("VLC_PASS")  # set this in VLC's Lua config
if VLC_PASSWORD is None:
    raise ValueError("Failed to load VLC password")

AUTH = HTTPBasicAuth("", VLC_PASSWORD)

DEBUG = False


class VlcMediaPlayerTracker:
    def __init__(self) -> None:
        pass

    def start_polling(self):
        self.polling_active = True
        while self.polling_active:
            yield self.ask_is_vlc_playing()

    def listen_for_player_changes(self):
        while True:
            yield self.ask_is_vlc_playing()

    def ask_is_vlc_playing(self):
        return get_vlc_status()

    def stop_polling(self):
        self.polling_active = False


def get_vlc_status() -> VlcInfo | None:
    url = f"{VLC_HOST}/requests/status.json"
    try:
        response = requests.get(url, auth=AUTH)
        response.raise_for_status()
        data = response.json()

        if DEBUG:
            print(json.dumps(data.get("information", {}), indent=2))

        state = data.get("state")  # "playing", "paused", "stopped"
        position = data.get("time")  # in seconds

        # Try to extract file info
        info = data.get("information", {}).get("category", {}).get("meta", {})
        print("INFO:", info)
        full_url = info.get("url")  # e.g., file:///C:/Videos/movie.mp4
        filename = info.get("filename")

        file_path = None
        print("full url:", full_url)
        if full_url and full_url.startswith("file://"):
            file_path = urllib.parse.unquote(full_url[7:])

        return VlcInfo(filename, file_path, state, position)
        # return {
        #     "state": state,
        #     "position_seconds": position,
        #     "filename": filename,
        #     "file_path": file_path,
        # }

    except requests.RequestException as e:
        print(f"Error connecting to VLC: {e}")
        return None
