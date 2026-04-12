# Pursuit creation backend

**Date:** 2026-04-12
**Status:** Ready for /developer
**Components touched:** activitytracker

## Problem

The dashboard redesign requires user-defined Pursuits (PRODUCT.md, ADR-003) to
attribute tracked time into Categories. No Pursuit table, service, or endpoint
exists today. A parallel frontend effort is building the Pursuit-creation UI
against hardcoded data and needs a real backend to dogfood tagging. This spec
covers just enough backend to let a user create a Pursuit, attach members to
it, and have those memberships retrievable by a lookup the Arbiter will later
consume. The actual writing of Activities into Pursuits is deliberately out of
scope — that's a follow-up.

## Goals

- User can create a Pursuit via `POST /api/pursuits` with name, category, color, optional weekly goal.
- User can attach a previously-observed program / domain / video channel to a Pursuit via `POST /api/pursuits/{pursuitId}/members`.
- User can list (`GET /api/pursuits`), update (`PATCH`), delete (`DELETE`), and remove members (`DELETE /members/...`) — if the surface falls out easily. Create + add-member are the required wins.
- Pursuit membership is queryable by `(source_type, identifier)` via an in-memory service, ready for the Arbiter to call later.
- Historical record of "which identifier belonged to which Pursuit and when" survives deletes and reassignments.

## Non-goals

- No Arbiter integration. The Arbiter is not modified. The membership service exists but nothing calls its lookup yet.
- No writing of Activities (program/domain/video sessions) into a Pursuit-attributed table.
- No Uncategorized sentinel row. Uncategorized is the absence of a membership.
- No `/api/pursuits/untagged` endpoint.
- No multi-user or auth scoping — matches current project state.
- No identifier normalization (lowercase, strip `www.`). Identifiers are stored verbatim as they appear in the authoritative summary table.
- No real color palette enforcement — stubbed validator only.
- No dashboard endpoints (`/api/daily/*`, `/api/weekly/*`). Those are separate specs.

## User story (happy path)

1. User has been running DeskSense for a few days. `vscode.exe` and `github.com` appear in `DailyProgramSummary` / `DailyDomainSummary`.
2. User (via the frontend) sends `POST /api/pursuits` with `{ "name": "Freelance Copywriting", "category": "productivity", "color": "#4f7cff", "weeklyGoalSeconds": 72000 }`. Server returns `201` with `{ "pursuitId": 1, ... }`.
3. User sends `POST /api/pursuits/1/members` with `{ "sourceType": "program", "identifier": "vscode.exe" }`. Server validates the identifier exists in `DailyProgramSummary.exe_path_as_id`, confirms no other Pursuit owns it, inserts, and returns `201`.
4. User repeats for `{ "sourceType": "domain", "identifier": "github.com" }`.
5. Internally, the `PursuitMembershipService` cache is invalidated so a subsequent `get_pursuit_id_for("program", "vscode.exe")` returns `1`.

## Behavior spec

### `POST /api/pursuits`
- Request body: `{ name, category, color, weeklyGoalSeconds? }`.
- `name`: required, string, trimmed, length ≤ 50, globally unique (case-insensitive). Empty / whitespace-only → `400`. Duplicate → `409` with body `{ "error": "name_taken" }`.
- `category`: required, must be one of `"productivity" | "learning" | "entertainment" | "communication"`. Anything else → `400`.
- `color`: required, string. Must pass `validate_color(color)` (stub returns `True` for v1). Invalid → `400`.
- `weeklyGoalSeconds`: optional; if present must be `int`, `0 ≤ n ≤ 7*24*3600` (604800). Out of range → `400`.
- On success: `201`, response `{ "pursuitId": <int>, "name", "category", "color", "weeklyGoalSeconds": <int|null>, "members": [] }`.
- `pursuitId` is the integer primary key, returned as JSON number. No slug.

### `POST /api/pursuits/{pursuitId}/members`
- Path param `pursuitId`: integer. Unknown → `404`.
- Request body: `{ sourceType, identifier }`.
- `sourceType`: required, one of `"program" | "domain" | "video_channel"`. Otherwise `400`.
- `identifier`: required, non-empty string. Stored verbatim.
- **Existence check:** the identifier MUST appear in the authoritative summary table for its sourceType:
  - `program` → at least one row in `DailyProgramSummary` where `exe_path_as_id == identifier`.
  - `domain` → at least one row in `DailyDomainSummary` where `domain_name == identifier`.
  - `video_channel` → at least one row in `DailyVideoSummary` where `channel_name == identifier` (YouTube only; null channel_name rows are skipped).
  - If no match: `404` with body `{ "error": "identifier_not_observed" }`.
