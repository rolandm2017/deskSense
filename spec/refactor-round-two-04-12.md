# Refactor Spec Round Two: Finish the Cleanup
# Created: 2026-04-12
# Status: Planning
# Prior spec: refactor-04-11.spec.md

## Context from the inception of round one of the refactor

The Core Problem

  You've built what are essentially system-level trace tests. Each test boots the entire pipeline —
  SurveillanceManager -> ProgramTracker -> ActivityArbiter -> StateMachine -> KeepAliveEngine ->
  ActivityRecorder -> multiple DAOs — then pumps events through it and asserts on every seam along the way
  using spy-wrapped real objects.

  The reason you need dozens of intermediate assertions is architectural: the pipeline has no observable
  intermediate state except through spies. The arbiter mutates sessions in-place, passes them between
  components, and the only "output" is what lands in DAOs at the end. So when the final assertion fails, you
   have no idea which component mangled the data without instrumenting every boundary.

  This creates a vicious cycle:
  1. Something breaks mid-pipeline
  2. You add assertions at each step to find where
  3. Now the test is 500 lines and coupled to internal call ordering
  4. You change an internal detail, 40 assertions break
  5. You can't tell which failures are "real" vs. "test structure artifact"

  What's Actually Being Tested

  Looking at what the assertions actually verify, these tests care about three things:

  1. Data integrity: Does a ProgramSession's exe_path, window_title, start_time survive the journey from
  facade to DAO?
  2. Timing math: Do the durations (pulse counts, partial windows, total hours) add up correctly?
  3. Call ordering/counts: Did on_new_session get called N times, finalize_log N-1 times, etc.?

  Items 1 and 2 are genuinely valuable. Item 3 is mostly testing how the code works rather than what it does
   — and that's where the fragility lives.

  Why It's Hard to Fix With Just Better Tests

  The pipeline has a design property that makes it inherently hard to test at a granular level: the
  ActivityArbiter is a God object that orchestrates state machine transitions, engine lifecycle, and
  recorder notifications all in one method (transition_state). The StateMachine also does mutation-in-place
  via _conclude_session, modifying the InternalState.session field to a Completed* type. The KeepAliveEngine
   calls back into the ActivityRecorder directly.

  This means you can't test "does the Arbiter hand off correctly to the Recorder?" without also running the
  StateMachine, the EngineContainer, and setting up all the spies. There's no clean boundary to test in
  isolation.

## Problem Statement

Round one landed the production-code seams and added new focused tests, but
did not retire the original smelly tests. The suite now has BOTH the new
clean tests AND the old 400-1400-line spy-laden tests running side by side.
This is worse than the starting state: more total code, more duplication,
and the original pain (when it fails, where did it fail?) still lives in the
old files.

Current state, as of 2026-04-12:

| File                                              | Lines | Mock(side_effect) spies |
|---------------------------------------------------|------:|------------------------:|
| tests/integration/program_session_path/test_fresh_entries.py        |  509 |  9 |
| tests/integration/program_session_path/test_with_existing_entries.py|  523 |  9 |
| tests/integration/test_productivity_integration.py                  | 1396 | 23 |
| tests/integration/test_pipeline_smoke.py                            |   67 |  0 |
| tests/integration/test_recorder_persistence.py                      |   90 |  0 |
| tests/unit/arbiter/test_arbiter_lifecycle.py                        |   59 |  0 |
| tests/unit/arbiter/test_state_machine.py                            |   68 |  0 |

Round one was NOT supposed to leave both sets living side by side. The spec
said "Delete the old ones only after the new ones pass." Deletion never
happened, and the new tests do not yet cover everything the old ones did.

Also, test_productivity_integration.py was out of scope in round one but is
the biggest single offender at 1396 lines. It was not mentioned in the first
spec because the developer only flagged the program_session_path files. It
needs to be addressed now.

## Goals of Round Two

1. New layered tests cover all behavior the old tests covered.
2. Old smelly tests are deleted.
3. The production API is tightened to remove now-dead code paths.

Non-goal: no further restructuring of production code beyond removing
now-unused methods. The seams landed in round one are sufficient.


## Files Involved

