import { TimelineBlock } from "../types";
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

interface DailyActivityTimelineProps {
  blocks: TimelineBlock[];
}

function DailyActivityTimeline({ blocks }: DailyActivityTimelineProps) {
  const hourLabels = getHourTickLabels();

  return (
    <ShowcaseSection title="Activity Timeline" delayMs={120} className="mb-12">
      <div className="mb-[6px] flex justify-between">
        {hourLabels.map((label) => (
          <span
            className="w-10 text-center font-mono text-[10px] text-[var(--ds-text-muted)]"
            key={label}
          >
            {label}
          </span>
        ))}
      </div>
      <div className="relative">
        <div className="relative h-12 overflow-hidden rounded-[2px] bg-[var(--ds-surface)]">
          {blocks.map((block) => {
            const position = getPositionPercent(
              block.startHour,
              block.endHour,
              SHOWCASE_DAY_START,
              SHOWCASE_DAY_END
            );

            return (
              <div
                className="showcase-tooltip-trigger absolute top-0 h-full min-w-[2px] transition-opacity duration-150 hover:opacity-80"
                key={`${block.label}-${block.startHour}`}
                style={{
                  left: `${position.left}%`,
                  width: `${position.width}%`,
                  background: getCategoryMeta(block.category).color,
                }}
              >
                <div className="showcase-tooltip rounded-[2px]">
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
      </div>
    </ShowcaseSection>
  );
}

export default DailyActivityTimeline;