- **Conflict check:** if a row already exists in `pursuit_members` with the same `(source_type, identifier)`, return `409` with body `{ "error": "member_taken", "pursuitId": <owner_id>, "pursuitName": <owner_name> }`. Applies even if the owning Pursuit is the one being targeted (idempotency is not required; duplicate add is a conflict).
- On success: `201`, response `{ "pursuitId", "sourceType", "identifier" }`. Insert row in `pursuit_members`, append `{action: "added"}` row to `pursuit_membership_history`, invalidate the membership cache.

### Adjacent endpoints (implement if trivial, skip if they balloon scope)
- `GET /api/pursuits` → list all, each with its `members` array. Shape per `spec/endpoints.md`.
- `PATCH /api/pursuits/{pursuitId}` → update `name` / `category` / `color` / `weeklyGoalSeconds`. Same validation rules as POST. `weeklyGoalSeconds: null` clears the goal. Unknown id → `404`.
- `DELETE /api/pursuits/{pursuitId}` → deletes the Pursuit; cascades to `pursuit_members`; each removed member gets a `{action: "removed"}` row in `pursuit_membership_history`; cache invalidated. `204` on success.
- `DELETE /api/pursuits/{pursuitId}/members/{sourceType}/{identifier}` → removes one member, logs `{action: "removed"}` to history, invalidates cache. `204`.
- If any of these surfaces more than ~30 lines of extra code each, skip it and add to Out-of-scope follow-ups instead.

### General
- All endpoints respond with JSON. Error bodies use shape `{ "error": "<snake_case_code>", ...optional fields }`.
- No pagination (volume is tiny — a user will have tens of Pursuits at most).

## Architecture & constraints

- **Route file:** new `activitytracker/src/activitytracker/routes/pursuit_routes.py`, `prefix="/pursuits"`, mounted in `server.py` under the `/api` prefix alongside existing routers.
- **Service:** new `activitytracker/src/activitytracker/services/pursuit_service.py`. Owns all validation, DB writes, cache invalidation. Routes call the service; routes do not touch DAOs directly.
- **DAO:** new `activitytracker/src/activitytracker/db/dao/direct/pursuit_dao.py`. Direct (sync) DAO — Pursuit CRUD is low-volume and user-initiated, not in the hot path. Do not use the queuing DAO pattern.
- **Cache / lookup service:** new `activitytracker/src/activitytracker/services/pursuit_membership_service.py`, singleton (same pattern as `_chrome_service_instance` in `service_dependencies.py`). Interface:
  ```python
  class PursuitMembershipService:
      def get_pursuit_id_for(source_type: str, identifier: str) -> int | None
      def invalidate() -> None   # blunt full reload from DB
  ```
  - Loads all `(source_type, identifier) -> pursuit_id` pairs from `pursuit_members` into an in-memory dict on first use.
  - `PursuitService` calls `invalidate()` after every mutating operation.
  - Thread-safety: reads must be safe from the Arbiter's thread and the FastAPI request threads. A simple `threading.Lock` around the dict swap is sufficient.
- **Color validator:** new `activitytracker/src/activitytracker/util/color_validator.py` exporting `validate_color(hex: str) -> bool`. v1 returns `True` unless the string is empty. Add `# TODO: real palette check` comment.
- **Wiring:** add `get_pursuit_service`, `get_pursuit_dao`, `get_pursuit_membership_service` factories in `service_dependencies.py` following existing patterns.
- **Boundary rules (hard):**
  - Internal integer `pursuit_id` is the only id form — it is used directly in JSON responses. No slug derivation. No UUID. (The `p_copywriting`-style ids in `spec/endpoints.md` were aspirational and are superseded here.)
  - The Arbiter code is not modified in this spec. Integration is a follow-up.
  - Routes do not import DAOs; only services do.
  - `PursuitMembershipService` is the sole read path for membership lookups from anywhere outside the Pursuit service itself. Other services must not query `pursuit_members` directly.
  - Uncategorized is NOT a row. Do not insert a sentinel. Absence of a membership is the definition.
  - Identifiers are stored verbatim. No `.lower()`, no `strip("www.")`. Normalization is a separate concern flagged in `spec/endpoints.md` open questions.

## Data & contracts

### New tables (add to `db/models.py`, new Alembic migration)

