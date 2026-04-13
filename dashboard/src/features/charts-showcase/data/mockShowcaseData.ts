import {
  DailyViewData,
  ActivityOverviewData,
  RailSection,
  ShowcaseCategory,
  ShowcaseCategoryMeta,
  WeeklyViewData,
} from "../types";

export const CATEGORY_META: Record<ShowcaseCategory, ShowcaseCategoryMeta> = {
  productivity: {
    key: "productivity",
    label: "Productivity",
    shortLabel: "Productive",
    color: "#C7F36B",
  },
  learning: {
    key: "learning",
    label: "Learning",
    shortLabel: "Learning",
    color: "#7DD3C7",
  },
  communication: {
    key: "communication",
    label: "Communication",
    shortLabel: "Comms",
    color: "#E9687A",
  },
  entertainment: {
    key: "entertainment",
    label: "Entertainment",
    shortLabel: "Entertainment",
    color: "#F28A2E",
  },
  idle: {
    key: "idle",
    label: "Idle",
    shortLabel: "Idle",
    color: "#6B6560",
  },
};

export const dailyShowcaseData: DailyViewData = {
  title: "Monday, April 7",
  firstActivity: "07:42",
  lastActivity: "23:18",
  stats: [
    { label: "Tracked Today", value: "9h 34m" },
    { label: "Productive", value: "6h 12m", accent: true },
    { label: "Projects Active", value: "3" },
    { label: "Focus Score", value: "72%" },
  ],
  timelineBlocks: [
    { startHour: 7.7, endHour: 8.1, category: "productivity", label: "VS Code — DeskSense" },
    { startHour: 8.1, endHour: 8.3, category: "communication", label: "Gmail" },
    { startHour: 8.3, endHour: 10.5, category: "productivity", label: "VS Code — DeskSense" },
    { startHour: 10.5, endHour: 10.8, category: "idle", label: "Away" },
    { startHour: 10.8, endHour: 12.2, category: "productivity", label: "VS Code — DeskSense" },
    { startHour: 12.2, endHour: 12.9, category: "entertainment", label: "YouTube" },
    { startHour: 12.9, endHour: 13.1, category: "idle", label: "Away — Lunch" },
    { startHour: 13.1, endHour: 14.0, category: "learning", label: "Anki — Japanese" },
    { startHour: 14.0, endHour: 14.5, category: "learning", label: "Chrome — Bunpro" },
    { startHour: 14.5, endHour: 16.8, category: "productivity", label: "VS Code — Client Project" },
    { startHour: 16.8, endHour: 17.1, category: "communication", label: "Slack" },
    { startHour: 17.1, endHour: 17.6, category: "productivity", label: "VS Code — Client Project" },
    { startHour: 17.6, endHour: 18.0, category: "idle", label: "Away" },
    { startHour: 18.0, endHour: 19.2, category: "entertainment", label: "Steam — Factorio" },
    { startHour: 19.2, endHour: 20.8, category: "learning", label: "Chrome — Khan Academy (Math)" },
    { startHour: 20.8, endHour: 21.3, category: "entertainment", label: "YouTube" },
    { startHour: 21.3, endHour: 23.0, category: "productivity", label: "VS Code — DeskSense" },
    { startHour: 23.0, endHour: 23.3, category: "communication", label: "Discord" },
  ],
  topPrograms: [
    {
      rank: 1,
      name: "Code Work Cluster",
      totalHours: 7.8,
      blocks: [
        { startHour: 7.7, endHour: 8.1, category: "productivity", label: "VS Code — DeskSense" },
        { startHour: 8.3, endHour: 10.5, category: "productivity", label: "VS Code — DeskSense" },
        { startHour: 10.8, endHour: 12.2, category: "productivity", label: "VS Code — DeskSense" },
        { startHour: 14.5, endHour: 16.8, category: "productivity", label: "VS Code — Client Project" },
        { startHour: 17.1, endHour: 17.6, category: "productivity", label: "VS Code — Client Project" },
        { startHour: 21.3, endHour: 23.0, category: "productivity", label: "VS Code — DeskSense" },
      ],
    },
    {
      rank: 2,
      name: "Study Browser Cluster",
      totalHours: 3,
      blocks: [
        { startHour: 13.1, endHour: 14.0, category: "learning", label: "Anki — Japanese" },
        { startHour: 14.0, endHour: 14.5, category: "learning", label: "Chrome — Bunpro" },
        { startHour: 19.2, endHour: 20.8, category: "learning", label: "Chrome — Khan Academy (Math)" },
      ],
    },
    {
      rank: 3,
      name: "Media + Messages",
      totalHours: 2,
      blocks: [
        { startHour: 8.1, endHour: 8.3, category: "communication", label: "Gmail" },
        { startHour: 12.2, endHour: 12.9, category: "entertainment", label: "YouTube" },
        { startHour: 16.8, endHour: 17.1, category: "communication", label: "Slack" },
        { startHour: 20.8, endHour: 21.3, category: "entertainment", label: "YouTube" },
        { startHour: 23.0, endHour: 23.3, category: "communication", label: "Discord" },
      ],
    },
  ],
  categoryBreakdown: [
    { category: "productivity", hours: 6.2 },
    { category: "learning", hours: 2.4 },
    { category: "entertainment", hours: 1.9 },
    { category: "communication", hours: 0.8 },
    { category: "idle", hours: 0.7 },
  ],
  projects: [
    { name: "Copywriting Freelancing", hours: 2.1, goal: 4, color: "#C7F36B" },
    { name: "Learning Japanese", hours: 1.5, goal: 1.5, color: "#7DD3C7" },
    { name: "Studying Mathematics", hours: 1.6, goal: 2, color: "#7DD3C7" },
  ],
};

