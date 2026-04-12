# God Object Refactor Plan - 2026-04-12

## Problem Statement

`activitytracker/src/activitytracker/arbiter/activity_arbiter.py` is close to a god object because it coordinates session transitions, sleep recovery, pulse lifecycle, UI notifications, recorder notifications, logging, and shutdown behavior in one class. Some centralization is legitimate here because the arbiter owns an important product invariant: at most one Activity should be active at a time. The problem is not that a coordinator exists; the problem is that the coordinator knows too much about how each subsystem works. That makes small changes risky because a timing-policy change can accidentally touch threading, persistence notification, or sleep-gap behavior.

`activitytracker/src/activitytracker/surveillance_manager.py` has a related but different problem: it acts as a composition root, runtime supervisor, event router, DAO builder, thread owner, message receiver starter, shutdown handler, and task cancellation manager. This makes it hard to test because constructing the manager pulls in much of the runtime object graph even when a test only wants to exercise one event path. It also makes changes complicated because lifecycle concerns, persistence concerns, and event adaptation are interleaved. The current shape is an antipattern not because a data pipeline needs no central owner, but because the central owner is doing too many concrete jobs directly.

## Goal

Reduce the amount of concrete work performed by `ActivityArbiter` and `SurveillanceManager` while preserving their role as coordinators.

The goal is not a large architecture rewrite. The goal is a sequence of small extractions that make behavior easier to test, reduce class size, and make future timing/pipeline changes less dangerous.

A rough success target is a 40% reduction in the amount of implementation detail inside the two classes, not necessarily a 40% line-count reduction. If tests need to be adjusted during the process, that is acceptable, but each stage should preserve the public behavior unless the stage explicitly documents an intentional behavior change.

## Non-Goals

- Do not remove `ActivityArbiter` as the public session coordinator.
- Do not remove `SurveillanceManager` as the high-level runtime coordinator unless a later design explicitly replaces it.
- Do not rewrite the timing model, summary recording model, or sleep recovery model as part of the first extraction.
- Do not combine multiple major extractions in one change unless the tests force it.
- Do not use this refactor to redesign dashboard endpoints, Pursuits, categories, or attribution semantics.

## Design Principle

A coordinator may know workflow order, but it should not personally implement every step.

A desirable `ActivityArbiter.transition_state(...)` should eventually read like orchestration:

```python
def transition_state(new_session):
    sleep_decision = sleep_gap_handler.inspect_before_transition(new_session)
    if sleep_decision.should_flush:
        active_session_state.flush_at(sleep_decision.end_time)
        pulse_controller.stop()
        notifier.notify_completed_session(sleep_decision.concluded_session)

    notifier.notify_display_update(new_session)
    outcome = active_session_state.advance_to(new_session)
    pulse_controller.switch_to(new_session)
    notifier.notify_new_session(new_session)
    notifier.notify_completed_session(outcome.concluded_session)
```

This sketch is not mandatory implementation. It shows the intended direction: the arbiter keeps the workflow, while extracted components own the mechanics.

## Stage 1 - Extract `PulseController`

### Purpose

Move keep-alive pulse lifecycle knowledge out of `ActivityArbiter`.

### Current Responsibility

`ActivityArbiter` currently knows about `ThreadedEngineContainer`, `KeepAliveEngine`, first-engine initialization, engine replacement, starting, stopping, and recorder injection. This is too much detail for a session arbiter. The arbiter should only say that a new session has become active, not know how the keep-alive thread is wired.

### Proposed Component

Create a component near the arbiter package, for example:

```text
activitytracker/src/activitytracker/arbiter/pulse_controller.py
```

Possible interface:

```python
class PulseController:
    def __init__(self, threaded_container, engine_class, recorder): ...
    def start_first(self, session): ...
    def replace_with(self, session): ...
    def stop(self): ...
```

If recorder injection is awkward because the recorder is added after arbiter construction, either allow `set_recorder(...)` or accept the recorder as an argument to `start_first(...)` / `replace_with(...)`. Prefer constructor injection if it does not create churn.

### Arbiter After This Stage

`ActivityArbiter` should no longer directly call:

- `self.current_pulse.add_first_engine(...)`
- `self.current_pulse.replace_engine(...)`
- `self.current_pulse.start()`
- `self.current_pulse.stop()`
- `self.engine_class(...)`

It should call the controller instead:

```python
self.pulse_controller.start_first(new_session)
self.pulse_controller.replace_with(new_session)
self.pulse_controller.stop()
```

### Tests

Add or adjust focused tests for:

- first session starts a first pulse engine
- replacement session concludes/replaces the prior engine
- flush/shutdown stops the pulse
- missing recorder behavior, if recorder injection remains nullable

Run relevant arbiter tests with `win-pytest`.

