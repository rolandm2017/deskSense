import { ProjectGoal } from "../types";
import ShowcaseSection from "./ShowcaseSection";

interface DailyProjectsListProps {
  projects: ProjectGoal[];
}

function DailyProjectsList({ projects }: DailyProjectsListProps) {
  return (
    <ShowcaseSection title="Projects - Today" delayMs={300}>
      <div className="flex flex-col">
        {projects.map((project, index) => {
          const pct = Math.min((project.hours / project.goal) * 100, 150);
          const wholeHours = Math.floor(project.hours);
          const minutes = Math.round((project.hours - wholeHours) * 60);

          return (
            <div
              className={`grid grid-cols-[minmax(0,1fr)_80px_100px] items-center gap-4 border-b border-[var(--ds-rule)] py-[14px] ${
                index === 0 ? "border-t" : ""
              }`}
              key={project.name}
            >
              <div className="text-[13px] text-[var(--ds-text)]">{project.name}</div>
              <div className="text-right font-mono text-[13px] font-medium text-[var(--ds-text)]">
                {wholeHours}h {minutes}m
              </div>
              <div className="relative h-1 overflow-visible rounded-[1px] bg-[var(--ds-surface-2)]">
                <div
                  className="absolute left-0 top-0 h-full rounded-[1px]"
                  style={{
                    width: `${Math.min(pct, 100)}%`,
                    background: project.color,
                  }}
                />
                {pct > 100 ? (
                  <div
                    className="absolute left-0 top-0 h-full rounded-[1px] opacity-40"
                    style={{ width: `${pct}%`, background: project.color }}
                  />
                ) : null}
                <div className="absolute left-full top-[-3px] h-[10px] w-px bg-[var(--ds-text-muted)]" />
              </div>
            </div>
          );
        })}
      </div>
    </ShowcaseSection>
  );
}

export default DailyProjectsList;
