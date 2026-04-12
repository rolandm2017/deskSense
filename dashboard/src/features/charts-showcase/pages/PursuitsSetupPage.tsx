import { ChangeEvent, useMemo, useState } from "react";

import {
  mockPursuitCandidates,
  mockPursuits,
} from "../data/mockPursuitsSetupData";
import {
  PursuitCandidateRow,
  PursuitCategory,
  PursuitDefinition,
} from "../types";

const categoryOptions: { value: PursuitCategory; label: string }[] = [
  { value: "productivity", label: "Productivity" },
  { value: "learning", label: "Learning" },
  { value: "communication", label: "Communication" },
  { value: "entertainment", label: "Entertainment" },
];

const defaultNewPursuit = {
  name: "",
  category: "productivity" as PursuitCategory,
  color: "#C7F36B",
  weeklyGoalHours: "",
};

const categoryColors: Record<PursuitCategory, string> = {
  productivity: "#C7F36B",
  learning: "#7DD3C7",
  communication: "#E9687A",
  entertainment: "#F28A2E",
};

function formatDuration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);

  if (hours === 0) {
    return `${minutes}m`;
  }

  if (minutes === 0) {
    return `${hours}h`;
  }

  return `${hours}h ${minutes}m`;
}

function getWeeklyGoalHours(pursuit: PursuitDefinition) {
  if (pursuit.weeklyGoalSeconds === null) {
    return "";
  }

  return String(Math.round((pursuit.weeklyGoalSeconds / 3600) * 10) / 10);
}

function getPursuitName(pursuits: PursuitDefinition[], pursuitId: string | null) {
  if (pursuitId === null) {
    return "Unassigned";
  }

  return pursuits.find((pursuit) => pursuit.pursuitId === pursuitId)?.name ?? "Unknown";
}

function getPursuitColor(category: PursuitCategory) {
  return categoryColors[category];
}

