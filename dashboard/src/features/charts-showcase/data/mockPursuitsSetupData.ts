import { PursuitCandidateRow, PursuitDefinition } from "../types";

export const mockPursuits: PursuitDefinition[] = [
  {
    pursuitId: "p_copywriting",
    name: "Freelance Copywriting",
    category: "productivity",
    color: "#C7F36B",
    weeklyGoalSeconds: 72_000,
  },
  {
    pursuitId: "p_japanese",
    name: "Learning Japanese",
    category: "learning",
    color: "#7DD3C7",
    weeklyGoalSeconds: 36_000,
  },
  {
    pursuitId: "p_entertainment",
    name: "Entertainment",
    category: "entertainment",
    color: "#F28A2E",
    weeklyGoalSeconds: null,
  },
];

export const mockPursuitCandidates: PursuitCandidateRow[] = [
  {
    sourceType: "program",
    identifier: "Code.exe",
    displayName: "VS Code",
    last30dSeconds: 146_400,
    currentPursuitId: null,
  },
  {
    sourceType: "domain",
    identifier: "docs.google.com",
    displayName: "Google Docs",
    last30dSeconds: 88_200,
    currentPursuitId: null,
  },
  {
    sourceType: "program",
    identifier: "Obsidian.exe",
    displayName: "Obsidian",
    last30dSeconds: 51_600,
    currentPursuitId: null,
  },
  {
    sourceType: "domain",
    identifier: "youtube.com",
    displayName: "YouTube",
    last30dSeconds: 72_000,
    currentPursuitId: "p_entertainment",
  },
  {
    sourceType: "domain",
    identifier: "bunpro.jp",
    displayName: "Bunpro",
    last30dSeconds: 39_000,
    currentPursuitId: "p_japanese",
  },
  {
    sourceType: "program",
    identifier: "Slack.exe",
    displayName: "Slack",
    last30dSeconds: 34_800,
    currentPursuitId: null,
  },
];
