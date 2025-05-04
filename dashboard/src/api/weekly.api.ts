import axios, { AxiosError } from "axios";

import {
    withDateConversion,
    withErrorHandling,
    withErrorHandlingAndArgument,
} from "./apiUtil";

import {
    DailyProgramSummaries,
    WeeklyProgramTimelines,
    WeeklyProgramUsage,
} from "../interface/programs.interface";

import {
    DailyChromeSummaries,
    DayOfChromeUsage,
    WeeklyChromeUsage,
} from "../interface/chrome.interface";

import {
    BreakdownByDay,
    WeeklyBreakdown,
} from "../interface/overview.interface";
import {
    PartiallyAggregatedWeeklyTimeline,
    TimelineRows,
    WeeklyTimeline,
} from "../interface/peripherals.interface";
import { ensureSunday } from "../util/apiUtil";
import { formatDateForApi } from "../util/timeTools";

const baseRoute = import.meta.env.VITE_API_URL + "/api";

const api = axios.create({
    baseURL: baseRoute,
    timeout: 5000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Add type-safe request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem("token");
        if (token) {
            if (config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

const getTodaysTimelineData = withErrorHandling<TimelineRows>(() =>
    api.get("/dashboard/timeline")
);

// TODO: Make home screen execute a "get week of" where incomplete weeks are OK.

const getProgramSummaries = withErrorHandling<DailyProgramSummaries>(() =>
    api.get("/dashboard/program/summaries")
);

const getChromeSummaries = withErrorHandling<DailyChromeSummaries>(() =>
    api.get("/dashboard/chrome/summaries")
);

// const getWeeklyTyping = withErrorHandling<WeeklyTyping>(() =>
//     api.get("/dashboard/typing/summaries/week")
// );

// const getWeeklyClicking = withErrorHandling<WeeklyClicking>(() =>
//     api.get("/dashboard/clicking/summaries/week")
// );

const getPresentWeekProgramUsage = withErrorHandling<WeeklyProgramUsage>(() =>
    api.get("/dashboard/program/summaries/week")
);

const getPresentWeekChromeUsage = withErrorHandling<WeeklyChromeUsage>(() =>
    api.get("/dashboard/chrome/summaries/week")
);

const getTimelineForPresentWeek =
    withErrorHandling<PartiallyAggregatedWeeklyTimeline>(() =>
        api.get("/dashboard/timeline/week")
    );

const getPresentWeekProgramTimeline = withErrorHandling<WeeklyProgramTimelines>(
    () => api.get("/dashboard/programs/usage/timeline")
);

/*
 *
 * Past week
 *
 */

const getWeeklyBreakdown = withErrorHandlingAndArgument<
    WeeklyBreakdown,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    // const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/breakdown/week/${formattedDate}`);
});

const getTimelineForPastWeek = withErrorHandlingAndArgument<
    WeeklyTimeline,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    // const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/timeline/week/${formattedDate}`);
});

const getChromeUsageForPastWeek = withErrorHandlingAndArgument<
    WeeklyChromeUsage,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    // const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/chrome/summaries/week/${formattedDate}`);
});

const getProgramTimelineForPastWeek = withErrorHandlingAndArgument<
    WeeklyProgramTimelines,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    // const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/programs/usage/timeline/${formattedDate}`);
});

// Typescript wizardry
//
//
//

// Example usage:
const getEnhancedChromeUsageForPastWeek = withDateConversion<
    DayOfChromeUsage,
    WeeklyChromeUsage,
    typeof getChromeUsageForPastWeek
>(getChromeUsageForPastWeek);

const getEnhancedWeeklyBreakdown = withDateConversion<
    BreakdownByDay,
    WeeklyBreakdown,
    typeof getWeeklyBreakdown
>(getWeeklyBreakdown);

export {
    getChromeSummaries,
    getEnhancedChromeUsageForPastWeek,
    getEnhancedWeeklyBreakdown,
    getPresentWeekChromeUsage,
    getPresentWeekProgramTimeline,
    // getWeeklyClicking,
    // getWeeklyTyping,
    getPresentWeekProgramUsage,
    getProgramSummaries,
    getProgramTimelineForPastWeek,
    getTimelineForPastWeek,
    getTimelineForPresentWeek,
    getTodaysTimelineData,
};
