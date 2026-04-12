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

  What I'd Recommend

  Strategy: Split the pipeline into testable units with clear contracts, then have a thin integration test
  that only asserts on the final output.

  Concretely:

  1. Make the StateMachine purely functional

  Right now set_new_session mutates current_state and prior_state in place, and you retrieve the result with
   a separate get_concluded_session() call. Instead, set_new_session should return the concluded session
  directly. This makes it trivially unit-testable: input session -> output completed session, no spies
  needed.

  2. Extract the "what to notify" logic from ActivityArbiter

  transition_state is doing: sleep detection, UI notification, state machine transition, engine lifecycle
  management, and DAO notification. The engine lifecycle and notification decisions can be separated so that
   transition_state produces a description of what happened (e.g., "concluded session X, started session
  Y"), and a separate step acts on it. The "what happened" part is unit-testable.

  3. Give ActivityRecorder observable output

  Instead of only writing to DAOs (which you then have to spy on), the recorder could maintain a structured
  event log — which you're already partially doing with pulse_history and remainder_history when DEBUG=True.
   Lean into this: make the recorder's test-mode output be the thing you assert on, rather than spying on 8
  different DAO methods.

  4. Integration test becomes: events in -> DB state out

  One integration test pumps events through the whole pipeline and asserts only on the final database state:
   "after these 4 program events and 4 chrome events, the summary table should have these rows with these
  durations." No spies, no call counts, no intermediate assertions. If it fails, you look at the unit tests
  to find where.

  5. The MockEngineContainer can go away

  The real ThreadedEngineContainer with a zero-sleep function and your controlled session durations should
  work fine if the Arbiter is simplified. The mock exists because you need to control timing precisely — but
   if the timing math is tested in unit tests on the KeepAliveEngine directly (input: 23 iterations ->
  output: 2 pulses + 3 partial), the integration test doesn't need to verify it again.

  ---
  The TLDR: your tests are long because the code doesn't have clean seams. Adding seams (return values
  instead of mutations, observable output instead of spies) would let you write focused unit tests per
  component and reduce the integration tests to simple input/output checks.

  Want me to ask you some clarifying questions before we dive into implementation, or does this direction
  resonate and you want to start somewhere specific?

✻ Brewed for 1m 32s

❯ I would like you to describe more of what you mean by "the code doesn't have clean seams," though I kind
  of get it. Could you also include some examples of what the new code would look like? You can just say,
  "After refactor example n," and trust that I recognize what the before state is. I remember the
  architecture of the program generally.

