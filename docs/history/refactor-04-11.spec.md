# Refactor Spec: Arbiter Pipeline Testability
# Created: 2026-04-11
# Status: Planning

## Problem Statement

The integration tests for the activity-tracking pipeline are brittle and hard
to maintain. Each test boots the entire pipeline (SurveillanceManager ->
ProgramTracker -> ActivityArbiter -> StateMachine -> KeepAliveEngine ->
ActivityRecorder -> DAOs), pumps events through it, and asserts on every
internal seam using spy-wrapped real objects.

A single test function runs 400-500 lines, creates 15-20 Mock(side_effect=...)
spies, and asserts intermediate call counts at every layer. The reason for this
is that the pipeline has no observable intermediate state except through spies.
When a final assertion fails, there is no way to find which component mangled
the data without instrumenting every boundary.

The root cause is NOT bad tests. The root cause is that the production code
lacks clean boundaries between components. Components interact through
mutation, side effects, and implicit call ordering rather than through explicit
inputs and outputs. To test one component, you must boot every other component.

## Files Involved

### Production code (all under activitytracker/src/activitytracker/)
- arbiter/activity_arbiter.py    -- ActivityArbiter: orchestrator, owns transition_state()
- arbiter/state_machine.py       -- StateMachine: tracks current/prior InternalState
- arbiter/session_polling.py     -- KeepAliveEngine + ThreadedEngineContainer
- arbiter/activity_recorder.py   -- ActivityRecorder: routes sessions to DAOs
- object/arbiter_classes.py      -- InternalState, ApplicationInternalState, ChromeInternalState
- object/classes.py              -- ProgramSession, ChromeSession, Completed* variants, SessionLedger

### Test code (all under activitytracker/tests/)
- integration/program_session_path/conftest.py
- integration/program_session_path/test_fresh_entries.py
- integration/program_session_path/test_with_existing_entries.py
- integration/test_productivity_integration.py
- integration/test_arbiter.py
- helper/program_path/program_path_setup.py    -- setup_recorder_spies(), preexisting data builders
- helper/program_path/program_path_assertions.py
- mocks/mock_engine_container.py               -- MockEngineContainer (deterministic pulse driver)
- mocks/mock_clock.py
- mocks/fake_persistence.py                    -- Fake*Dao classes (in-memory stores)

## Refactoring Steps

Execute these in order. Each step should be a separate commit. After each step,
run `pytest` to confirm nothing is broken. Steps 1-3 are production code
changes. Step 4 is test infrastructure. Step 5 rewrites the integration tests.

Important: Do NOT delete the existing integration tests until replacements
are in place and passing. During the transition, both old and new tests coexist.

### Step 1: StateMachine.set_new_session returns the concluded session

This is the highest-value, lowest-risk change. The existing code uses a
two-step protocol:

    self.state_machine.set_new_session(new_session)
    concluded_session = self.state_machine.get_concluded_session()

There is even a FIXME at activity_arbiter.py:115 acknowledging this should
change. The meaningful result is stored as a side effect in self.prior_state.

#### What to change in state_machine.py:

set_new_session() should RETURN the concluded session directly:

    def set_new_session(self, next_session) -> CompletedProgramSession | CompletedChromeSession | None:
        next_session = snapshot_obj_for_tests(next_session)
        if self.current_state is None:
            # Initialization: no prior session to conclude
            self.current_state = InternalState(None, None, next_session)
            return None

        concluded = self._build_concluded(self.current_state, next_session.start_time)
        self.current_state = InternalState(None, None, next_session)
        return concluded

    def _build_concluded(self, state, incoming_start):
        """Conclude the current session. Returns the completed session or None."""
        if self.is_initialization_session(state.session):
            return None
        duration = incoming_start.dt - state.session.start_time.dt
        if duration.total_seconds() < -60:
            raise SuspiciousDurationError("Negative duration")
        session_copy = snapshot_obj_for_tests(state.session)
        completed = session_copy.to_completed(incoming_start)
        completed.duration = duration
        return completed

Keep self.prior_state assignment if other code reads it, but the return value
is now the primary interface. get_concluded_session() can stay temporarily but
should be marked deprecated.

#### What to change in activity_arbiter.py:

Replace the two-step protocol:

    # Before:
    self.state_machine.set_new_session(new_session)
    concluded_session = self.state_machine.get_concluded_session()

    # After:
    concluded_session = self.state_machine.set_new_session(new_session)

This appears in transition_state() around lines 150-152.

#### What to change in tests:

Any test that calls state_machine.set_new_session() and then
get_concluded_session() should switch to using the return value.
Search for "get_concluded_session" across the test suite.

#### How to verify:

