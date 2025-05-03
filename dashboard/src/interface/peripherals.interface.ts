export interface DayOfTyping {
    date: Date;
    usage: TypingSessionsReport;
}

export interface DayOfClicking {
    date: Date;
    usage: MouseReport;
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

export interface WeeklyTimeline {
    days: DayOfTimelineRows[]; // between 1 and 7 entries long
}

export interface PartiallyAggregatedWeeklyTimeline {
    beforeToday: DayOfTimelineRows[]; // between 0 and 6 entries long
    today: DayOfTimelineRows;
    startDate: string;
}

export interface TypingSessionLog {
    keyboardEventId: number;
    startTime: string; // ISO 8601 datetime string
    endTime: string; // ISO 8601 datetime string
}

export interface TypingSessionsReport {
    count: number;
    keyboardLogs: TypingSessionLog[];
}

export interface MouseLog {
    mouseEventId: number;
    startTime: string; // ISO 8601 datetime string
    endTime: string; // ISO 8601 datetime string
}

export interface MouseReport {
    count: number;
    mouseLogs: MouseLog[];
}

/*
 *
 * Daily section
 * Daily section
 * Daily section
 * Daily section
 *
 */

export interface TimelineEntrySchema {
    id: string;
    group: string;
    content: string;
    start: Date;
    end: Date;
}

export interface TimelineRows {
    mouseRows: TimelineEntrySchema[];
    keyboardRows: TimelineEntrySchema[];
}

export interface AggregatedTimelineEntry {
    id: string;
    group: string;
    content: string;
    start: Date;
    end: Date;
    eventCount?: number;
}
