import ShowcaseStatBand from "../components/ShowcaseStatBand";
import { CATEGORY_META, activityOverviewData } from "../data/mockShowcaseData";
import { ActivityOverviewProgram, ActivityOverviewSession } from "../types";

const ACTIVITY_DAY_START = 4;
const ACTIVITY_DAY_END = 28;

function toPercent(hour: number) {
  return ((hour - ACTIVITY_DAY_START) / (ACTIVITY_DAY_END - ACTIVITY_DAY_START)) * 100;
}

function formatActivityClockHour(hour: number) {
  const normalizedHour = hour >= 24 ? hour - 24 : hour;
  const wholeHour = Math.floor(normalizedHour);
  const minutes = String(Math.round((normalizedHour - wholeHour) * 60)).padStart(2, "0");
  const meridiem = wholeHour >= 12 ? "p" : "a";
  const twelveHour = wholeHour === 0 ? 12 : wholeHour > 12 ? wholeHour - 12 : wholeHour;

  return `${twelveHour}:${minutes}${meridiem}`;
}

function formatActivityDuration(hours: number) {
  if (hours >= 1) {
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    return minutes > 0 ? `${wholeHours}h ${minutes}m` : `${wholeHours}h`;
  }

  return `${Math.round(hours * 60)}m`;
}

function formatActivityTick(hour: number) {
  const normalizedHour = hour >= 24 ? hour - 24 : hour;

  if (normalizedHour === 0) {
    return "12a";
  }

  if (normalizedHour === 12) {
    return "12p";
  }

  return normalizedHour < 12 ? `${normalizedHour}a` : `${normalizedHour - 12}p`;
}

function getActivityTickLabels() {
  const labels: string[] = [];

  for (let hour = ACTIVITY_DAY_START; hour < ACTIVITY_DAY_END; hour += 1) {
    labels.push(formatActivityTick(hour));
  }

  return labels;
}

function getTotalHours(sessions: ActivityOverviewSession[]) {
  return sessions.reduce((total, session) => total + session.endHour - session.startHour, 0);
}

function ActivityTooltip({
  title,
  startHour,
  endHour,
}: {
  title: string;
  startHour: number;
  endHour: number;
}) {
  return (
    <div className="showcase-tooltip rounded-[2px] px-[10px] py-[6px]">
      <div className="text-[12px] text-[var(--ds-text)]">{title}</div>
      <div className="mt-[2px] font-mono text-[10px] text-[var(--ds-text-muted)]">
        {formatActivityClockHour(startHour)} - {formatActivityClockHour(endHour)} ·{" "}
        {formatActivityDuration(endHour - startHour)}
      </div>
    </div>
  );
}

function ActivityTimeAxis() {
  return (
    <div className="mb-[6px] flex justify-between pl-40 pr-14">
      {getActivityTickLabels().map((label) => (
        <span
          className="w-7 text-center font-mono text-[10px] text-[var(--ds-text-muted)]"
          key={label}
        >
          {label}
        </span>
      ))}
    </div>
  );
}

function PresenceLane() {
  const activeTotal = activityOverviewData.presence.reduce(
    (total, block) => total + (block.active ? block.endHour - block.startHour : 0),
    0
  );

  return (
    <section
      className="showcase-band-enter mb-8"
      style={{ animationDelay: "180ms" }}
    >
      <div className="mb-4 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
        Active vs Idle
      </div>
      <div className="relative">
        <div className="grid grid-cols-[160px_minmax(0,1fr)_56px] items-center">
          <div className="pr-3 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-[var(--ds-text-muted)]">
            Presence
          </div>
          <div className="relative h-7 overflow-hidden rounded-[1px] bg-[var(--ds-surface)]">
            {activityOverviewData.presence.map((block) => {
              const left = toPercent(block.startHour);
              const width = toPercent(block.endHour) - left;

              return (
                <div
                  className="showcase-tooltip-trigger absolute top-0 h-full min-w-px transition-opacity duration-150 hover:opacity-75"
                  key={`${block.startHour}-${block.endHour}-${block.active}`}
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                    background: block.active
                      ? CATEGORY_META.productivity.color
                      : CATEGORY_META.idle.color,
                    opacity: block.active ? 0.5 : 0.25,
                  }}
                >
                  <ActivityTooltip
                    title={block.active ? "Active" : "Idle"}
                    startHour={block.startHour}
                    endHour={block.endHour}
                  />
                </div>
              );
            })}
          </div>
          <div className="pl-3 text-right font-mono text-[11px] text-[var(--ds-text-muted)]">
            {formatActivityDuration(activeTotal)}
          </div>
        </div>
      </div>
    </section>
  );
}

