import { TopProgramLane } from "../types";
import {
  formatClockHour,
  formatDecimalHours,
  getCategoryMeta,
  getHourTickLabels,
  getPositionPercent,
  SHOWCASE_DAY_END,
  SHOWCASE_DAY_START,
} from "../utils/showcaseFormat";
import ShowcaseSection from "./ShowcaseSection";

interface TopProgramsSwimLanesProps {
  lanes: TopProgramLane[];
}

function TopProgramsSwimLanes({ lanes }: TopProgramsSwimLanesProps) {
  const hourLabels = getHourTickLabels();

  return (
    <ShowcaseSection title="Top Programs" delayMs={180} className="mb-12">
      <div className="mb-[6px] flex items-center">
        <div className="w-[180px] shrink-0" />
        <div className="flex flex-1 justify-between">
          {hourLabels.map((label) => (
            <span
              className="w-10 text-center font-mono text-[10px] text-[var(--ds-text-muted)]"
              key={label}
            >
              {label}
            </span>
          ))}
        </div>
        <div className="w-14 shrink-0" />
      </div>

      <div className="flex flex-col gap-[6px]">
        {lanes.map((lane) => (
          <div
            className="grid grid-cols-[180px_minmax(0,1fr)_56px] items-center gap-3"
            key={lane.name}
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="w-4 shrink-0 font-mono text-[10px] font-semibold text-[var(--ds-text-muted)]">
                {lane.rank}
              </span>
              <span className="truncate text-[12px] text-[var(--ds-text)]" title={lane.name}>
                {lane.name}
              </span>
            </div>

            <div className="relative h-6 overflow-hidden rounded-[1px] bg-[var(--ds-surface)]">
              {lane.blocks.map((block) => {
                const position = getPositionPercent(
                  block.startHour,
                  block.endHour,
                  SHOWCASE_DAY_START,
                  SHOWCASE_DAY_END
                );

                return (
                  <div
                    className="showcase-tooltip-trigger absolute top-[2px] h-5 min-w-[2px] rounded-[1px] transition-opacity duration-150 hover:opacity-75"
                    key={`${lane.name}-${block.label}-${block.startHour}`}
                    style={{
                      left: `${position.left}%`,
                      width: `${position.width}%`,
                      background: getCategoryMeta(block.category).color,
                    }}
                  >
                    <div className="showcase-tooltip rounded-[2px] px-[10px] py-[6px]">
                      <div className="text-[12px] text-[var(--ds-text)]">
                        {block.label}
                      </div>
                      <div className="mt-[2px] font-mono text-[10px] text-[var(--ds-text-muted)]">
                        {formatClockHour(block.startHour)} - {formatClockHour(block.endHour)} ·{" "}
                        {formatDecimalHours(block.endHour - block.startHour)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="text-right font-mono text-[11px] text-[var(--ds-text-muted)]">
              {formatDecimalHours(lane.totalHours)}
            </div>
          </div>
        ))}
      </div>
    </ShowcaseSection>
  );
}

export default TopProgramsSwimLanes;
