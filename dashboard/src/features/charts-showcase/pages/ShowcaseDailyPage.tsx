import CategoryBreakdownBars from "../components/CategoryBreakdownBars";
import DailyActivityTimeline from "../components/DailyActivityTimeline";
import DailyProjectsList from "../components/DailyProjectsList";
import ShowcaseStatBand from "../components/ShowcaseStatBand";
import TopProgramsSwimLanes from "../components/TopProgramsSwimLanes";
import { dailyShowcaseData } from "../data/mockShowcaseData";

function ShowcaseDailyPage() {
  return (
    <div>
      <section className="showcase-band-enter mb-8" style={{ animationDelay: "0ms" }}>
        <div className="mb-8 flex items-baseline justify-between">
          <div className="font-display text-[42px] leading-none text-[var(--ds-text)]">
            {dailyShowcaseData.title}
          </div>
          <div className="text-right font-mono text-[11px] leading-[1.7] text-[var(--ds-text-muted)]">
            First activity {dailyShowcaseData.firstActivity}
            <br />
            Last activity {dailyShowcaseData.lastActivity}
          </div>
        </div>
      </section>

      <ShowcaseStatBand stats={dailyShowcaseData.stats} />
      <DailyActivityTimeline blocks={dailyShowcaseData.timelineBlocks} />
      <TopProgramsSwimLanes lanes={dailyShowcaseData.topPrograms} />
      <CategoryBreakdownBars rows={dailyShowcaseData.categoryBreakdown} />
      <div className="h-8" />
      <DailyProjectsList projects={dailyShowcaseData.projects} />
    </div>
  );
}

export default ShowcaseDailyPage;
