import { CategoryHours } from "../types";
import { getCategoryMeta } from "../utils/showcaseFormat";
import ShowcaseSection from "./ShowcaseSection";

interface CategoryBreakdownBarsProps {
  rows: CategoryHours[];
  maxHours?: number;
}

function CategoryBreakdownBars({
  rows,
  maxHours = 12,
}: CategoryBreakdownBarsProps) {
  return (
    <ShowcaseSection title="Category Breakdown" delayMs={240} className="mb-12">
      <div className="flex flex-col gap-3">
        {rows.map((row) => {
          const category = getCategoryMeta(row.category);
          const pct = (row.hours / maxHours) * 100;
          const wholeHours = Math.floor(row.hours);
          const minutes = Math.round((row.hours - wholeHours) * 60);

          return (
            <div
              className="grid grid-cols-[120px_minmax(0,1fr)_60px] items-center gap-4"
              key={row.category}
            >
              <div className="flex items-center gap-2">
                <div
                  className="h-[6px] w-[6px] shrink-0"
                  style={{ background: category.color }}
                />
                <div className="text-[13px] text-[var(--ds-text)]">
                  {category.label}
                </div>
              </div>
              <div className="relative h-5 overflow-hidden rounded-[1px] bg-[var(--ds-surface)]">
                <div
                  className="h-full rounded-[1px] transition-[width] duration-[400ms] ease-out"
                  style={{ width: `${pct}%`, background: category.color }}
                />
              </div>
              <div className="text-right font-mono text-[11px] text-[var(--ds-text-muted)]">
                {wholeHours}h {minutes}m
              </div>
            </div>
          );
        })}
      </div>
    </ShowcaseSection>
  );
}

export default CategoryBreakdownBars;