Write a focused unit test for StateMachine alone:

    def test_state_machine_concludes_with_correct_duration():
        sm = StateMachine(mock_clock)
        result = sm.set_new_session(session_a)
        assert result is None  # initialization

        result = sm.set_new_session(session_b)
        assert result is not None
        assert result.start_time == session_a.start_time
        assert result.duration == session_b.start_time.dt - session_a.start_time.dt

    def test_state_machine_three_sessions_form_chain():
        sm = StateMachine(mock_clock)
        sm.set_new_session(session_a)
        concluded_a = sm.set_new_session(session_b)
        concluded_b = sm.set_new_session(session_c)
        assert concluded_a.end_time == concluded_b.start_time

These tests replace the "assert_sessions_form_a_chain" blocks that currently
live inside the 500-line integration tests.


### Step 2: Extract TransitionOutcome from ActivityArbiter

Add a small dataclass and a helper method to transition_state() so that the
transition decision is observable as a value.

Do NOT try to make transition_state pure. Sleep handling, engine replacement,
and recorder notification are inherently lifecycle-y. The goal is just to
make the decision inspectable.

#### Add to activity_arbiter.py (or a new file arbiter/transition_outcome.py):

    from dataclasses import dataclass

    @dataclass
    class TransitionOutcome:
        new_session: ProgramSession | ChromeSession
        concluded_session: CompletedProgramSession | CompletedChromeSession | None
        was_initialization: bool

#### Add method to ActivityArbiter:

    def _advance_state(self, new_session) -> TransitionOutcome:
        was_initialization = self.state_machine.current_state is None
        concluded = self.state_machine.set_new_session(new_session)
        return TransitionOutcome(new_session, concluded, was_initialization)

#### Refactor transition_state() to use _advance_state:

transition_state() currently has a big if/else on self.state_machine.current_state.
Replace the state machine interaction with:

    outcome = self._advance_state(new_session)

Then use outcome.was_initialization to decide the if/else branch, and
outcome.concluded_session instead of calling get_concluded_session().

Keep sleep detection and engine lifecycle in transition_state() for now.
The split into _handle_sleep_gap() / _replace_pulse() / _notify_recorders()
can happen later if it pays off.

#### How to verify:

    def test_first_session_is_initialization():
        arbiter = make_arbiter_with_no_sleep()
        outcome = arbiter._advance_state(session_a)
        assert outcome.was_initialization is True
        assert outcome.concluded_session is None

    def test_second_session_concludes_first():
        arbiter = make_arbiter_with_no_sleep()
        arbiter._advance_state(session_a)
        outcome = arbiter._advance_state(session_b)
        assert outcome.was_initialization is False
        assert outcome.concluded_session.start_time == session_a.start_time


### Step 3: Add KeepAliveEngine.compute_pulses static method

The pulse math (full windows vs partial remainder) is currently only observable
by spying on recorder.add_ten_sec_to_end_time and recorder.add_partial_window.
Extract the math into a testable pure function.

#### Add to session_polling.py KeepAliveEngine class:

    @staticmethod
    def compute_pulses(duration_in_seconds: int, window_size: int = 10) -> tuple[int, int]:
        """Given a session duration, return (full_pulse_count, remainder_seconds)."""
        full_pulses = duration_in_seconds // window_size
        remainder = duration_in_seconds % window_size
        return full_pulses, remainder

This does NOT change existing behavior. iterate_loop() and conclude() stay
the same. This is purely an addition for testability.

#### How to verify:

    def test_65_seconds():
        assert KeepAliveEngine.compute_pulses(65) == (6, 5)

    def test_exact_boundary():
        assert KeepAliveEngine.compute_pulses(30) == (3, 0)

    def test_sub_window():
        assert KeepAliveEngine.compute_pulses(7) == (0, 7)


### Step 4: Create RecordingActivityRecorder test double

This replaces the pattern of wrapping every method in Mock(side_effect=...).
Instead of 15 spies on the real ActivityRecorder, arbiter tests use this
lightweight double that captures what happened.

#### Create new file: activitytracker/tests/mocks/recording_activity_recorder.py

    from activitytracker.util.copy_util import snapshot_obj_for_tests

    class RecordingActivityRecorder:
        """
        Test double for ActivityRecorder. Captures all calls as lists
        so tests can assert on what happened without spying on DAOs.

        Implements the same interface the Arbiter expects:
        - on_new_session(session)
        - on_state_changed(session)
        - add_ten_sec_to_end_time(session)
        - add_partial_window(amount, session)
        """
        def __init__(self):
            self.new_sessions = []
            self.concluded_sessions = []
            self.full_windows = []
            self.partial_windows = []

        def on_new_session(self, session):
            self.new_sessions.append(snapshot_obj_for_tests(session))

        def on_state_changed(self, session):
            if session is not None:
                self.concluded_sessions.append(snapshot_obj_for_tests(session))

        def add_ten_sec_to_end_time(self, session):
            self.full_windows.append(snapshot_obj_for_tests(session))

        def add_partial_window(self, amount, session):
            self.partial_windows.append((amount, snapshot_obj_for_tests(session)))

This object is used for arbiter-level tests that care about "did the arbiter
route sessions correctly?" It does NOT test DAO persistence -- that is a
separate concern tested separately.

