# Pursuits Setup UI Spec

Date: 2026-04-12  
Status: Approved design scope for hardcoded UI prototype

## 1. Goal
Build a **hardcoded frontend UI** where users can:
1. Create/edit pursuits.
2. Select activities (programs/domains) and assign them to pursuits.
3. Preview bulk assignment changes before applying.

This is a UI-only milestone. No backend wiring in this pass.

## 2. Route + Placement
- Add a new showcase route: `/showcase/pursuits-setup`.
- Keep implementation inside the existing showcase system for fast iteration.
- Add nav entry in showcase view navigation.

## 3. Scope
In scope:
- Candidate-first assignment workflow.
- Mixed-type multi-select (`program` + `domain`) in one assignment action.
- Pursuit creation and editing UI.
- Assignment panel with existing pursuit picker + inline create form.
- Strict single-membership handling in the UI.

Out of scope:
- Real API calls and persistence.
- `video_channel` candidate type (deferred).
- Full production validation/error handling contract.

## 4. Core Workflow
Primary model: **candidate-first**.

1. User reviews candidate list (default: unassigned only).
2. User selects one or more candidates (mixed types allowed).
3. User assigns selection to either:
   - an existing pursuit, or
   - a newly created pursuit (inline in side panel).
4. User sees a preview of changes:
   - items to add,
   - items to move (`from -> to`).
5. User confirms apply.

## 5. Page Structure
Two-column layout:

- Left: **Candidate Table**
- Right: **Assignment + Pursuit Editor Panel** (persistent)

### 5.1 Candidate Table (left)
Required columns:
- `checkbox`
- `display name`
- `type` chip (`program` or `domain`)
- `last 30d time`
- `current pursuit` (`Unassigned` if none)

Controls:
- Search input (filters by display name, both types).
- `Show assigned` toggle (default: off).
- Optional sort defaults to `last 30d time desc`.

Behavior:
- Default view emphasizes unassigned high-time items.
- Assigned rows are visible when toggle is on.

### 5.2 Side Panel (right)
Sections:
1. `Selected items` summary (count + list).
2. `Assign to existing pursuit` selector.
3. `Create new pursuit` inline form (name/category/color/optional weekly goal field for UI completeness).
4. `Preview changes` (adds + moves).
5. `Apply` action.

Why persistent panel:
- Better for monthly bulk triage than repeated modal opening/closing.

## 6. Single-Membership Rules (UI behavior)
Strict one-member-to-one-pursuit behavior is enforced in prototype UX.

- Each candidate shows current owner pursuit.
- If selected items include already-assigned members and target pursuit differs:
  - treat as a move,
  - require explicit confirmation in preview/apply step.
- No silent overwrite.

## 7. Data Window
Candidate data in this prototype is framed as:
- **Last 30 days**

UI should display this explicitly near table header (for future `/api/pursuits/untagged` parity).

## 8. Data Model for Hardcoded Mock
Use local mock arrays in showcase feature. Suggested shape:

```ts
interface PursuitCandidateRow {
  sourceType: "program" | "domain";
  identifier: string;
  displayName: string;
  last30dSeconds: number;
  currentPursuitId: string | null;
}

interface PursuitDefinition {
  pursuitId: string;
  name: string;
  category: "productivity" | "learning" | "communication" | "entertainment";
  color: string;
  weeklyGoalSeconds: number | null;
}
```

## 9. Edit/Removal Handling in This Pass
- Pursuit **edit UI** is included (rename/category/color/goal controls).
- Member removal from pursuit can be represented as an unassign action from selected rows.
- Deep management workflows (dedicated pursuit detail page, audit/history) are deferred.

## 10. Copy + Naming
Use `Pursuit` terminology consistently.

Examples:
- Page title: `Pursuit Setup`
- Table subtitle: `Top unassigned apps and websites in the last 30 days`
- Preview labels: `Moves requiring confirmation`

## 11. Acceptance Criteria (UI Prototype)
1. Route `/showcase/pursuits-setup` renders without backend dependency.
2. Candidate list supports mixed-type multi-select.
3. Search filters candidates by name.
4. `Show assigned` toggle defaults off and reveals assigned rows when enabled.
5. Side panel stays visible while selecting rows.
6. User can choose existing pursuit or create new pursuit inline.
7. Preview area differentiates `add` vs `move` items.
8. Move actions require explicit confirmation before apply.
9. All content uses hardcoded values and local state only.

## 12. Deferred Follow-ups
- Add `video_channel` as third source type.
- Wire to planned endpoints:
  - `GET /api/pursuits`
  - `POST/PATCH/DELETE /api/pursuits`
  - `POST/DELETE pursuit members`
  - `GET /api/pursuits/untagged`
- Add robust empty/error/loading states for live data.