### Production code
- activitytracker/src/activitytracker/arbiter/state_machine.py
  -- get_concluded_session() is deprecated and has no callers. Remove it.
  -- prior_state and the self.prior_state.session = concluded mutation
     only exist to feed get_concluded_session(). Both can go.

### Tests to retire (delete at the end)
- activitytracker/tests/integration/program_session_path/test_fresh_entries.py
- activitytracker/tests/integration/program_session_path/test_with_existing_entries.py
- activitytracker/tests/integration/program_session_path/conftest.py  (if no other users)
- activitytracker/tests/integration/program_session_path/__init__.py  (whole folder goes)
- activitytracker/tests/helper/program_path/program_path_assertions.py  (if no other users)
- activitytracker/tests/helper/program_path/program_path_setup.py      (if no other users)
- activitytracker/tests/integration/test_productivity_integration.py    (after splitting)

Before deleting, grep each file's exports to confirm no other test imports
them. The program_path_setup.py module exports group_of_preexisting_summaries
and group_of_preexisting_logs which are useful; move them into the new
preexisting-entries test if that is the only remaining consumer.

### Tests to extend
- activitytracker/tests/integration/test_pipeline_smoke.py
  -- Currently only asserts totals. Add per-row assertions.

### New tests to create
- activitytracker/tests/integration/test_recorder_persistence_preexisting.py
- activitytracker/tests/integration/test_tracker_to_arbiter.py
- activitytracker/tests/integration/test_chrome_service_to_arbiter.py
- activitytracker/tests/integration/test_dao_duration_reconciliation.py
- activitytracker/tests/integration/test_gathering_date.py
- activitytracker/tests/integration/test_dashboard_weekly_productivity.py


## Plan

Execute in order. Each step is a separate commit. Nothing is deleted until
Step 7.


### Step 1: Extend test_pipeline_smoke.py

Currently the smoke test only asserts that total seconds match and row
counts are right. To retire test_fresh_entries.py we need the smoke test
to also verify per-row integrity.

Add assertions to test_pipeline_smoke_final_db_state_only (or add a second
test in the same file):

    for i, session in enumerate(sessions[:-1]):
        # The last session is still active in the arbiter; skip it.
        matching_log = find_log_for(session, program_logging, chrome_logging)
        assert matching_log.duration_in_sec == durations[i]
        assert matching_log.exe_path_as_id == session.exe_path  # or domain equivalent
        assert matching_log.program_name == session.window_title

        matching_summary = find_summary_for(session, program_summary, chrome_summary)
        assert matching_summary.hours_spent == pytest.approx(
            durations[i] / SECONDS_PER_HOUR
        )

Keep the test under 150 lines. No spies. This replaces the bulk of what
test_fresh_entries.py asserted.


### Step 2: Create test_recorder_persistence_preexisting.py

The only unique coverage in test_with_existing_entries.py is the case where
a DailyProgramSummary already exists for today with some hours_spent value,
and a new session should ADD to it rather than replace it.

Create a focused test calling the recorder directly:

    def test_recorder_adds_to_existing_summary():
        recorder, p_summary, p_logging = build_recorder_with_fakes()
        session = make_test_session()

        # Seed: a summary already exists with 1 hour recorded
        preexisting = make_preexisting_summary(session, starting_hours=1.0)
        p_summary.add_new_item(preexisting)

        # Act
        recorder.on_new_session(session)
        recorder.add_ten_sec_to_end_time(session)
        recorder.add_partial_window(5, session)
        recorder.on_state_changed(session.to_completed(...))

        # Assert
        summaries = p_summary.read_all()
        assert len(summaries) == 1  # Not duplicated
        assert summaries[0].hours_spent == pytest.approx(1.0 + 15 / SECONDS_PER_HOUR)
        assert len(p_logging.read_all()) == 1  # A new log IS created each session

Reuse make_preexisting_summary from helper/program_path/program_path_setup.py
or inline a simpler version. ~40 lines.


### Step 3: Create test_tracker_to_arbiter.py

Rescue test_program_tracker_to_arbiter from test_productivity_integration.py.
It tests: facade yields program dicts, ProgramTracker converts them to
ProgramSessions, arbiter.set_program_state receives them in order with
expected fields.

