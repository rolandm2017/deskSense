from collections import deque

from activitytracker.object.classes import ChromeSession


class TabCache:
    """
    Class exists because Chrome can't detect the user alt-tabbing back
    into Chrome. So the latest values are cached. When ProgramTracker
    detects Chrome being activated, the latest value matching the
    window title will be used as the tab.

    Entries must be auto-deleted after a few cached tabs, to avoid
    the program fetching outdated tabs.
    """

    def __init__(self) -> None:
        self.cache = deque(maxlen=10)

    def store(self, tab: ChromeSession):
        print("Storing tab: ", tab)
        print(f"'{tab.detail}'", "will be the key")
        self.cache.append({tab.detail: tab})

    def contains(self, target_title):
        """Works with ProgramSession's detail property"""
        return any(
            title == target_title for cache_dict in self.cache for title in cache_dict.keys()
        )

    def get_by_title(self, title):
        print("IN GET BY TITLE")
        print("IN GET BY TITLE")
        print("IN GET BY TITLE")
        for cache_dict in reversed(self.cache):
            print(title, cache_dict)
            if title in cache_dict or cache_dict:
                return cache_dict[title]
        return None  # Return None if not found

    def update_start_time(self, cached_tab: ChromeSession, new_start_time):
        cached_tab.start_time = new_start_time
        return cached_tab