function PursuitsSetupPage() {
  const [candidates, setCandidates] = useState(mockPursuitCandidates);
  const [pursuits, setPursuits] = useState(mockPursuits);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAssigned, setShowAssigned] = useState(false);
  const [targetPursuitId, setTargetPursuitId] = useState(mockPursuits[0]?.pursuitId ?? "");
  const [editPursuitId, setEditPursuitId] = useState(mockPursuits[0]?.pursuitId ?? "");
  const [moveConfirmed, setMoveConfirmed] = useState(false);
  const [newPursuit, setNewPursuit] = useState(defaultNewPursuit);

  const targetPursuit = pursuits.find((pursuit) => pursuit.pursuitId === targetPursuitId);
  const editPursuit = pursuits.find((pursuit) => pursuit.pursuitId === editPursuitId);

  const visibleCandidates = useMemo(() => {
    return candidates
      .filter((candidate) => showAssigned || candidate.currentPursuitId === null)
      .filter((candidate) =>
        candidate.displayName.toLowerCase().includes(searchTerm.toLowerCase()),
      )
      .sort((a, b) => b.last30dSeconds - a.last30dSeconds);
  }, [candidates, searchTerm, showAssigned]);

  const selectedCandidates = candidates.filter((candidate) =>
    selectedIds.includes(`${candidate.sourceType}:${candidate.identifier}`),
  );

  const adds = selectedCandidates.filter((candidate) => candidate.currentPursuitId === null);
  const assignedSelections = selectedCandidates.filter(
    (candidate) => candidate.currentPursuitId !== null,
  );
  const moves = selectedCandidates.filter(
    (candidate) =>
      candidate.currentPursuitId !== null && candidate.currentPursuitId !== targetPursuitId,
  );
  const applyDisabled =
    selectedCandidates.length === 0 || targetPursuit === undefined || (moves.length > 0 && !moveConfirmed);

  function toggleCandidate(candidate: PursuitCandidateRow) {
    const candidateId = `${candidate.sourceType}:${candidate.identifier}`;

    setSelectedIds((current) =>
      current.includes(candidateId)
        ? current.filter((selectedId) => selectedId !== candidateId)
        : [...current, candidateId],
    );
  }

  function handleTargetChange(event: ChangeEvent<HTMLSelectElement>) {
    setTargetPursuitId(event.target.value);
    setMoveConfirmed(false);
  }

  function handleCreatePursuit() {
    const trimmedName = newPursuit.name.trim();

    if (trimmedName.length === 0) {
      return;
    }

    const createdPursuit: PursuitDefinition = {
      pursuitId: `p_${trimmedName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_${pursuits.length + 1}`,
      name: trimmedName,
      category: newPursuit.category,
      color: newPursuit.color || getPursuitColor(newPursuit.category),
      weeklyGoalSeconds:
        newPursuit.weeklyGoalHours.trim().length === 0
          ? null
          : Math.round(Number(newPursuit.weeklyGoalHours) * 3600),
    };

    setPursuits((current) => [...current, createdPursuit]);
    setTargetPursuitId(createdPursuit.pursuitId);
    setEditPursuitId(createdPursuit.pursuitId);
    setNewPursuit(defaultNewPursuit);
  }

  function updateEditedPursuit(updates: Partial<PursuitDefinition>) {
    if (editPursuit === undefined) {
      return;
    }

    setPursuits((current) =>
      current.map((pursuit) =>
        pursuit.pursuitId === editPursuit.pursuitId ? { ...pursuit, ...updates } : pursuit,
      ),
    );
  }

  function handleApplyChanges() {
    if (applyDisabled || targetPursuit === undefined) {
      return;
    }

    setCandidates((current) =>
      current.map((candidate) =>
        selectedIds.includes(`${candidate.sourceType}:${candidate.identifier}`)
          ? { ...candidate, currentPursuitId: targetPursuit.pursuitId }
          : candidate,
      ),
    );
    setSelectedIds([]);
    setMoveConfirmed(false);
  }

  function handleUnassignSelected() {
    if (assignedSelections.length === 0) {
      return;
    }

    setCandidates((current) =>
      current.map((candidate) =>
        selectedIds.includes(`${candidate.sourceType}:${candidate.identifier}`)
          ? { ...candidate, currentPursuitId: null }
          : candidate,
      ),
    );
    setSelectedIds([]);
    setMoveConfirmed(false);
  }

  return (
    <div className="showcase-band-enter">
      <section className="mb-8 border-b border-[var(--ds-rule)] pb-6">
        <div className="font-display text-[42px] leading-none text-[var(--ds-text)]">
          Pursuit Setup
        </div>
        <p className="mt-3 max-w-[760px] text-[14px] leading-6 text-[var(--ds-text-muted)]">
          Top unassigned apps and websites in the last 30 days
        </p>
      </section>

      <div className="grid grid-cols-[minmax(0,1fr)_320px] gap-8">
        <section>
          <div className="mb-4 flex items-end justify-between gap-4">
            <label className="block min-w-[260px] text-[11px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
              Search candidates
              <input
                className="mt-2 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] normal-case tracking-normal text-[var(--ds-text)] outline-none"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>
            <label className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
              <input
                type="checkbox"
                checked={showAssigned}
                onChange={(event) => setShowAssigned(event.target.checked)}
              />
              Show assigned
            </label>
          </div>

          <table className="w-full border-collapse text-left">
            <thead className="border-y border-[var(--ds-rule)] font-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
              <tr>
                <th className="w-10 py-3" />
                <th className="py-3">Display name</th>
                <th className="py-3">Type</th>
                <th className="py-3 text-right">Last 30d time</th>
                <th className="py-3 text-right">Current pursuit</th>
              </tr>
            </thead>
            <tbody>
              {visibleCandidates.map((candidate) => {
                const candidateId = `${candidate.sourceType}:${candidate.identifier}`;

                return (
                  <tr key={candidateId} className="border-b border-[var(--ds-rule)]">
                    <td className="py-3">
                      <input
                        aria-label={`Select ${candidate.displayName}`}
                        type="checkbox"
                        checked={selectedIds.includes(candidateId)}
                        onChange={() => toggleCandidate(candidate)}
                      />
                    </td>
                    <td className="py-3 pr-3">
                      <div className="font-medium text-[var(--ds-text)]">{candidate.displayName}</div>
                      <div className="font-mono text-[10px] text-[var(--ds-text-muted)]">
                        {candidate.identifier}
                      </div>
                    </td>
                    <td className="py-3">
                      <span className="border border-[var(--ds-rule)] px-2 py-1 font-mono text-[10px] uppercase text-[var(--ds-text-muted)]">
                        {candidate.sourceType}
                      </span>
                    </td>
                    <td className="py-3 text-right font-mono text-[12px]">
                      {formatDuration(candidate.last30dSeconds)}
                    </td>
                    <td className="py-3 text-right text-[12px] text-[var(--ds-text-muted)]">
                      {getPursuitName(pursuits, candidate.currentPursuitId)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        <aside className="border-l border-[var(--ds-rule)] pl-6">
          <section className="showcase-rail-card border-t-0 pt-0">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
              Selected items
            </div>
            <div className="mt-3 font-display text-[28px] leading-none">{selectedCandidates.length} selected</div>
            <ul className="mt-4 space-y-2 text-[12px] text-[var(--ds-text-muted)]">
              {selectedCandidates.map((candidate) => (
                <li key={`${candidate.sourceType}:${candidate.identifier}`}>
                  {candidate.displayName} · {candidate.sourceType}
                </li>
              ))}
            </ul>
          </section>

          <section className="showcase-rail-card mt-6">
            <label className="block font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
              Assign to existing pursuit
              <select
                className="mt-3 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] normal-case tracking-normal text-[var(--ds-text)]"
                value={targetPursuitId}
                onChange={handleTargetChange}
              >
                {pursuits.map((pursuit) => (
                  <option key={pursuit.pursuitId} value={pursuit.pursuitId}>
                    {pursuit.name}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <section className="showcase-rail-card mt-6">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
              Create new pursuit
            </div>
            <div className="mt-3 space-y-3">
              <label className="block text-[12px] text-[var(--ds-text-muted)]">
                New pursuit name
                <input
                  className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                  value={newPursuit.name}
                  onChange={(event) => setNewPursuit({ ...newPursuit, name: event.target.value })}
                />
              </label>
              <label className="block text-[12px] text-[var(--ds-text-muted)]">
                New pursuit category
                <select
                  className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                  value={newPursuit.category}
                  onChange={(event) =>
                    setNewPursuit({
                      ...newPursuit,
                      category: event.target.value as PursuitCategory,
                      color: getPursuitColor(event.target.value as PursuitCategory),
                    })
                  }
                >
                  {categoryOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-[12px] text-[var(--ds-text-muted)]">
                New pursuit color
                <input
                  className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                  value={newPursuit.color}
                  onChange={(event) => setNewPursuit({ ...newPursuit, color: event.target.value })}
                />
              </label>
              <label className="block text-[12px] text-[var(--ds-text-muted)]">
                New pursuit weekly goal
                <input
                  className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                  inputMode="decimal"
                  value={newPursuit.weeklyGoalHours}
                  onChange={(event) =>
                    setNewPursuit({ ...newPursuit, weeklyGoalHours: event.target.value })
                  }
                />
              </label>
              <button
                className="w-full border border-[var(--ds-accent)] px-3 py-2 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--ds-accent)]"
                type="button"
                onClick={handleCreatePursuit}
              >
                Create pursuit
              </button>
            </div>
          </section>

          <section className="showcase-rail-card mt-6">
            <label className="block font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
              Pursuit to edit
              <select
                className="mt-3 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] normal-case tracking-normal text-[var(--ds-text)]"
                value={editPursuitId}
                onChange={(event) => setEditPursuitId(event.target.value)}
              >
                {pursuits.map((pursuit) => (
                  <option key={pursuit.pursuitId} value={pursuit.pursuitId}>
                    {pursuit.name}
                  </option>
                ))}
              </select>
            </label>
            {editPursuit !== undefined ? (
              <div className="mt-3 space-y-3">
                <label className="block text-[12px] text-[var(--ds-text-muted)]">
                  Edit pursuit name
                  <input
                    className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                    value={editPursuit.name}
                    onChange={(event) => updateEditedPursuit({ name: event.target.value })}
                  />
                </label>
                <label className="block text-[12px] text-[var(--ds-text-muted)]">
                  Edit pursuit category
                  <select
                    className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                    value={editPursuit.category}
                    onChange={(event) =>
                      updateEditedPursuit({
                        category: event.target.value as PursuitCategory,
                        color: getPursuitColor(event.target.value as PursuitCategory),
                      })
                    }
                  >
                    {categoryOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-[12px] text-[var(--ds-text-muted)]">
                  Edit pursuit color
                  <input
                    className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                    value={editPursuit.color}
                    onChange={(event) => updateEditedPursuit({ color: event.target.value })}
                  />
                </label>
                <label className="block text-[12px] text-[var(--ds-text-muted)]">
                  Edit pursuit weekly goal
                  <input
                    className="mt-1 w-full border border-[var(--ds-rule)] bg-[var(--ds-surface-2)] px-3 py-2 text-[13px] text-[var(--ds-text)]"
                    inputMode="decimal"
                    value={getWeeklyGoalHours(editPursuit)}
                    onChange={(event) =>
                      updateEditedPursuit({
                        weeklyGoalSeconds:
                          event.target.value.trim().length === 0
                            ? null
                            : Math.round(Number(event.target.value) * 3600),
                      })
                    }
                  />
                </label>
              </div>
            ) : null}
          </section>

          <section className="showcase-rail-card mt-6">
            <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
              Preview changes
            </div>
            <div className="mt-4 space-y-4 text-[12px]">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
                  Adds
                </div>
                <ul className="mt-2 space-y-1 text-[var(--ds-text-muted)]">
                  {adds.map((candidate) => (
                    <li key={`${candidate.sourceType}:${candidate.identifier}`}>
                      {candidate.displayName} -&gt; {targetPursuit?.name}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
                  Moves requiring confirmation
                </div>
                <ul className="mt-2 space-y-1 text-[var(--ds-text-muted)]">
                  {moves.map((candidate) => (
                    <li key={`${candidate.sourceType}:${candidate.identifier}`}>
                      {candidate.displayName}: {getPursuitName(pursuits, candidate.currentPursuitId)} -&gt;{" "}
                      {targetPursuit?.name}
                    </li>
                  ))}
                </ul>
              </div>
              {moves.length > 0 ? (
                <label className="flex items-start gap-2 text-[12px] text-[var(--ds-text-muted)]">
                  <input
                    type="checkbox"
                    checked={moveConfirmed}
                    onChange={(event) => setMoveConfirmed(event.target.checked)}
                  />
                  I understand selected assigned items will move pursuits
                </label>
              ) : null}
              <button
                className="w-full border border-[var(--ds-accent)] bg-[var(--ds-accent)] px-3 py-2 font-mono text-[11px] uppercase tracking-[0.08em] text-[#18191B] disabled:border-[var(--ds-rule)] disabled:bg-transparent disabled:text-[var(--ds-text-muted)]"
                type="button"
                disabled={applyDisabled}
                onClick={handleApplyChanges}
              >
                Apply changes
              </button>
              <button
                className="w-full border border-[var(--ds-rule)] px-3 py-2 font-mono text-[11px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)] disabled:opacity-50"
                type="button"
                disabled={assignedSelections.length === 0}
                onClick={handleUnassignSelected}
              >
                Unassign selected
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default PursuitsSetupPage;