Copy the existing test roughly as-is but strip it down. It is already the
least bad of the three tests in test_productivity_integration.py. Aim
for ~150 lines. Keep the MockProgramFacade pattern. Assert only on what
reaches arbiter.set_program_state -- do not follow the data further. The
arbiter's own behavior is already tested by test_arbiter_lifecycle.py.


### Step 4: Create test_chrome_service_to_arbiter.py

Rescue test_chrome_svc_to_arbiter_path the same way. Copy, strip to the
essentials. ~80 lines. Assert only on spy_on_set_chrome_state call args.


### Step 5: Create test_dao_duration_reconciliation.py and test_gathering_date.py

These replace the middle chunk of test_arbiter_to_dao_layer, which verified
that log durations sum to summary hours within tolerance, and that
gathering_date is correct on every row.

test_dao_duration_reconciliation.py:
    Seed the real DB via the real DAOs (not via arbiter). For each program:
    start_session, push_window_ahead_ten_sec N times, add_used_time(remainder),
    finalize_log. Assert sum(log.duration_in_sec) == summary.hours_spent * 3600
    within tolerance. No arbiter, no state machine.
    ~100 lines.

test_gathering_date.py:
    Seed one session through the recorder with a known timezone-aware
    start_time. Assert gathering_date on logs and summaries equals the
    expected UTC start-of-day. ~50 lines.


### Step 6: Create test_dashboard_weekly_productivity.py

Replaces the end of test_arbiter_to_dao_layer (the dashboard_service part).

Seed the real DB directly with DailyProgramSummary and DailyChromeSummary
rows for a known day. No arbiter, no recorder, no facade. Just:

    program_summary_dao.add_new_item(fake_summary_productive)
    program_summary_dao.add_new_item(fake_summary_leisure)

    result = dashboard_service.get_weekly_productivity_overview(start_of_week)

    day_entry = find_day_in_result(result, expected_date)
    assert day_entry["productivity"] > 0
    assert day_entry["leisure"] > 0
    assert day_entry["productivity"] + day_entry["leisure"] == pytest.approx(
        expected_total_hours
    )

This is the test that was originally trying to find a bug in
get_weekly_productivity_overview that yielded 28-hour days. By testing it
with seeded data, future bugs in that function become trivially findable.
~80 lines.


### Step 7: Delete the old tests

Once Steps 1-6 are green, delete:
- activitytracker/tests/integration/program_session_path/  (whole folder)
- activitytracker/tests/integration/test_productivity_integration.py

Grep for imports before deleting helpers. If helper/program_path/ modules
are unused, delete them too.

Run the full test suite. Expect a net reduction of roughly:
    -509 -523 -1396 +150 +40 +150 +80 +100 +50 +80 = ~-1778 lines


### Step 8: Remove get_concluded_session and prior_state

In state_machine.py:
- Delete get_concluded_session()
- Delete self.prior_state initialization
- Delete self.prior_state = self.current_state in set_new_session
- Delete self.prior_state.session = concluded in set_new_session

The StateMachine then has only current_state, which matches its actual role
(a container for the current session, as the FIXME at the top of the class
says).

Run the full test suite. Nothing should break.


## Verification Checklist

Before declaring round two done:

- [ ] pytest passes on the full suite
- [ ] No file in tests/integration/ exceeds 200 lines
- [ ] No Mock(side_effect=...) usage remains in tests/integration/
- [ ] program_session_path/ folder is gone
- [ ] test_productivity_integration.py is gone
- [ ] StateMachine has no prior_state, no get_concluded_session
- [ ] Total test line count is meaningfully lower than before round one


## Risk notes

The DB-backed tests (test_dao_duration_reconciliation,
test_gathering_date, test_dashboard_weekly_productivity) depend on
regular_session_maker and plain_asm fixtures from the existing conftest.
Reuse those. If they are currently only wired in
test_productivity_integration.py, promote them to a higher conftest.

Running tests requires Windows-side pytest. Agents in WSL cannot execute
npm; Python tests should work but confirm with the user if in doubt.

test_arbiter.py and test_arbiter_after_sleep.py were not touched in round
one and are not in scope here. If they have the same smell, that is round
three.
