import { PropsWithChildren } from "react";

interface ShowcaseSectionProps extends PropsWithChildren {
  title: string;
  delayMs: number;
  className?: string;
}

function ShowcaseSection({
  title,
  delayMs,
  className = "",
  children,
}: ShowcaseSectionProps) {
  return (
    <section
      className={`showcase-band-enter ${className}`}
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="mb-4 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
        {title}
      </div>
      {children}
    </section>
  );
}

export default ShowcaseSection;
