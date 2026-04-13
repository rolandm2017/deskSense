# DeskSense

DeskSense is a privacy-focused desktop time tracker for self-management.
Runs on one machine. No data leaves the computer except auth/license info.

## Who it's for

Target users are broad but bounded by intent: people who want to audit
and self-manage their own time, not bill anyone else for it.

- Students tracking study habits.
- Knowledge workers auditing distraction.
- Someone self-managing during deep-work.
- A learner checking whether they've done "enough" this week.
- Language learners tracking their language immersion.

The originating use case: the author wanting to know "how much time am I
wasting vs. using well?" and to replace manual tracking of second-language
immersion.

The developer is also a language learner himself, part of the final category.

**Not for:** freelancer invoicing or client billing. That's Toggl's lane.
Features like per-client rates, exportable invoices, and rounding-to-
billable-increment are explicitly out of scope. Framing is "did I really
waste all that time today?" or "I did 30 hours this week, go me" — not
external reporting.

## Core vocabulary

- **Activity** — a single fine-grained recording of use: one foreground
  session of a program, a domain visit, a video watch. Produced by the
  arbiter and the Chrome extension.
- **Summary** — a rollup of Activities over a period, per program / domain /
  video. `DailyProgramSummary`, `DailyDomainSummary`, `DailyVideoSummary`.
- **Pursuit** — a deliberately open-ended, user-defined grouping of
  Activities tracked under one umbrella, so the app can tell when the user
  is doing a certain behavior. Examples: "Language Learning", "Accounting",
  "Entertainment", "Freelance Copywriting". A Pursuit has members
  (programs, domains, or video channels), exactly one Category, a color,
  and an optional weekly goal. Program, domain, and video Activities all
  feed into Pursuits.
- **Category** — one of a fixed set: productivity, learning, entertainment,
  communication. Assigned per-Pursuit, not per-Activity.
- **Uncategorized** — system-owned implicit Pursuit covering any tracked
  time not yet attributed to a user-defined Pursuit. Not counted toward
  any Category. Shrinks as the user tags more apps. Means "at the
  machine, but this app isn't in a Pursuit yet."
- **Idle** — time the system believes the user is AFK or on their phone.
  Detected via absence of keyboard/mouse activity. Distinct from
  Uncategorized: Idle means "not at the machine," Uncategorized means
  "at the machine, but untagged."

See `docs/product-decision-log.md` for the ADRs that shaped these.

## Platform and privacy stance

- Desktop/laptop only. Will never run on a phone.
- Internet is used only to verify subscription/license. All tracking and
  storage is local.
- High-resolution user activity data never leaves the server.
- Day boundary is 4:00am local to the user's machine. The client sends
  its timezone (browser → backend) so a user who travels with their
  laptop still gets correct day buckets.
- Week boundary is Monday 4:00am, ISO-style.

## Future goals (not yet implemented)

- Tauri desktop wrapper.
- User auth, user scoping, and license gating — currently absent. See
  `spec/todo.md`.
- Dashboard depth beyond daily/weekly views.
- Optional spreadsheet export for personal archival.

## Performance expectation

- Dashboard interactions should feel instant. Target under ~300ms load
  where feasible. Exact per-endpoint budgets and measurement method are
  still being defined.

## Documentation precedence

- `PRODUCT.md` is authoritative for product intent and vocabulary.
- `AGENTS.md` is next for architecture and implementation guidance.
- `CLAUDE.md` is tool-specific guidance for Claude workflows.