Also: rename MockEngineContainer to DeterministicPulseContainer (or at
minimum add an alias). It is not merely a mock -- it is a test clock for
session duration. Keep it; do not try to use the real ThreadedEngineContainer
in tests.


### Step 5: Rewrite integration tests as layered tests

Replace the three problem files with focused tests at each layer. The new
tests live alongside the old ones initially. Delete the old ones only after
the new ones pass.

#### Layer A: StateMachine unit tests
File: tests/unit/arbiter/test_state_machine.py

Test that set_new_session returns correct concluded sessions, durations are
computed correctly, sessions form chains, initialization returns None,
conclude_without_replacement works. No mocks needed. ~10 focused tests.

#### Layer B: Arbiter lifecycle tests (using RecordingActivityRecorder)
File: tests/unit/arbiter/test_arbiter_lifecycle.py

Build an arbiter with: mock clock, FakeSystemStatusDao (no sleep detected),
DeterministicPulseContainer, and RecordingActivityRecorder. Feed it a
sequence of sessions. Assert on the recorder's captured lists:

    for session in chronological_sessions:
        arbiter.transition_state(session)

    assert len(recorder.new_sessions) == 4
    assert len(recorder.concluded_sessions) == 3
    assert len(recorder.partial_windows) == 3
    assert recorder.concluded_sessions[0].end_time == recorder.concluded_sessions[1].start_time

No DAO spies. No SurveillanceManager. ~5 focused tests covering:
- fresh sessions (all new)
- mixed program + chrome sessions
- session with pre-existing entries (if relevant at arbiter level)

#### Layer C: Recorder persistence tests
File: tests/integration/test_recorder_persistence.py

Test ActivityRecorder directly by calling its methods with hand-crafted
sessions and asserting on DAO state:

    recorder.on_new_session(program_session_a)
    recorder.add_ten_sec_to_end_time(program_session_a)
    recorder.add_partial_window(5, program_session_a)
    recorder.on_state_changed(completed_session_a)

    logs = program_logging_dao.read_all()
    summaries = program_summary_dao.read_all()
    assert logs[0].duration_in_sec == 15
    assert summaries[0].hours_spent == pytest.approx(15 / 3600)

Uses Fake*Dao classes for the "fresh entries" variant and real DB for the
variant that tests actual SQL (test_productivity_integration test 3).

#### Layer D: Thin end-to-end smoke test
File: tests/integration/test_pipeline_smoke.py

One test that pumps events through the full pipeline and asserts ONLY on
final DB state. No spies. No intermediate assertions.

    arbiter = build_full_pipeline(fake_daos)
    for event in test_events:
        arbiter.set_program_state(event)

    summaries = fake_daos.program_summary.read_all()
    assert len(summaries) == 4
    assert summaries[0].hours_spent == pytest.approx(65 / 3600)

If this test fails and the Layer A-C tests pass, you know the wiring is
wrong. If Layer A-C tests fail, you know exactly which component broke.


## What NOT to do

- Do not try to make ActivityArbiter.transition_state() pure. It manages
  thread lifecycle and that's fine.
- Do not remove MockEngineContainer. Rename it if you want, but the real
  ThreadedEngineContainer should not be used in tests. Thread sleeps and
  join timeouts make tests flaky.
- Do not put a permanent event log into production ActivityRecorder. The
  RecordingActivityRecorder is a test-only double.
- Do not try to remove InternalState or the arbiter_classes module in this
  refactor. That is a separate cleanup. The existing InternalState is
  mostly unused baggage (active_application, is_chrome) but removing it
  is out of scope.
- Do not refactor the SurveillanceManager or ProgramTracker. Those are
  upstream of the arbiter. The current tests that boot SurveillanceManager
  are testing too much; the new tests start at the arbiter boundary.
- Do not change the KeepAliveEngine's iterate_loop/conclude behavior. The
  compute_pulses static method is purely additive.


## Ordering and Risk

Step 1 is the safest and highest value. It can be done independently.
Step 2 depends on Step 1.
Step 3 is independent of everything.
Step 4 is independent of Steps 1-3 but is needed for Step 5.
Step 5 depends on all prior steps.

If you bail out after Step 1 alone, the codebase is already better.


## Test Data

The test fixtures in conftest.py define four ProgramSessions with known
timestamps and durations:

    session1: Chrome,    16:14:50  (duration to next: ~65s)
    session2: Postman,   16:15:55  (duration to next: ~8s)
    session3: VSCode,    16:16:03  (duration to next: ~14s)
    session4: Chrome,    16:16:17  (still active, duration 0)

These durations drive the expected pulse counts:
- 65s -> 6 full pulses, 5 remainder
-  8s -> 0 full pulses, 8 remainder
- 14s -> 1 full pulse,  4 remainder

test_productivity_integration.py uses a separate set of events (pr_events_v2
+ ch_events_v2) that interleave programs and chrome tabs. These are defined
inline in that file starting around line 524.

Reuse the existing test data. Do not invent new session fixtures unless the
existing ones don't cover a case.
