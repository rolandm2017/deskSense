# TODO — deferred decisions and unbuilt areas

The developer intends to make decisions about the following later. They
are currently unaddressed. Agents should not assume these exist.

## Major unbuilt areas

- **User auth.** No login exists. The backend will eventually own auth;
  single-machine scoping will still apply.
- **User scoping of endpoints.** Every dashboard endpoint currently
  assumes "the one user of this machine." Will need user_id scoping once
  auth lands.
- **License / payment gating.** The only reason the finished app touches
  the internet. Not yet built.

## Deferred design decisions

- **Error contracts for dashboard endpoints.** 4xx/5xx conventions,
  empty-state shape ("no data today yet"), and client behavior when the
  backend is unreachable. Chrome extension offline handling is also
  explicitly unfinished.
- **Performance budget for new `/api/daily/*` and `/api/weekly/*`
  endpoints.** No target set; current dashboard is known to be slow.
- **Category set extensibility.** Four Categories are hardcoded
  (ADR-003). Whether this ever opens up is TBD.
- **Pursuit color handling.** Free-form hex vs palette; server-side
  validation vs client-picked.
- **Tauri impact on endpoint shape.** If the dashboard becomes an
  embedded webview, some HTTP endpoints might become IPC. Revisit
  before Tauri work starts.
- **Identifier normalization and domain scoping.** Already flagged as
  open questions in `spec/endpoints.md`.