export const activityOverviewData: ActivityOverviewData = {
  title: "Monday, April 7",
  firstActivity: "07:42",
  lastActivity: "23:18",
  programsTracked: "12",
  stats: [
    { label: "Active Time", value: "9h 34m" },
    { label: "Idle Time", value: "2h 48m" },
    { label: "Longest Session", value: "2h 12m" },
    { label: "Unique Programs", value: "12" },
  ],
  presence: [
    { startHour: 7.7, endHour: 10.5, active: true },
    { startHour: 10.5, endHour: 10.83, active: false },
    { startHour: 10.83, endHour: 12.85, active: true },
    { startHour: 12.85, endHour: 13.17, active: false },
    { startHour: 13.17, endHour: 17.6, active: true },
    { startHour: 17.6, endHour: 18, active: false },
    { startHour: 18, endHour: 21.33, active: true },
    { startHour: 21.33, endHour: 21.5, active: false },
    { startHour: 21.5, endHour: 23.3, active: true },
  ],
  programs: [
    {
      name: "VS Code",
      category: "productivity",
      sessions: [
        { startHour: 7.7, endHour: 8.1, detail: "DeskSense — main.ts" },
        { startHour: 8.33, endHour: 10.5, detail: "DeskSense — renderer.ts" },
        { startHour: 10.83, endHour: 12.2, detail: "DeskSense — chart.ts" },
        { startHour: 14.5, endHour: 16.83, detail: "Client Project — api.py" },
        { startHour: 17.1, endHour: 17.6, detail: "Client Project — tests.py" },
        { startHour: 21.5, endHour: 23, detail: "DeskSense — timeline.ts" },
      ],
    },
    {
      name: "Chrome",
      category: "productivity",
      sessions: [
        { startHour: 8.1, endHour: 8.33, detail: "Stack Overflow — async patterns" },
        { startHour: 13.17, endHour: 13.5, detail: "MDN Web Docs" },
        { startHour: 14, endHour: 14.5, detail: "Bunpro — Grammar N3" },
        { startHour: 19.2, endHour: 20.83, detail: "Khan Academy — Linear Algebra" },
        { startHour: 23, endHour: 23.17, detail: "GitHub — pull requests" },
      ],
    },
    {
      name: "Terminal",
      category: "productivity",
      sessions: [
        { startHour: 7.83, endHour: 8, detail: "npm run dev" },
        { startHour: 8.5, endHour: 8.67, detail: "git push" },
        { startHour: 10.83, endHour: 11, detail: "docker compose up" },
        { startHour: 14.67, endHour: 14.83, detail: "pytest" },
        { startHour: 16.83, endHour: 17, detail: "ssh deploy" },
        { startHour: 21.67, endHour: 21.83, detail: "npm run build" },
      ],
    },
    {
      name: "Gmail",
      category: "communication",
      sessions: [
        { startHour: 8.1, endHour: 8.3, detail: "Inbox — client correspondence" },
        { startHour: 17, endHour: 17.1, detail: "Inbox — invoicing" },
      ],
    },
    {
      name: "Slack",
      category: "communication",
      sessions: [
        { startHour: 11, endHour: 11.17, detail: "#dev — standup" },
        { startHour: 16.83, endHour: 17.1, detail: "#general — EOD updates" },
      ],
    },
    {
      name: "Discord",
      category: "communication",
      sessions: [{ startHour: 23, endHour: 23.3, detail: "Server — dev community" }],
    },
    {
      name: "YouTube",
      category: "entertainment",
      parentApp: "Chrome",
      sessions: [{ startHour: 12.2, endHour: 12.85, detail: "3Blue1Brown — Essence of LA" }],
    },
    {
      name: "VLC Player",
      category: "entertainment",
      sessions: [{ startHour: 12.5, endHour: 12.85, detail: "lecture-recording-04.mkv" }],
    },
    {
      name: "Anki",
      category: "learning",
      sessions: [{ startHour: 13.17, endHour: 14, detail: "Japanese Core 2000 — Review" }],
    },
    {
      name: "Factorio",
      category: "entertainment",
      sessions: [{ startHour: 18, endHour: 19.2, detail: "Nauvis — iron smelting" }],
    },
    {
      name: "Obsidian",
      category: "productivity",
      sessions: [
        { startHour: 11.17, endHour: 11.33, detail: "Daily note — April 7" },
        { startHour: 20.83, endHour: 21, detail: "Math notes — eigenvalues" },
      ],
    },
    {
      name: "File Explorer",
      category: "productivity",
      sessions: [
        { startHour: 11.33, endHour: 11.42, detail: "Downloads folder" },
        { startHour: 21, endHour: 21.08, detail: "Projects directory" },
      ],
    },
  ],
};

