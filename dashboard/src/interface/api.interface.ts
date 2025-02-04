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

/*
 *
 * Daily section
 * Daily section
 * Daily section
 * Daily section
 *
 */

// export interface DailyTypingSummary {
//     // what goes in here
// }

// export interface DailyClickingSummary {
//     // what to do ?
// }

export interface DailyProgramSummary {
    id: number;
    programName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface DailyProgramSummaries {
    columns: DailyProgramSummary[];
}

export interface DailyDomainSummary {
    id: number;
    domainName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface DailyChromeSummaries {
    columns: DailyDomainSummary[];
}

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
