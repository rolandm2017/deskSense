export interface DailyChromeSummaries {
    columns: DailyDomainSummary[];
}

export interface DailyDomainSummary {
    id: number;
    domainName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface WeeklyChromeUsage {
    days: DayOfChromeUsage[];
}

export interface DayOfChromeUsage {
    date: Date;
    content: { columns: DailyDomainSummary[] };
}