## Stage 2 - Extract `ActivityNotifier`

### Purpose

Move UI and recorder listener mechanics out of `ActivityArbiter`.

### Current Responsibility

`ActivityArbiter` currently registers listeners, checks listener shape, snapshots new sessions for tests, notifies UI display updates, notifies new sessions, and notifies completed sessions. These are observer mechanics, not arbitration policy.

### Proposed Component

Create:

```text
activitytracker/src/activitytracker/arbiter/activity_notifier.py
```

Possible interface:

```python
class ActivityNotifier:
    def add_ui_listener(self, listener): ...
    def add_recorder_listener(self, listener): ...
    def notify_display_update(self, session): ...
    def notify_new_session(self, session): ...
    def notify_completed_session(self, session): ...
    @property
    def recorder(self): ...
```

If `PulseController` needs the recorder, the notifier can expose it, or the arbiter can pass the same recorder to both notifier and pulse controller. Prefer not to make `PulseController` depend directly on `ActivityNotifier` unless that reduces complexity clearly.

### Arbiter After This Stage

`ActivityArbiter` should still expose compatibility methods if external code calls them:

```python
def add_ui_listener(self, listener):
    self.notifier.add_ui_listener(listener)

def add_recorder_listener(self, listener):
    self.notifier.add_recorder_listener(listener)
```

But the storage and notification behavior should live in `ActivityNotifier`.

### Tests

Add focused notifier tests for:

- UI listener called on display update
- recorder listener must support expected methods
- new session notification snapshots/copies as expected
- completed session notification passes through `None` or completed sessions according to existing behavior

## Stage 3 - Extract `SleepGapHandler`

### Purpose

Move sleep/wake detection and suspicious status-write logic out of `ActivityArbiter.transition_state(...)`.

### Current Responsibility

The arbiter currently asks the sleep detector whether awakening from sleep occurred, logs the result, flushes current state at a pre-sleep time, and also contains suspicious latest-status-write logic. This interleaves sleep recovery with ordinary session replacement.

### Proposed Component

Create:

```text
activitytracker/src/activitytracker/arbiter/sleep_gap_handler.py
```

Possible data object:

```python
@dataclass
class SleepGapDecision:
    should_flush: bool
    end_time: UserLocalTime | None
```

Possible interface:

```python
class SleepGapHandler:
    def inspect_before_transition(self, incoming_session) -> SleepGapDecision: ...
```

The handler should own calls to:

- `detect_awakening_from_sleep()`
- `get_latest_write_time()`
- warning logs related to sleep/status gaps

The arbiter can keep the actual `flush_and_reset(...)` operation initially, because that operation touches state and pulse lifecycle. A later stage can return a richer decision if needed.

### Tests

Add focused tests for:

- no sleep gap produces no flush decision
- detected sleep gap returns the correct flush time
- suspicious latest status write is handled without referencing undefined names

Note: the current code appears to reference `incoming_session_start` inside `transition_state(...)` without defining it. This should be tested and corrected during or before this stage.

## Stage 4 - Clarify `StateMachine` / `ActiveSessionState`

### Purpose

Clarify the actual responsibility of `StateMachine` after the previous extractions.

### Current Responsibility

`state_machine.py` currently looks less like a full finite state machine and more like an active-session container that can conclude a current session when a new session arrives. It builds completed sessions and calculates duration. The TODO comments already suggest this class may have drifted from its original purpose.

### Proposed Direction

Do not do this stage first. After pulse, notifier, and sleep logic are extracted, decide whether to rename or simplify `StateMachine`.

Possible target name:

```python
class ActiveSessionState:
    def advance_to(self, next_session) -> TransitionOutcome: ...
    def conclude_at(self, end_time): ...
    def conclude_now(self): ...
    def has_current_session(self) -> bool: ...
```

This may be a rename-only refactor at first. Avoid changing the timing semantics unless a failing test proves the existing behavior is wrong.

## Stage 5 - Extract `TaskRegistry` From `SurveillanceManager`

### Purpose

Make async task ownership explicit and cleanup safer.

### Current Responsibility

`SurveillanceManager.cancel_pending_tasks()` currently scans `asyncio.all_tasks()` and guesses which tasks belong to the manager using task names and frame strings. That is brittle. The manager should cancel only the tasks it created or explicitly owns.

### Proposed Component

Create a small registry, likely under `activitytracker/src/activitytracker/util/` or near the surveillance code:

```python
class TaskRegistry:
    def __init__(self, loop): ...
    def create_task(self, coro, *, name: str): ...
    async def cancel_all(self, timeout: float = 3.0) -> int: ...
```

`SurveillanceManager` and extracted event routers should use `TaskRegistry.create_task(...)` instead of calling `self.loop.create_task(...)` directly.

### Tests

