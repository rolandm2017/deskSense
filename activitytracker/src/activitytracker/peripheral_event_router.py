class PeripheralEventRouter:
    def __init__(self, timeline_dao, keyboard_dao, mouse_dao, task_registry):
        self.timeline_dao = timeline_dao
        self.keyboard_dao = keyboard_dao
        self.mouse_dao = mouse_dao
        self.task_registry = task_registry

    def handle_keyboard_ready_for_db(self, event):
        self.task_registry.create_task(
            self.timeline_dao.create_from_keyboard_aggregate(event),
            name="timeline-keyboard",
        )
        self.task_registry.create_task(self.keyboard_dao.create(event), name="keyboard-dao")

    def handle_mouse_ready_for_db(self, event):
        self.task_registry.create_task(
            self.timeline_dao.create_from_mouse_move_window(event),
            name="timeline-mouse",
        )
        self.task_registry.create_task(
            self.mouse_dao.create_from_window(event), name="mouse-dao"
        )
