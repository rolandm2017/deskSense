import CategoryLegend from "../components/CategoryLegend";
import ProjectScoreboard from "../components/ProjectScoreboard";
import ShowcaseStatBand from "../components/ShowcaseStatBand";
import WeeklyStackedBreakdownChart from "../components/WeeklyStackedBreakdownChart";
import WeeklyTrendChart from "../components/WeeklyTrendChart";
import { CATEGORY_META, weeklyShowcaseData } from "../data/mockShowcaseData";

function ShowcaseWeeklyPage() {
  return (
    <div>
      <section className="showcase-band-enter mb-8" style={{ animationDelay: "0ms" }}>
        <div className="mb-8 flex items-baseline justify-between">
          <div className="font-display text-[42px] leading-none text-[var(--ds-text)]">
            {weeklyShowcaseData.title}
          </div>
          <div className="font-mono text-[11px] text-[var(--ds-text-muted)]">
            {weeklyShowcaseData.range}
          </div>
        </div>
      </section>

      <ShowcaseStatBand stats={weeklyShowcaseData.stats} />
      <WeeklyStackedBreakdownChart
        days={weeklyShowcaseData.dailyBreakdown}
        goalHours={weeklyShowcaseData.productiveGoalHours}
      />
      <CategoryLegend categories={Object.values(CATEGORY_META)} />
      <WeeklyTrendChart points={weeklyShowcaseData.trend} />
      <ProjectScoreboard rows={weeklyShowcaseData.scoreboard} />
    </div>
  );
}

export default ShowcaseWeeklyPage;
