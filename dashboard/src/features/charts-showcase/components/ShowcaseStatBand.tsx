import { Fragment } from "react";

import { ShowcaseStat } from "../types";

interface ShowcaseStatBandProps {
  stats: ShowcaseStat[];
  delayMs?: number;
}

function renderStatValue(value: string) {
  const parts = value.split(" ");

  return parts.map((part, index) => {
    const match = part.match(/^([+-]?\d+)([a-z%]+)?$/i);
    if (!match) {
      return <Fragment key={`${value}-${index}`}>{part} </Fragment>;
    }

    const [, number, unit] = match;

    return (
      <Fragment key={`${value}-${index}`}>
        {index > 0 ? " " : null}
        {number}
        {unit ? (
          <span className="ml-1 align-baseline font-mono text-[11px] text-[var(--ds-text-muted)]">
            {unit}
          </span>
        ) : null}
      </Fragment>
    );
  });
}

function ShowcaseStatBand({ stats, delayMs = 60 }: ShowcaseStatBandProps) {
  return (
    <section
      className="showcase-band-enter mb-12 flex border-y border-[var(--ds-rule)]"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {stats.map((stat) => (
        <div
          className="flex-1 border-r border-[var(--ds-rule)] py-6 last:border-r-0"
          key={stat.label}
        >
          <div className="mb-2 font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-[var(--ds-text-muted)]">
            {stat.label}
          </div>
          <div
            className={`font-display text-[30px] leading-none ${
              stat.accent ? "text-[var(--ds-accent)]" : "text-[var(--ds-text)]"
            }`}
          >
            {renderStatValue(stat.value)}
          </div>
        </div>
      ))}
    </section>
  );
}

export default ShowcaseStatBand;
