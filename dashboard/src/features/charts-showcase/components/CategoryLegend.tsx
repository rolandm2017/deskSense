import { ShowcaseCategoryMeta } from "../types";

interface CategoryLegendProps {
  categories: ShowcaseCategoryMeta[];
  delayMs?: number;
}

function CategoryLegend({ categories, delayMs = 180 }: CategoryLegendProps) {
  return (
    <div
      className="showcase-band-enter mb-12 flex gap-5"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {categories.map((category) => (
        <div className="flex items-center gap-[6px]" key={category.key}>
          <div
            className="h-[6px] w-[6px]"
            style={{ background: category.color }}
          />
          <span className="font-mono text-[10px] uppercase tracking-[0.06em] text-[var(--ds-text-muted)]">
            {category.shortLabel ?? category.label}
          </span>
        </div>
      ))}
    </div>
  );
}

export default CategoryLegend;
