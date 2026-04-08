import { ScoreboardRow } from "../types";
import ShowcaseSection from "./ShowcaseSection";

interface ProjectScoreboardProps {
  rows: ScoreboardRow[];
}

function ProjectScoreboard({ rows }: ProjectScoreboardProps) {
  return (
    <ShowcaseSection title="Project Scoreboard" delayMs={300}>
      <div className="border-t border-[var(--ds-rule)]">
        <div className="grid grid-cols-[minmax(0,1fr)_80px_80px_120px_60px] items-center gap-3 border-b border-[var(--ds-rule)] py-[14px]">
          <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            Project
          </div>
          <div className="text-right font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            Actual
          </div>
          <div className="text-right font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            Goal
          </div>
          <div className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            Progress
          </div>
          <div className="text-right font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            Δ vs prev
          </div>
        </div>

        {rows.map((row) => {
          const pct = Math.min((row.actual / row.goal) * 100, 100);
          const fillColor =
            row.actual >= row.goal
              ? "#C7F36B"
              : row.actual >= row.goal * 0.8
                ? "#F28A2E"
                : "#E9687A";

          const deltaClass =
            row.delta > 0
              ? "text-[var(--ds-accent)]"
              : row.delta < 0
                ? "text-[var(--ds-communication)]"
                : "text-[var(--ds-text-muted)]";

          return (
            <div
              className="grid grid-cols-[minmax(0,1fr)_80px_80px_120px_60px] items-center gap-3 border-b border-[var(--ds-rule)] py-[14px]"
              key={row.name}
            >
              <div className="text-[13px] text-[var(--ds-text)]">{row.name}</div>
              <div className="text-right font-mono text-[13px] font-medium text-[var(--ds-text)]">
                {row.actual.toFixed(1)}h
              </div>
              <div className="text-right font-mono text-[13px] text-[var(--ds-text-muted)]">
                {row.goal}h
              </div>
              <div className="relative h-1 overflow-visible rounded-[1px] bg-[var(--ds-surface-2)]">
                <div
                  className="absolute left-0 top-0 h-full rounded-[1px]"
                  style={{ width: `${pct}%`, background: fillColor }}
                />
                <div className="absolute left-full top-[-3px] h-[10px] w-px bg-[var(--ds-text-muted)]" />
              </div>
              <div className={`text-right font-mono text-[11px] font-medium ${deltaClass}`}>
                {row.delta > 0 ? "+" : ""}
                {row.delta !== 0 ? `${row.delta.toFixed(1)}h` : "—"}
              </div>
            </div>
          );
        })}
      </div>
    </ShowcaseSection>
  );
}

export default ProjectScoreboard;
