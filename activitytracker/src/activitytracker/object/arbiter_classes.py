class InternalState:
    def __init__(self, active_application, is_chrome, session):
        self.active_application = active_application
        self.is_chrome = is_chrome
        self.session = session

    def __str__(self):
        return f"InternalState(application='{self.active_application}', is_chrome={self.is_chrome}, session={self.session})"
