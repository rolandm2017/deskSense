// **
// ****
// Program Usage Timeline
// *

export interface WeeklyProgramUsage {
    days: DayOfProgramUsage[];
}

export interface WeeklyProgramTimelines {
    days: ProgamUsageTimeline[];
}

export interface ProgamUsageTimeline {
    date: Date | string;
    programs: ProgramTimelineContent[];
    // events: TimelineEvent[];
}

export interface ProgramTimelineContent {
    programName: string;
    events: ProgramTimelineEvent[];
}

export interface ProgramTimelineEvent {
    logId: number;

    startTime: Date;
    endTime: Date;
}

export interface DailyProgramSummary {
    id: number;
    programName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface DailyProgramSummaries {
    columns: DailyProgramSummary[];
}

export interface DayOfProgramUsage {
    date: Date;
    usage: DailyProgramSummary;
}

export interface ProgramActivityLog {
    programEventId: number;
    window: string;
    startTime: string; // ISO 8601 datetime string
    endTime: string; // ISO 8601 datetime string
    productive: boolean;
}

export interface ProgramActivityReport {
    count: number;
    programLogs: ProgramActivityLog[]; //
}
