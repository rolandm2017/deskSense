# activitytracker/src/facade/keyboard_facade_singleton.py
from .keyboard_facade import KeyboardFacadeCore
from .mouse_facade import MouseFacadeCore

# Singleton instance
_keyboard_facade_instance = None
_mouse_facade_instance = None


def get_keyboard_facade_instance():
    global _keyboard_facade_instance
    if _keyboard_facade_instance is None:
        _keyboard_facade_instance = KeyboardFacadeCore()
    return _keyboard_facade_instance


def get_mouse_facade_instance():
    global _mouse_facade_instance
    if _mouse_facade_instance is None:
        _mouse_facade_instance = MouseFacadeCore()
    return _mouse_facade_instance
