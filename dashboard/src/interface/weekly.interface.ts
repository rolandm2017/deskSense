import {
    DailyProgramSummary,
    DailyDomainSummary,
    TypingSessionsReport,
    MouseReport,
    TimelineRows,
} from "./api.interface";

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

export interface WeeklyChromeUsage {
    days: DayOfChromeUsage[];
}

export interface WeeklyTimeline {
    days: DayOfTimelineRows[]; // between 1 and 7 entries long
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
