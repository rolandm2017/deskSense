import { Navigate, Route } from "react-router-dom";

import ShowcaseShell from "./components/ShowcaseShell";
import {
  dailyRailSections,
  weeklyRailSections,
} from "./data/mockShowcaseData";
import ShowcaseDailyPage from "./pages/ShowcaseDailyPage";
import PursuitsSetupPage from "./pages/PursuitsSetupPage";
import ShowcaseWeeklyPage from "./pages/ShowcaseWeeklyPage";

export const showcaseRoutes = (
  <Route
    path="/showcase"
    element={
      <ShowcaseShell
        dailyRailSections={dailyRailSections}
        weeklyRailSections={weeklyRailSections}
      />
    }
  >
    <Route index element={<Navigate to="/showcase/daily" replace />} />
    <Route path="daily" element={<ShowcaseDailyPage />} />
    <Route path="weekly" element={<ShowcaseWeeklyPage />} />
    <Route path="pursuits-setup" element={<PursuitsSetupPage />} />
  </Route>
);
