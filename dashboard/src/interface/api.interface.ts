export interface KeyboardLog {
    keyboardEventId: number;
    timestamp: string; // ISO 8601 datetime string  // FIXME: should be uh, uh, start_time, end_time
}

export interface KeyboardReport {
    count: number;
    keyboardLogs: KeyboardLog[];
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
