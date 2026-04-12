# God Object Refactor Plan - 2026-04-12

Status: Stages 1–7 implemented — ready for /code-review. Stage 8 pending.

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

## Implementation notes (filled in by /developer)

### Stage 1 — Extract `PulseController`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- `PulseController` owns engine construction + container lifecycle → `activitytracker/src/activitytracker/arbiter/pulse_controller.py`
- Arbiter no longer calls `add_first_engine` / `replace_engine` / container `start` / `stop`, nor instantiates `engine_class` directly → `activitytracker/src/activitytracker/arbiter/activity_arbiter.py` (transitions now delegate to `pulse_controller.start_first` / `replace_with` / `stop`)
- Recorder injection resolved via `set_recorder(...)` because all call sites (prod + tests) add the recorder post-construction → `activity_arbiter.py:add_recorder_listener` forwards to `pulse_controller.set_recorder`

**Tests added**
- `activitytracker/tests/arbiter/test_pulse_controller.py::test_start_first_adds_and_starts_engine` — first session wires an engine into the container then starts it
- `...::test_replace_with_stops_replaces_and_starts` — replacement performs stop → replace_engine → start in that order
- `...::test_stop_stops_container` — stop delegates to container
- `...::test_engine_built_with_recorder_set_via_setter` — recorder set via setter flows into built engine
- `...::test_engine_built_with_none_recorder_before_set` — pre-recorder behavior preserved (engine built with `None`, matching prior arbiter init-phase behavior)

**Deviations from spec**
- Chose `set_recorder(...)` over constructor injection because the recorder is always added post-construction in existing callers (prod `service_dependencies.py` and all tests). Spec explicitly allowed either.
- `PulseController.__init__` takes only `(threaded_container, engine_class)` — the recorder parameter is omitted in favor of the setter, per the point above.

**Deferred / noticed but not done**
- `transition_state` references an undefined `incoming_session_start` in the suspicious-status-write branch. Spec assigns this to Stage 3 (`SleepGapHandler`). Left untouched.
- Stale commented-out `self.current_pulse` FIXME/TODO comments in `session_polling.py` — not in scope.
- `activitytracker/tests/helper/test_truncation.py` fails when running the full suite (passes in isolation). Pre-existing test-order flakiness unrelated to this refactor.
- Stages 2–8.

**For the reviewer**
- Order of operations inside `transition_state` non-initialization branch was preserved: `notify_of_new_session(...)` still fires before any pulse swap. Worth a glance.
- Removed the `if self.current_pulse is None: raise ValueError(...)` guard: `pulse_controller` is always constructed in `__init__`, so the branch was unreachable. If reviewer wants it back as a defensive check inside `PulseController`, easy to add.
- Kept legacy `print("Starting pulse in init loop")` for now — not in scope to clean up.

### Stage 2 — Extract `ActivityNotifier`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- UI and recorder listener mechanics moved out of the arbiter → `activitytracker/src/activitytracker/arbiter/activity_notifier.py`
- Listener-shape check (`hasattr(listener, "on_state_changed")`) lives in the notifier, not the arbiter
- Arbiter retains `add_ui_listener` / `add_recorder_listener` as thin delegations → `activity_arbiter.py`
- `activity_recorder` is now a property on the arbiter delegating to `notifier.recorder` (two existing integration tests read this attribute)

**Tests added**
- `tests/arbiter/test_activity_notifier.py::test_ui_listener_fires_on_display_update`
- `...::test_display_update_is_noop_without_listener`
- `...::test_add_recorder_listener_rejects_missing_on_state_changed`
- `...::test_notify_new_session_snapshots_session` — mutation-after-notify does not leak into recorder
- `...::test_notify_completed_session_passes_none_through`
- `...::test_notify_completed_session_noop_without_recorder`
- `...::test_recorder_property_returns_registered_listener`

**Deviations from spec**
- Method name choices follow the spec's sketched workflow: `notify_new_session`, `notify_completed_session`, `notify_display_update`. The arbiter's old `notify_summary_dao` / `notify_of_new_session` names are retired — no callers outside the arbiter referenced them.

