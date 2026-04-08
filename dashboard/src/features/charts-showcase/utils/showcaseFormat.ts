import { ShowcaseCategory } from "../types";
import { CATEGORY_META } from "../data/mockShowcaseData";

export const SHOWCASE_DAY_START = 6;
export const SHOWCASE_DAY_END = 24;

export function formatDecimalHours(hours: number): string {
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);

  if (wholeHours > 0) {
    return `${wholeHours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

export function formatCompactDuration(hours: number): string {
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);
  return `${wholeHours}h${minutes > 0 ? ` ${minutes}m` : ""}`;
}

export function formatClockHour(hour: number): string {
  const hh = Math.floor(hour);
  const mm = String(Math.round((hour - hh) * 60)).padStart(2, "0");
  const twelveHour = hh > 12 ? hh - 12 : hh;
  return `${twelveHour}:${mm}${hh >= 12 ? "p" : "a"}`;
}

export function getHourTickLabels(startHour = SHOWCASE_DAY_START, endHour = SHOWCASE_DAY_END): string[] {
  const labels: string[] = [];

  for (let hour = startHour; hour < endHour; hour += 1) {
    if (hour === 12) {
      labels.push("12p");
    } else if (hour < 12) {
      labels.push(hour === startHour ? `${hour}a` : `${hour}`);
    } else {
      labels.push(`${hour - 12}`);
    }
  }

  return labels;
}

export function getPositionPercent(startHour: number, endHour: number, domainStart: number, domainEnd: number) {
  const span = domainEnd - domainStart;
  return {
    left: ((startHour - domainStart) / span) * 100,
    width: ((endHour - startHour) / span) * 100,
  };
}

export function getCategoryMeta(category: ShowcaseCategory) {
  return CATEGORY_META[category];
}