export const weeklyShowcaseData: WeeklyViewData = {
  title: "Week 15",
  range: "March 31 — April 6, 2026",
  stats: [
    { label: "Total Tracked", value: "51h 22m" },
    { label: "Productive", value: "33h 48m", accent: true },
    { label: "Daily Average", value: "7h 20m" },
    { label: "vs Last Week", value: "+4h 11m", accent: true },
  ],
  dailyBreakdown: [
    {
      day: "Mon",
      isToday: true,
      total: 9.3,
      values: { productivity: 5.2, learning: 1.8, communication: 0.5, entertainment: 1.0, idle: 0.8 },
    },
    {
      day: "Tue",
      total: 10.5,
      values: { productivity: 6.8, learning: 2.1, communication: 0.7, entertainment: 0.5, idle: 0.4 },
    },
    {
      day: "Wed",
      total: 9.7,
      values: { productivity: 4.1, learning: 1.2, communication: 1.1, entertainment: 2.3, idle: 1.0 },
    },
    {
      day: "Thu",
      total: 9.7,
      values: { productivity: 7.2, learning: 1.5, communication: 0.4, entertainment: 0.3, idle: 0.3 },
    },
    {
      day: "Fri",
      total: 10.7,
      values: { productivity: 5.9, learning: 2.4, communication: 0.6, entertainment: 1.2, idle: 0.6 },
    },
    {
      day: "Sat",
      total: 9.6,
      values: { productivity: 2.1, learning: 3.2, communication: 0.3, entertainment: 2.8, idle: 1.2 },
    },
    {
      day: "Sun",
      total: 7.1,
      values: { productivity: 2.5, learning: 2.0, communication: 0.2, entertainment: 1.4, idle: 1.0 },
    },
  ],
  productiveGoalHours: 7,
  trend: [
    { label: "W8", hours: 22.4 },
    { label: "W9", hours: 28.1 },
    { label: "W10", hours: 19.8 },
    { label: "W11", hours: 31.5 },
    { label: "W12", hours: 35.2 },
    { label: "W13", hours: 29.7 },
    { label: "W14", hours: 33.8 },
    { label: "W15", hours: 33.8 },
  ],
  scoreboard: [
    { name: "Copywriting Freelancing", actual: 18.2, goal: 20, delta: 2.4 },
    { name: "Learning Japanese", actual: 10.5, goal: 10, delta: 0.5 },
    { name: "Studying Mathematics", actual: 12.8, goal: 14, delta: -1.2 },
    { name: "DeskSense Development", actual: 8.3, goal: 8, delta: 0.3 },
  ],
};

export const dailyRailSections: RailSection[] = [
  {
    title: "Reading",
    notes: [
      { label: "Peak focus", value: "8:18a - 12:12p" },
      { label: "Largest gap", value: "12:54p - 1:06p" },
      { label: "Strongest lane", value: "Code Work Cluster" },
    ],
  },
  {
    title: "Projects",
    notes: [
      { label: "Freelancing pace", value: "52% of daily target" },
      { label: "Japanese", value: "Goal met" },
      { label: "Math", value: "0.4h remaining" },
    ],
  },
  {
    title: "Notes",
    notes: [
      { label: "Pattern", value: "Work first, study late, entertainment after dinner" },
      { label: "Signal", value: "Good recovery after two brief idle interruptions" },
    ],
  },
];

export const weeklyRailSections: RailSection[] = [
  {
    title: "Reading",
    notes: [
      { label: "Best day", value: "Friday · 10h 42m tracked" },
      { label: "Most productive", value: "Thursday · 7h 12m" },
      { label: "Softest day", value: "Sunday" },
    ],
  },
  {
    title: "Projects",
    notes: [
      { label: "Ahead", value: "Copywriting +2.4h" },
      { label: "On pace", value: "Japanese +0.5h" },
      { label: "Needs push", value: "Math -1.2h" },
    ],
  },
  {
    title: "Notes",
    notes: [
      { label: "Trend", value: "Productive hours holding flat at 33.8h" },
      { label: "Shape", value: "Weekday structure remains strong, weekend opens up" },
    ],
  },
];
