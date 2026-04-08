import { Outlet, useLocation } from "react-router-dom";

import { CATEGORY_META } from "../data/mockShowcaseData";
import { RailSection } from "../types";
import ShowcaseRightRail from "./ShowcaseRightRail";
import ShowcaseViewNav from "./ShowcaseViewNav";

interface ShowcaseShellProps {
  dailyRailSections: RailSection[];
  weeklyRailSections: RailSection[];
}

function ShowcaseShell({
  dailyRailSections,
  weeklyRailSections,
}: ShowcaseShellProps) {
  const location = useLocation();
  const weeklyActive = location.pathname.includes("/weekly");
  const railSections = weeklyActive ? weeklyRailSections : dailyRailSections;

  return (
    <div className="min-h-screen bg-[var(--ds-bg)] px-8 py-12 text-[13px] text-[var(--ds-text)]">
      <div className="mx-auto flex max-w-[1200px] gap-10">
        <div className="min-w-0 flex-1">
          <ShowcaseViewNav />
          <Outlet />
        </div>
        <ShowcaseRightRail
          heading={weeklyActive ? "This Week" : "Today"}
          subheading={
            weeklyActive
              ? "Shared rail, route-backed views, and static readings for the weekly poster."
              : "Static showcase mode. Hardcoded values for visual conversion before live data wiring."
          }
          sections={railSections}
          categories={Object.values(CATEGORY_META)}
        />
      </div>
    </div>
  );
}

export default ShowcaseShell;
