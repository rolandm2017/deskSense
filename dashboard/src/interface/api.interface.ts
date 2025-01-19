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