function ProgramLane({ program, rank }: { program: ActivityOverviewProgram; rank: number }) {
  const color = CATEGORY_META[program.category].color;
  const totalHours = getTotalHours(program.sessions);

  return (
    <div className="mb-1 grid grid-cols-[160px_minmax(0,1fr)_56px] items-center">
      <div className="flex min-w-0 items-center gap-2 pr-3">
        <span className="w-[18px] shrink-0 text-right font-mono text-[10px] font-semibold text-[var(--ds-text-muted)]">
          {rank}
        </span>
        <span
          className="flex h-[14px] w-[14px] shrink-0 items-center justify-center rounded-[1px] font-mono text-[8px] font-semibold text-[var(--ds-bg)]"
          style={{ background: color }}
        >
          {program.name.charAt(0)}
        </span>
        <span
          className="truncate text-[12px] text-[var(--ds-text)]"
          title={program.name}
        >
          {program.name}
          {program.parentApp ? (
            <span
              className="ml-1 inline-block h-1 w-1 align-middle opacity-60"
              style={{ background: CATEGORY_META.productivity.color }}
              title={`via ${program.parentApp}`}
            />
          ) : null}
        </span>
      </div>

      <div className="relative h-[22px] overflow-hidden rounded-[1px] bg-[var(--ds-surface)]">
        {program.sessions.map((session) => {
          const left = toPercent(session.startHour);
          const width = Math.max(toPercent(session.endHour) - left, 0.15);

          return (
            <div
              className="showcase-tooltip-trigger absolute top-0.5 h-[18px] min-w-[2px] rounded-[1px] transition-opacity duration-150 hover:opacity-75"
              key={`${program.name}-${session.startHour}-${session.endHour}-${session.detail}`}
              style={{
                left: `${left}%`,
                width: `${width}%`,
                background: color,
              }}
            >
              <ActivityTooltip
                title={`${program.name} — ${session.detail}`}
                startHour={session.startHour}
                endHour={session.endHour}
              />
            </div>
          );
        })}
      </div>

      <div className="pl-3 text-right font-mono text-[11px] text-[var(--ds-text-muted)]">
        {formatActivityDuration(totalHours)}
      </div>
    </div>
  );
}

function ActivityLanes() {
  const programs = [...activityOverviewData.programs]
    .map((program) => ({ ...program, totalHours: getTotalHours(program.sessions) }))
    .sort((a, b) => b.totalHours - a.totalHours)
    .slice(0, 12);

  return (
    <section
      className="showcase-band-enter mb-12"
      style={{ animationDelay: "300ms" }}
    >
      <div className="mb-4 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--ds-text-muted)]">
        Top 12 Activities
      </div>
      <div className="relative">
        {programs.map((program, index) => (
          <ProgramLane
            key={program.name}
            program={program}
            rank={index + 1}
          />
        ))}
      </div>
    </section>
  );
}

function ActivityLegend() {
  return (
    <div
      className="showcase-band-enter mb-12 mt-8 flex gap-5 border-t border-[var(--ds-rule)] pt-4"
      style={{ animationDelay: "360ms" }}
    >
      {Object.values(CATEGORY_META).map((category) => (
        <div className="flex items-center gap-1.5" key={category.key}>
          <span className="h-1.5 w-1.5" style={{ background: category.color }} />
          <span className="font-mono text-[10px] uppercase tracking-[0.06em] text-[var(--ds-text-muted)]">
            {category.shortLabel ?? category.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function ShowcaseActivityOverviewPage() {
  return (
    <div>
      <section
        className="showcase-band-enter mb-8"
        style={{ animationDelay: "0ms" }}
      >
        <div className="mb-8 flex items-baseline justify-between">
          <div className="font-display text-[42px] leading-none text-[var(--ds-text)]">
            {activityOverviewData.title}
          </div>
          <div className="text-right font-mono text-[11px] leading-[1.7] text-[var(--ds-text-muted)]">
            First activity {activityOverviewData.firstActivity}
            <br />
            Last activity {activityOverviewData.lastActivity}
            <br />
            {activityOverviewData.programsTracked} programs tracked
          </div>
        </div>
      </section>

      <ShowcaseStatBand stats={activityOverviewData.stats} delayMs={60} />
      <div className="showcase-band-enter" style={{ animationDelay: "120ms" }}>
        <ActivityTimeAxis />
      </div>
      <PresenceLane />
      <hr className="showcase-band-enter mb-6 border-t border-[var(--ds-rule)]" style={{ animationDelay: "240ms" }} />
      <ActivityLanes />
      <ActivityLegend />
    </div>
  );
}

export default ShowcaseActivityOverviewPage;