Add focused tests for:

- task creation is tracked
- `cancel_all()` cancels pending tasks
- completed tasks do not break cleanup
- timeout behavior is deterministic enough for unit testing

## Stage 6 - Extract `PeripheralEventRouter`

### Purpose

Move keyboard/mouse persistence routing out of `SurveillanceManager`.

### Current Responsibility

`SurveillanceManager` currently handles keyboard and mouse aggregate events by scheduling writes to timeline, keyboard, and mouse DAOs. That is event routing and persistence adaptation, not runtime supervision.

### Proposed Component

Create:

```text
activitytracker/src/activitytracker/peripheral_event_router.py
```

Possible interface:

```python
class PeripheralEventRouter:
    def __init__(self, timeline_dao, keyboard_dao, mouse_dao, task_registry): ...
    def handle_keyboard_ready_for_db(self, event): ...
    def handle_mouse_ready_for_db(self, event): ...
```

Then `SurveillanceManager` passes router methods into the tracker cores.

### Tests

Add focused tests for:

- keyboard events schedule timeline and keyboard DAO writes
- mouse events schedule timeline and mouse DAO writes
- router uses `TaskRegistry`, not raw `asyncio.all_tasks()` scanning

## Stage 7 - Extract `TrackerRuntime`

### Purpose

Move tracker thread lifecycle out of `SurveillanceManager`.

### Current Responsibility

`SurveillanceManager` constructs tracker cores, wraps them in `ThreadedTracker`, starts all tracker threads, and stops all tracker threads during cleanup. This makes the manager large and makes tracker lifecycle hard to test independently.

### Proposed Component

Create:

```text
activitytracker/src/activitytracker/tracker_runtime.py
```

Possible interface:

```python
class TrackerRuntime:
    def __init__(self, keyboard_tracker, mouse_tracker, program_tracker): ...
    def start(self): ...
    def stop(self): ...
```

A later version may include construction, but the first extraction can simply receive already-built tracker cores or threaded trackers. Keep it mechanical.

### Tests

Add focused tests for:

- `start()` starts keyboard, mouse, and program trackers
- `stop()` stops keyboard, mouse, and program trackers
- errors during stop are either propagated or handled consistently with current cleanup behavior

## Stage 8 - Move Construction Into a Factory If Still Needed

### Purpose

Reduce `SurveillanceManager.__init__` after runtime and routers are extracted.

### Current Responsibility

`SurveillanceManager.__init__` currently builds DAOs, facades, trackers, runtime wrappers, and starts some background behavior. Some of that is acceptable in a composition root, but it makes the manager hard to instantiate in tests.

### Proposed Direction

Create a factory only after the previous extractions show what the constructor should actually receive.

Possible target:

```python
manager = build_surveillance_manager(
    clock=clock,
    async_session_maker=async_session_maker,
    regular_session_maker=regular_session_maker,
    chrome_service=chrome_service,
    arbiter=arbiter,
    facades=facades,
    message_receiver=message_receiver,
    system_status_dao=system_status_dao,
)
```

The manager constructor can then become closer to:

```python
class SurveillanceManager:
    def __init__(self, runtime, message_receiver, status_polling, task_registry, shutdown_coordinator): ...
```

Do not start with this stage. It is easier after the concrete responsibilities have been extracted.

## Suggested Implementation Order

1. Extract `PulseController`.
2. Extract `ActivityNotifier`.
3. Extract `SleepGapHandler`.
4. Clarify or rename `StateMachine` only if still useful.
5. Extract `TaskRegistry`.
6. Extract `PeripheralEventRouter`.
7. Extract `TrackerRuntime`.
8. Consider a surveillance factory or constructor cleanup.

## Worker-Agent Constraints

Each worker agent should take one stage at a time unless explicitly told otherwise.

For each stage:

- Keep public behavior unchanged unless the stage explicitly says otherwise.
- Prefer adding focused tests around the extracted component.
- Avoid broad cleanup, renaming, formatting churn, or unrelated TODO fixes.
- Use existing tests as behavior documentation, but expect some tests to require updates if they assert implementation details.
- Run the relevant Python tests with `win-pytest` from WSL.
- Do not run npm tests/builds from WSL.
- Preserve the central invariant: at most one Activity is active at a time.
- Preserve backend ownership of timing logic.

## Review Checklist

Reviewers should check:

- Did the arbiter or manager actually become thinner, or was code only moved with worse coupling?
- Does the extracted component have a clear single responsibility?
- Does the arbiter still express the session transition workflow clearly?
- Does the manager still express runtime lifecycle clearly?
- Are task ownership and shutdown behavior safer than before?
- Are tests focused on behavior rather than private implementation details?
- Were unrelated product concepts, endpoints, Pursuits, or dashboard behavior left untouched?
