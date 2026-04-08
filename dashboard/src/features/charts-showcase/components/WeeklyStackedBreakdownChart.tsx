import { WeeklyDayBreakdown } from "../types";
import { getCategoryMeta } from "../utils/showcaseFormat";
import ShowcaseSection from "./ShowcaseSection";

interface WeeklyStackedBreakdownChartProps {
  days: WeeklyDayBreakdown[];
  maxHours?: number;
  goalHours: number;
}

const categoryOrder = [
  "productivity",
  "learning",
  "communication",
  "entertainment",
  "idle",
] as const;

function WeeklyStackedBreakdownChart({
  days,
  maxHours = 12,
  goalHours,
}: WeeklyStackedBreakdownChartProps) {
  const gridLabels = Array.from({ length: maxHours / 2 + 1 }, (_, index) => index * 2);

  return (
    <ShowcaseSection title="Daily Breakdown" delayMs={120} className="mb-0">
      <div className="relative pl-10">
        <div className="relative mb-2 flex h-[280px] items-end border-b border-[var(--ds-rule)]">
          {gridLabels.map((label) => {
            const bottom = (label / maxHours) * 100;

            return (
              <div key={label}>
                <div
                  className="absolute left-0 right-0 border-t border-dashed border-[var(--ds-rule)]"
                  style={{ bottom: `${bottom}%` }}
                />
                <div
                  className="absolute left-[-36px] -translate-y-1/2 font-mono text-[10px] text-[var(--ds-text-muted)]"
                  style={{ bottom: `${bottom}%` }}
                >
                  {label}h
                </div>
              </div>
            );
          })}

          <div
            className="absolute left-0 right-0 z-[2] border-t-2 border-dashed border-[var(--ds-accent-deep)]"
            style={{ bottom: `${(goalHours / maxHours) * 100}%` }}
          >
            <span className="absolute right-[-4px] top-[-18px] font-mono text-[9px] font-semibold uppercase tracking-[0.06em] text-[var(--ds-accent-deep)]">
              Goal {goalHours}h
            </span>
          </div>

          {days.map((day) => (
            <div
              className="relative z-[1] flex flex-1 flex-col items-center justify-end"
              key={day.day}
            >
              <div className="flex w-9 flex-col-reverse overflow-hidden rounded-t-[1px]">
                {categoryOrder.map((category) => (
                  <div
                    className="w-full transition-[height] duration-[400ms] ease-out"
                    key={`${day.day}-${category}`}
                    style={{
                      height: `${(day.values[category] / maxHours) * 280}px`,
                      background: getCategoryMeta(category).color,
                    }}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mb-12 flex">
          {days.map((day) => (
            <div
              className={`flex-1 pt-[10px] text-center font-mono text-[11px] ${
                day.isToday ? "font-semibold text-[var(--ds-accent)]" : "text-[var(--ds-text-muted)]"
              }`}
              key={`${day.day}-label`}
            >
              {day.day}
              <span className="mt-[2px] block text-[10px]">
                {Math.floor(day.total)}h
                {Math.round((day.total - Math.floor(day.total)) * 60) > 0
                  ? `${Math.round((day.total - Math.floor(day.total)) * 60)}m`
                  : ""}
              </span>
            </div>
          ))}
        </div>
      </div>
    </ShowcaseSection>
  );
}

export default WeeklyStackedBreakdownChart;
