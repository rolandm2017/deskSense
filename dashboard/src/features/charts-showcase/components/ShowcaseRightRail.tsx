import { RailSection } from "../types";
import { ShowcaseCategoryMeta } from "../types";

interface ShowcaseRightRailProps {
  heading: string;
  subheading: string;
  sections: RailSection[];
  categories: ShowcaseCategoryMeta[];
}

function ShowcaseRightRail({
  heading,
  subheading,
  sections,
  categories,
}: ShowcaseRightRailProps) {
  return (
    <aside className="sticky top-12 h-[calc(100vh-96px)] w-[280px] self-start border-l border-[var(--ds-rule)] pl-8">
      <div className="showcase-band-enter" style={{ animationDelay: "120ms" }}>
        <div className="mb-2 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
          Observatory
        </div>
        <div className="font-display text-[30px] leading-none text-[var(--ds-text)]">
          {heading}
        </div>
        <div className="mt-3 font-mono text-[11px] leading-6 text-[var(--ds-text-muted)]">
          {subheading}
        </div>
      </div>

      <div
        className="showcase-rail-card showcase-band-enter mt-8"
        style={{ animationDelay: "180ms" }}
      >
        <div className="mb-4 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
          Categories
        </div>
        <div className="flex flex-col gap-3">
          {categories.map((category) => (
            <div className="flex items-center gap-3" key={category.key}>
              <div
                className="h-[6px] w-[6px] shrink-0"
                style={{ background: category.color }}
              />
              <div className="font-mono text-[10px] uppercase tracking-[0.06em] text-[var(--ds-text-muted)]">
                {category.shortLabel ?? category.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {sections.map((section, index) => (
        <div
          className="showcase-rail-card showcase-band-enter mt-8"
          key={section.title}
          style={{ animationDelay: `${240 + index * 60}ms` }}
        >
          <div className="mb-4 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
            {section.title}
          </div>
          <div className="flex flex-col gap-4">
            {section.notes.map((note) => (
              <div key={`${section.title}-${note.label}`}>
                <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-[var(--ds-text-muted)]">
                  {note.label}
                </div>
                <div className="mt-1 text-[13px] leading-5 text-[var(--ds-text)]">
                  {note.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </aside>
  );
}

export default ShowcaseRightRail;