### Stage 3 — Extract `SleepGapHandler`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- New `SleepGapHandler.inspect_before_transition(incoming)` owns `detect_awakening_from_sleep()`, the yellow sleep-warning log, `get_latest_write_time()`, and the suspicious-status-write warning → `activitytracker/src/activitytracker/arbiter/sleep_gap_handler.py`
- `SleepGapDecision(should_flush, end_time)` dataclass returned to the arbiter
- `ActivityArbiter.transition_state` now reads: `decision = sleep_gap_handler.inspect_before_transition(new_session); if decision.should_flush: self.flush_and_reset(decision.end_time)` — closer to the spec's orchestration sketch
- Arbiter keeps `flush_and_reset(...)` itself, per the spec's note ("The arbiter can keep the actual `flush_and_reset(...)` operation initially")

**Tests added**
- `tests/arbiter/test_sleep_gap_handler.py::test_no_awakening_returns_no_flush_decision`
- `...::test_awakening_detected_returns_flush_with_gap_time`
- `...::test_suspicious_latest_write_does_not_raise_name_error` — pins the Stage 3 bugfix
- `...::test_recent_latest_write_produces_no_flush`

**Intentional behavior change**
- Fixed the undefined-name bug in the suspicious-status-write branch. Old arbiter code referenced `incoming_session_start.dt` — a name never bound in that scope. The branch is log-only but would have raised `NameError` if both `latest_status_write` existed and the write was >2 min stale. The handler now computes `minutes_since_write = (incoming.start_time.dt - latest_status_write.dt).total_seconds() / 60` and emits the same warning. The suspicious-write threshold (2 min) is named `_SUSPICIOUS_WRITE_THRESHOLD`.

**Deferred / noticed but not done**
- Dead TODO/FIXME comments from the old `transition_state` block are gone with the refactor — not a separate cleanup, just fell away with the code.
- `transition_state` now reads close to the spec's orchestration sketch; further polish (renaming `StateMachine` → `ActiveSessionState`) is explicitly Stage 4.
- Full test suite still shows `tests/helper/test_truncation.py` failing when run with the whole suite (passes in isolation). Pre-existing test-order flakiness — unchanged.

**For the reviewer**
- The `suspicious_write_time` threshold was hardcoded to 2 minutes before and remains 2 minutes; I made it a named class-level constant. If you prefer a module constant or a config lookup, easy swap.
- `ActivityNotifier.add_recorder_listener` raises `AttributeError` for listeners missing `on_state_changed` — same exception the old arbiter raised. Preserved verbatim so any caller catching it still works.
- Order of operations inside non-init `transition_state`: display → advance → notify_new → pulse.replace → notify_completed. This matches the spec's sketch. The prior arbiter did display → advance → notify_new → pulse.stop → pulse.replace+start → notify_completed; equivalent since `pulse_controller.replace_with` internally does stop→replace→start.
- No longer importing `datetime`, `timedelta`, `timezone`, `snapshot_obj_for_tests` in the arbiter — they moved to the extracted components.

### Stage 4 — Rename `StateMachine` → `ActiveSessionState`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- Class renamed from `StateMachine` to `ActiveSessionState` → `activitytracker/src/activitytracker/arbiter/active_session_state.py` (formerly `state_machine.py`)
- Class docstring updated to reflect "container for the currently active session" (the spec/TODOs noted it had already drifted from being a finite state machine)
- `ActivityArbiter.state_machine` attribute renamed to `active_session_state`
- All direct readers updated: `tests/unit/arbiter/test_state_machine.py`, `tests/arbiter/test_state_machine.py`, `tests/integration/test_arbiter.py`, `tests/integration/test_arbiter_after_sleep.py`

**Tests added**
- None (spec: "may be a rename-only refactor at first"; all existing tests exercise behavior and continue to pass).

