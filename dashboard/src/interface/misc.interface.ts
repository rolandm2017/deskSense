export interface BarChartColumn {
    programName: string;
    hoursSpent: number;
}

export interface AggregatedTimelineEntry {
    id: string;
    group: string;
    content: string;
    start: Date;
    end: Date;
    eventCount?: number;
}