**`pursuits`**
- `id`: Integer, PK.
- `name`: String(50), not null, unique (case-insensitive — implement via a functional unique index on `lower(name)` or a citext column; pick whichever is simpler with current Postgres setup).
- `category`: String, not null. Stored as string; validated at service layer against the fixed set. (Using a plain String keeps future category additions cheap; using SQLAlchemy Enum is fine too — developer's call, pick one and be consistent.)
- `color`: String, not null.
- `weekly_goal_seconds`: Integer, nullable.
- `created_at`: DateTime(timezone=True), not null, server default `now()`.
- `updated_at`: DateTime(timezone=True), not null, server default `now()`, update trigger or service-side bump on PATCH.

**`pursuit_members`** (live membership — one row per active attachment)
- `id`: Integer, PK.
- `pursuit_id`: Integer, FK → `pursuits.id`, ON DELETE CASCADE.
- `source_type`: String, not null.
- `identifier`: String, not null.
- `created_at`: DateTime(timezone=True), not null, server default `now()`.
- **Unique constraint** on `(source_type, identifier)` — enforces ADR-003's "one member → one Pursuit" at the DB level.
- Index on `pursuit_id`.

**`pursuit_membership_history`** (append-only audit log)
- `id`: Integer, PK.
- `pursuit_id`: Integer, not null. NOT a FK — history must outlive the Pursuit. Store the id as a bare integer.
- `pursuit_name_snapshot`: String, not null. Snapshot of the Pursuit's name at the time of the event, so the history remains readable after deletes/renames.
- `source_type`: String, not null.
- `identifier`: String, not null.
- `action`: String, not null. Values: `"added"` | `"removed"`.
- `occurred_at`: DateTime(timezone=True), not null, server default `now()`.
- Index on `(source_type, identifier)` for future "who has owned this identifier?" queries.

### API contracts

Covered in the Behavior spec above. Routes live under `/api/pursuits`.

### Cross-component messages

None. This is backend-only.

## Invariants to preserve

- **Backend owns timing logic / Activity Arbiter is sole authority.** This spec does not touch Activity writing — it only provides the data structures and a read-side service the Arbiter will later consult. The Arbiter remains the only authority on what gets logged.
- **Backend owns user auth / no data sync across machines.** No user scoping introduced; Pursuits are global on the single machine, matching current project state.
- **High-resolution user activity data never leaves the server.** Pursuit endpoints return only aggregate / configuration data (name, category, color, goal, member identifiers that already appear in summary tables). Nothing new is exposed.

## Test plan

All Python tests run via `win-pytest`. Agents can run these; direct `pytest` fails under WSL.

### Failing tests to write first

Create `activitytracker/tests/routes/test_pursuit_routes.py` and `activitytracker/tests/services/test_pursuit_service.py`. Per the project's "write failing test first" rule, each test below should fail on a fresh checkout before implementation lands.

- `test_create_pursuit_returns_201_and_id` — happy path POST.
- `test_create_pursuit_rejects_invalid_category` — 400.
- `test_create_pursuit_rejects_duplicate_name_case_insensitive` — 409 `name_taken`.
- `test_create_pursuit_rejects_name_over_50_chars` — 400.
- `test_create_pursuit_rejects_negative_weekly_goal` — 400.
- `test_create_pursuit_rejects_weekly_goal_over_one_week` — 400.
- `test_add_member_happy_path` — 201, row exists in `pursuit_members`, history row inserted with `action="added"`.
- `test_add_member_unseen_identifier_returns_404` — identifier absent from summary tables.
- `test_add_member_already_claimed_returns_409_with_owner_info` — response body includes `pursuitId` and `pursuitName` of the conflicting owner.
- `test_add_member_invalidates_membership_cache` — after add, `PursuitMembershipService.get_pursuit_id_for(...)` returns the new pursuit id. This is the one that proves the whole feature is wired end to end.

### Membership service unit tests

Create `activitytracker/tests/services/test_pursuit_membership_service.py`:
- `test_get_pursuit_id_for_returns_none_when_unknown`.
- `test_get_pursuit_id_for_returns_pursuit_id_after_invalidate`.
- `test_concurrent_invalidate_does_not_deadlock` — sanity on the lock.

### Integration / e2e

One integration test exercising the full flow against a test DB fixture:
`activitytracker/tests/integration/test_pursuit_flow.py` — create pursuit, seed a `DailyProgramSummary` row, add program member, assert cache returns id, DELETE pursuit, assert cache returns None, assert history has `added` + `removed` rows.

### Not testable by the agent

- The frontend UI that consumes these endpoints — out of scope; /qa will cover.

## Open questions / developer-agent latitude

- **Case-insensitive name uniqueness implementation:** functional unique index on `lower(name)` vs `citext` column. Pick whichever is less setup in current Alembic + Postgres config. Either is acceptable.
- **Category column type:** SQLAlchemy Enum vs plain String. Pick one, apply consistently. Both are fine.
- **PATCH updated_at mechanism:** DB trigger vs service-side bump. Service-side is simpler and the codebase does not yet use triggers. Prefer service-side.
- **Adjacent endpoints (`GET /api/pursuits`, PATCH, DELETE, DELETE member):** implement if each adds <30 lines of route+service+test. Otherwise move to Out-of-scope follow-ups and note what was skipped.

## Out-of-scope follow-ups

- Arbiter integration: call `PursuitMembershipService.get_pursuit_id_for(...)` when closing ProgramSession / ChromeSession / VideoSession and persist the attribution.
- Uncategorized handling as a first-class UI/query concept (vs. current "absence of row" semantics).
- Real palette-aware color validation.
- Identifier normalization policy (ties into `spec/endpoints.md` open questions).
- `GET /api/pursuits/untagged` for the bulk-tagging flow.
- Multi-user / user scoping.