**Deviations from spec**
- Method names kept as-is (`set_new_session`, `conclude_without_replacement_at_time`, `conclude_without_replacement`, `is_initialization_session`, `current_state`). The spec sketched `advance_to / conclude_at / conclude_now / has_current_session` as a *possible* target but explicitly said "This may be a rename-only refactor at first." You confirmed `ActiveSessionState` as the class name; method rename would have churned ~20 test assertions without behavior payoff.
- Test file `tests/arbiter/test_state_machine.py` kept at its current path with its `TestStateMachine` pytest class — pytest collects by `Test*` prefix, behavior unchanged, renaming the file would just churn the diff. Flag for a future sweep if desired.

**Deferred / noticed but not done**
- Method renames → future stage if wanted.
- Dead FIXME/TODO comments inside `active_session_state.py` (e.g., "FIXME: This whole file can go. It's just a session container.") left untouched — the rename partially answers them, but a cleanup pass is out of scope.

### Stage 5 — Extract `TaskRegistry`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- New `TaskRegistry(loop)` with `create_task(coro, *, name)` and `async cancel_all(timeout=3.0) -> int` → `activitytracker/src/activitytracker/util/task_registry.py`
- `SurveillanceManager.__init__` constructs `self.tasks = TaskRegistry(self.loop)`
- `handle_keyboard_ready_for_db` and `handle_mouse_ready_for_db` now route through `self.tasks.create_task(..., name=...)` instead of `self.loop.create_task(...)`
- `cancel_pending_tasks` reduced from ~95 lines of `asyncio.all_tasks()` scanning + name/frame heuristics to a three-line body: stop polling, `await self.tasks.cancel_all()`, report count

**Tests added**
- `tests/util/test_task_registry.py::test_create_task_is_tracked`
- `...::test_cancel_all_cancels_pending_and_returns_count`
- `...::test_cancel_all_skips_already_completed_tasks`
- `...::test_cancel_all_returns_within_timeout_for_stubborn_task` — asserts the timeout bounds wait duration even when the task resists cancellation

**Intentional behavior change (spec-driven)**
- `cancel_pending_tasks` no longer inspects `asyncio.all_tasks()` or filters by `task.get_stack()` filename or task-name heuristics ("uvicorn", "starlette", "mouse", "keyboard", etc.). The manager now cancels *exactly* the tasks it created. Framework/uvicorn tasks were already being skipped on purpose by the heuristic; the registry-owned approach makes that guarantee structural rather than name-based. `MessageReceiver.async_stop()` continues to own its own cleanup independently.

**Deferred / noticed but not done**
- `SurveillanceManager.__init__` still builds DAOs, facades, tracker threads — that's Stage 7 / Stage 8.
- Stage 6 (`PeripheralEventRouter`): the two `handle_*_ready_for_db` methods are ripe for extraction, now that they route through the registry. Clean handoff for the next stage.
- Pre-existing `tests/helper/test_truncation.py` full-suite flakiness unchanged.

**For the reviewer**
- `TaskRegistry.tasks` is a public list, exposed for assertion in tests. If you prefer it private, happy to swap.
- `cancel_all` swallows `asyncio.TimeoutError` (returns the pending count anyway) to preserve the old behavior of not crashing on stubborn tasks. The timeout bound is enforced via `asyncio.wait_for`.
- Debug-print noise from the old implementation is gone. If any operational script relied on the "Found N uvicorn/starlette tasks" output, it's no longer emitted — net positive, but worth a grep in ops scripts.

### Stage 6 — Extract `PeripheralEventRouter`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- New `PeripheralEventRouter` owns keyboard/mouse persistence routing → `activitytracker/src/activitytracker/peripheral_event_router.py:1`
- Keyboard aggregate events schedule timeline and keyboard DAO writes through the injected task registry → `activitytracker/src/activitytracker/peripheral_event_router.py:8`
- Mouse aggregate events schedule timeline and mouse DAO writes through the injected task registry → `activitytracker/src/activitytracker/peripheral_event_router.py:15`
- `SurveillanceManager` constructs the router after creating the DAOs and `TaskRegistry` → `activitytracker/src/activitytracker/surveillance_manager.py:107`
- `SurveillanceManager` passes router methods into `KeyboardTrackerCore` and `MouseTrackerCore` instead of owning the persistence handler bodies → `activitytracker/src/activitytracker/surveillance_manager.py:121`

