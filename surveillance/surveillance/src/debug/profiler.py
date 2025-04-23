# profiler.py
import time
import inspect

_last_time = None


def timestamp(label=None):
    global _last_time
    now = time.time()
    delta = now - _last_time if _last_time is not None else None
    _last_time = now

    caller = inspect.stack()[1].function
    msg = f"[profiler] {label or caller} at {now:.3f}"
    if delta is not None:
        msg += f" (+{delta:.3f}s)"
    print(msg)
