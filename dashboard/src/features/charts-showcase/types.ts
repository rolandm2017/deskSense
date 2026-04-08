export type ShowcaseCategory =
  | "productivity"
  | "learning"
  | "communication"
  | "entertainment"
  | "idle";

export interface ShowcaseCategoryMeta {
  key: ShowcaseCategory;
  label: string;
  shortLabel?: string;
  color: string;
}

export interface ShowcaseStat {
  label: string;
  value: string;
  accent?: boolean;
}

export interface TimelineBlock {
  startHour: number;
  endHour: number;
  category: ShowcaseCategory;
  label: string;
}

export interface ProgramGroupBlock {
  startHour: number;
  endHour: number;
  category: ShowcaseCategory;
  label: string;
}

export interface TopProgramLane {
  rank: number;
  name: string;
  totalHours: number;
  blocks: ProgramGroupBlock[];
}

export interface CategoryHours {
  category: ShowcaseCategory;
  hours: number;
}

export interface ProjectGoal {
  name: string;
  hours: number;
  goal: number;
  color: string;
}

export interface DailyViewData {
  title: string;
  firstActivity: string;
  lastActivity: string;
  stats: ShowcaseStat[];
  timelineBlocks: TimelineBlock[];
  topPrograms: TopProgramLane[];
  categoryBreakdown: CategoryHours[];
  projects: ProjectGoal[];
}

export interface WeeklyDayBreakdown {
  day: string;
  total: number;
  isToday?: boolean;
  values: Record<ShowcaseCategory, number>;
}

export interface TrendPoint {
  label: string;
  hours: number;
}

export interface ScoreboardRow {
  name: string;
  actual: number;
  goal: number;
  delta: number;
}

export interface WeeklyViewData {
  title: string;
  range: string;
  stats: ShowcaseStat[];
  dailyBreakdown: WeeklyDayBreakdown[];
  productiveGoalHours: number;
  trend: TrendPoint[];
  scoreboard: ScoreboardRow[];
}

export interface RailNote {
  label: string;
  value: string;
}

export interface RailSection {
  title: string;
  notes: RailNote[];
}
