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

export interface DaysOfAggregatedRows {
    date: Date;
    mouseRow: AggregatedTimelineEntry[];
    keyboardRow: AggregatedTimelineEntry[];
}

export interface WeeklyTimelineAggregate {
    // the same as the WeeklyTimeline, but it's been aggregated
    days: DaysOfAggregatedRows[];
}
