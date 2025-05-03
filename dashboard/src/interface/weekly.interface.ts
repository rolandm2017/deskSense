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