● "Clean seams" explained

  A seam is a place where you can observe or intercept behavior without modifying the code around it. A
  clean seam means: one side produces a value, the other side consumes it, and you can test either side
  independently by substituting the other.

  Your pipeline right now has fused seams — places where two components interact through mutation, side
  effects, or implicit ordering rather than through explicit inputs and outputs. To test one side, you have
  to boot the other side too, which is why your tests need the full pipeline running.

  Here are the specific fused seams and what they'd look like unfused:

  ---
  Seam 1: StateMachine.set_new_session → get_concluded_session

  Right now this is a two-step dance. The caller must call set_new_session, then separately call
  get_concluded_session and know that the result lives in self.prior_state.session. The mutation of
  state.session from a ProgramSession to a CompletedProgramSession happens inside _conclude_session via
  state.session = completed. This is invisible from outside — you can't tell what happened without spying.

  After refactor 1:

  class StateMachine:
      def set_new_session(
          self, next_session: ProgramSession | ChromeSession
      ) -> CompletedProgramSession | CompletedChromeSession | None:
          next_session = snapshot_obj_for_tests(next_session)

          if self.current_state is None:
              self.current_state = InternalState(None, None, next_session)
              return None  # initialization, nothing concluded

          concluded = self._conclude_session(
              self.current_state, next_session.start_time
          )
          self.current_state = InternalState(None, None, next_session)
          return concluded

      def _conclude_session(self, state, incoming_start) -> CompletedProgramSession | CompletedChromeSession
   | None:
          if self.is_initialization_session(state.session):
              return None
          duration = incoming_start.dt - state.session.start_time.dt
          if duration.total_seconds() < -60:
              raise SuspiciousDurationError("Negative duration")
          session_copy = snapshot_obj_for_tests(state.session)
          completed = session_copy.to_completed(incoming_start)
          completed.duration = duration
          return completed  # return it, don't stash it

  Now you can test the StateMachine alone:

  def test_state_machine_concludes_with_correct_duration():
      sm = StateMachine(mock_clock)
      sm.set_new_session(session_a)  # returns None (init)
      concluded = sm.set_new_session(session_b)
      assert concluded.start_time == session_a.start_time
      assert concluded.duration == timedelta(seconds=65)

  No spies. No Arbiter. No EngineContainer. Just input → output.

  ---
  Seam 2: ActivityArbiter.transition_state does too many things

  Right now transition_state is: detect sleep, notify UI, run state machine, stop old engine, create new
  engine, start new engine, notify recorder of new session, notify recorder of concluded session. You can't
  test any of those decisions without all the others running.

  After refactor 2:

  Split the decision from the execution:

  @dataclass
  class TransitionResult:
      """What happened during this transition — a testable value."""
      new_session: ProgramSession | ChromeSession
      concluded_session: CompletedProgramSession | CompletedChromeSession | None
      is_initialization: bool
      sleep_detected: bool
      flushed_at: UserLocalTime | None = None

  class ActivityArbiter:
      def transition_state(self, new_session):
          result = self._evaluate_transition(new_session)
          self._execute_transition(result)

      def _evaluate_transition(self, new_session) -> TransitionResult:
          """Pure-ish logic: what should happen? No side effects."""
          sleep_detected, time_before_gap = (
              self.sleep_detector.detect_awakening_from_sleep()
          )

          if sleep_detected:
              flushed = self.state_machine.conclude_without_replacement_at_time(
                  time_before_gap
              )
              # After flush, state_machine.current_state is None,
              # so the next set_new_session will be an init

          concluded = self.state_machine.set_new_session(new_session)
          is_init = concluded is None and not sleep_detected

          return TransitionResult(
              new_session=new_session,
              concluded_session=concluded,
              is_initialization=is_init,
              sleep_detected=sleep_detected,
              flushed_at=time_before_gap if sleep_detected else None,
          )

      def _execute_transition(self, result: TransitionResult):
          """Side effects: engine lifecycle, notifications."""
          self.notify_display_update(result.new_session)
          self.notify_of_new_session(result.new_session)

          if not result.is_initialization:
              self.current_pulse.stop()

          new_engine = self.engine_class(
              result.new_session, self.activity_recorder
          )

          if result.is_initialization:
              self.current_pulse.add_first_engine(new_engine)
          else:
              self.current_pulse.replace_engine(new_engine)

          self.current_pulse.start()

          if result.concluded_session is not None:
              self.notify_summary_dao(result.concluded_session)
          if result.flushed_at is not None:
              self.notify_summary_dao(result.concluded_session)

  Now you can test the decision logic without any engine or recorder:

  def test_second_session_concludes_first():
      arbiter = ActivityArbiter(clock, no_sleep_detector, dummy_container)
      result = arbiter._evaluate_transition(session_a)
      assert result.is_initialization is True
      assert result.concluded_session is None

      result = arbiter._evaluate_transition(session_b)
      assert result.is_initialization is False
      assert result.concluded_session.start_time == session_a.start_time

  And you can test the execution by passing a hand-crafted TransitionResult and checking that the right
  things happened — no state machine needed.

  ---
  Seam 3: KeepAliveEngine → ActivityRecorder callbacks

  The engine calls self.recorder.add_ten_sec_to_end_time(self.session) and
  self.recorder.add_partial_window(amount_used, self.session) directly. This is why your tests need spies on
   add_ten_sec_to_end_time and add_partial_window — the only way to observe the engine's behavior is to
  intercept these calls.

  After refactor 3:

  Make the engine produce a log of what it did, not execute it immediately:

  @dataclass
  class PulseEvent:
      session: ProgramSession | ChromeSession
      event_type: str  # "full_window" or "partial_window"
      amount: int      # 10 for full, 0-9 for partial

  class KeepAliveEngine:
      def __init__(self, session, recorder):
          self.session = session
          self.recorder = recorder
          self.amount_used = 0

      def iterate_loop(self):
          self.amount_used += 1
          if self.amount_used >= self.max_interval:
              self.recorder.add_ten_sec_to_end_time(self.session)
              self.amount_used = 0

      def conclude(self):
          self.recorder.add_partial_window(self.amount_used, self.session)

      # The key addition: the engine's behavior is now inspectable
      # without spying, because we can test the math separately:
      @staticmethod
      def compute_pulses(duration_in_seconds, window_size=10):
          """Given a duration, how many full pulses and what remainder?"""
          full_pulses = duration_in_seconds // window_size
          remainder = duration_in_seconds % window_size
          return full_pulses, remainder

  The math is now a pure function you can test with a one-liner:

  def test_65_seconds_yields_6_pulses_and_5_remainder():
      assert KeepAliveEngine.compute_pulses(65) == (6, 5)

  And the integration concern — "does the engine actually call the recorder correctly?" — can be a single
  focused test with a mock recorder, not part of the 500-line end-to-end.

  ---
  Seam 4: ActivityRecorder decides AND persists

  on_new_session does branching logic (is it a video? is it a program? does it already exist today?) and
  then calls 2-3 different DAOs. Your tests spy on all those DAOs because that's the only way to see what
  decisions the recorder made.

  After refactor 4:

  Separate the routing decision from the persistence:

  class ActivityRecorder:
      def on_new_session(self, session):
          actions = self._plan_new_session(session)
          self._execute_actions(actions)

      def _plan_new_session(self, session) -> list[RecorderAction]:
          """Decide what to do. Testable without any DAO."""
          actions = []
          if session.video_info:
              actions.append(StartVideoLog(session))
              if not self._video_exists_today(session):
                  actions.append(StartVideoSummary(session))
          if isinstance(session, ProgramSession):
              actions.append(StartProgramLog(session))
              if not self._program_exists_today(session):
                  actions.append(StartProgramSummary(session))
          elif isinstance(session, ChromeSession):
              actions.append(StartChromeLog(session))
              if not self._domain_exists_today(session):
                  actions.append(StartChromeSummary(session))
          return actions

  Now you can test "for a fresh ProgramSession, what actions should happen?" without any DAO at all — just
  check the returned list. And the "do the DAOs actually work?" question is a separate, DAO-level
  integration test.

  ---
  Tying it together: what your integration test becomes

  After these refactors, the big integration test shrinks to something like:

  async def test_four_program_sessions_produce_correct_db_state(
      fake_daos, test_events
  ):
      """Events in → DB state out. That's it."""
      arbiter = build_arbiter_with(fake_daos)

      for event in test_events:
          arbiter.set_program_state(event)

      summaries = fake_daos.program_summary.read_all()
      logs = fake_daos.program_logging.read_all()

      assert len(summaries) == 4
      assert len(logs) == 4
      assert summaries[0].hours_spent == pytest.approx(65 / 3600)
      assert logs[0].duration_in_sec == 65
      # ...and so on for the final output values you care about

  30 lines. No spies. If it breaks, you run the unit tests for StateMachine, KeepAliveEngine, and
  ActivityRecorder to find which component went wrong. The intermediate assertions exist in those unit
  tests, not in the integration test — which is exactly where they belong.