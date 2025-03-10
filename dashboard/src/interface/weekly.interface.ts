import {
    DailyProgramSummary,
    DailyDomainSummary,
    TypingSessionsReport,
    MouseReport,
    TimelineRows,
} from "./api.interface";
import { DayOfAggregatedRows } from "./misc.interface";

export interface DayOfTyping {
    date: Date;
    usage: TypingSessionsReport;
}

export interface DayOfClicking {
    date: Date;
    usage: MouseReport;
}

export interface DayOfProgramUsage {
    date: Date;
    usage: DailyProgramSummary;
}

export interface DayOfChromeUsage {
    date: Date;
    content: { columns: DailyDomainSummary[] };
}

export interface DayOfTimelineRows {
    date: Date;
    row: TimelineRows;
}

/*
 * Weekly
 * Weekly
 */

export interface WeeklyTyping {
    days: DayOfTyping[];
}

export interface WeeklyClicking {
    days: DayOfClicking[];
}

export interface WeeklyProgramUsage {
    days: DayOfProgramUsage[];
}

export interface WeeklyProgramTimelines {
    days: ProgamUsageTimeline[];
}

export interface WeeklyChromeUsage {
    days: DayOfChromeUsage[];
}

export interface WeeklyTimeline {
    days: DayOfTimelineRows[]; // between 1 and 7 entries long
}

export interface PartiallyAggregatedWeeklyTimeline {
    beforeToday: DayOfTimelineRows[]; // between 0 and 6 entries long
    today: DayOfTimelineRows;
    startDate: string;
}

/*
 * Graph stuff
 *
 */

export interface SocialMediaUsage {
    day: string;
    hours: number;
}

export interface BreakdownByDay {
    day: Date;
    productiveHours: number;
    leisureHours: number;
}
export interface WeeklyBreakdown {
    days: BreakdownByDay[];
}

// **
// ****
// Program Usage Timeline
// *

export interface ProgamUsageTimeline {
    date: Date | string;
    programs: ProgramTimelineContent[];
    // events: TimelineEvent[];
}

export interface ProgramTimelineContent {
    programName: string;
    events: TimelineEvent[];
}

export interface TimelineEvent {
    startTime: Date;
    endTime: Date;
}
