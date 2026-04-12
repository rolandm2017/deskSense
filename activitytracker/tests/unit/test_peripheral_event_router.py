from unittest.mock import Mock

from activitytracker.peripheral_event_router import PeripheralEventRouter


def test_keyboard_events_schedule_timeline_and_keyboard_writes():
    event = object()
    timeline_dao = Mock()
    keyboard_dao = Mock()
    mouse_dao = Mock()
    task_registry = Mock()

    timeline_write = object()
    keyboard_write = object()
    timeline_dao.create_from_keyboard_aggregate.return_value = timeline_write
    keyboard_dao.create.return_value = keyboard_write

    router = PeripheralEventRouter(
        timeline_dao=timeline_dao,
        keyboard_dao=keyboard_dao,
        mouse_dao=mouse_dao,
        task_registry=task_registry,
    )

    router.handle_keyboard_ready_for_db(event)

    timeline_dao.create_from_keyboard_aggregate.assert_called_once_with(event)
    keyboard_dao.create.assert_called_once_with(event)
    mouse_dao.create_from_window.assert_not_called()
    task_registry.create_task.assert_any_call(timeline_write, name="timeline-keyboard")
    task_registry.create_task.assert_any_call(keyboard_write, name="keyboard-dao")


def test_mouse_events_schedule_timeline_and_mouse_writes():
    event = object()
    timeline_dao = Mock()
    keyboard_dao = Mock()
    mouse_dao = Mock()
    task_registry = Mock()

    timeline_write = object()
    mouse_write = object()
    timeline_dao.create_from_mouse_move_window.return_value = timeline_write
    mouse_dao.create_from_window.return_value = mouse_write

    router = PeripheralEventRouter(
        timeline_dao=timeline_dao,
        keyboard_dao=keyboard_dao,
        mouse_dao=mouse_dao,
        task_registry=task_registry,
    )

    router.handle_mouse_ready_for_db(event)

    timeline_dao.create_from_mouse_move_window.assert_called_once_with(event)
    mouse_dao.create_from_window.assert_called_once_with(event)
    keyboard_dao.create.assert_not_called()
    task_registry.create_task.assert_any_call(timeline_write, name="timeline-mouse")
    task_registry.create_task.assert_any_call(mouse_write, name="mouse-dao")


def test_router_uses_task_registry():
    event = object()
    timeline_dao = Mock()
    keyboard_dao = Mock()
    mouse_dao = Mock()
    task_registry = Mock()

    router = PeripheralEventRouter(
        timeline_dao=timeline_dao,
        keyboard_dao=keyboard_dao,
        mouse_dao=mouse_dao,
        task_registry=task_registry,
    )

    router.handle_keyboard_ready_for_db(event)
    router.handle_mouse_ready_for_db(event)

    assert task_registry.create_task.call_count == 4
