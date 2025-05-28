from activitytracker.object.classes import ChromeSession


class TabCache:
    def __init__(self) -> None:
        self.cache = []

    def store(self, tab: ChromeSession):
        self.cache.append({tab.detail: tab})

    def contains(self, target_title):
        return any(title == target_title for title, entry in self.cache)

    def get_by_title(self, title):
        return self.cache[title]