**Tests added**
- `activitytracker/tests/unit/test_peripheral_event_router.py::test_keyboard_events_schedule_timeline_and_keyboard_writes` — proves keyboard events schedule timeline + keyboard DAO writes
- `activitytracker/tests/unit/test_peripheral_event_router.py::test_mouse_events_schedule_timeline_and_mouse_writes` — proves mouse events schedule timeline + mouse DAO writes
- `activitytracker/tests/unit/test_peripheral_event_router.py::test_router_uses_task_registry` — proves router routing goes through the injected task registry

**Deviations from spec**
- none

**Deferred / noticed but not done**
- Stage 7 (`TrackerRuntime`) still owns extracting tracker thread lifecycle from `SurveillanceManager`.
- Stage 8 constructor/factory cleanup remains deferred.
- Pre-existing broad dirty worktree state is unrelated to this stage and was left untouched.

**For the reviewer**
- I removed the old `SurveillanceManager.handle_keyboard_ready_for_db` and `handle_mouse_ready_for_db` methods rather than keeping compatibility wrappers. `rg` found no other call sites, and the tracker cores now receive the router methods directly.
- The task names (`timeline-keyboard`, `keyboard-dao`, `timeline-mouse`, `mouse-dao`) were preserved exactly from Stage 5.

### Stage 7 — Extract `TrackerRuntime`

**Date implemented:** 2026-04-12
**Commit(s):** uncommitted

**Spec coverage**
- New `TrackerRuntime` owns wrapping keyboard, mouse, and program tracker cores in `ThreadedTracker` instances → `activitytracker/src/activitytracker/tracker_runtime.py:4`
- `TrackerRuntime.start()` starts keyboard, mouse, and program tracker threads → `activitytracker/src/activitytracker/tracker_runtime.py:16`
- `TrackerRuntime.stop()` stops keyboard, mouse, and program tracker threads → `activitytracker/src/activitytracker/tracker_runtime.py:21`
- `SurveillanceManager.__init__` now constructs `TrackerRuntime` instead of storing `keyboard_thread`, `mouse_thread`, and `program_thread` itself → `activitytracker/src/activitytracker/surveillance_manager.py:135`
- `SurveillanceManager.start_trackers()` delegates tracker startup to the runtime → `activitytracker/src/activitytracker/surveillance_manager.py:145`
- `SurveillanceManager.cleanup()` delegates tracker shutdown to the runtime → `activitytracker/src/activitytracker/surveillance_manager.py:209`

**Tests added**
- `activitytracker/tests/unit/test_tracker_runtime.py::test_start_starts_keyboard_mouse_and_program_trackers` — proves `start()` starts all three tracker wrappers
- `activitytracker/tests/unit/test_tracker_runtime.py::test_stop_stops_keyboard_mouse_and_program_trackers` — proves `stop()` stops all three tracker wrappers
- `activitytracker/tests/unit/test_tracker_runtime.py::test_stop_error_propagates_and_skips_later_trackers` — documents current sequential stop behavior when a stop error occurs

**Deviations from spec**
- `TrackerRuntime` receives already-built tracker cores and wraps them in `ThreadedTracker` itself. The spec explicitly allowed either already-built tracker cores or threaded trackers; this moves slightly more lifecycle detail out of `SurveillanceManager` without starting the Stage 8 factory cleanup.

**Deferred / noticed but not done**
- Stage 8 constructor/factory cleanup remains deferred.
- `SurveillanceManager.__init__` still builds DAOs, facades, tracker cores, the router, and the runtime. That construction pressure is exactly what Stage 8 is for.
- Existing `cleanup()` behavior still stops `program_online_polling` in more than one path. Left unchanged because this stage is a mechanical tracker-thread extraction.

**For the reviewer**
- `TrackerRuntime.stop()` intentionally propagates the first tracker stop exception and does not stop later trackers after that exception. This matches the old `SurveillanceManager.cleanup()` try block, where the first stop exception would jump to the `except`.
- I kept `SurveillanceManager.start_trackers()` as the public method and only changed its body to delegate, preserving callers while removing thread ownership from the manager.
