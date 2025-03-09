import axios, { AxiosError, AxiosResponse } from "axios";
import {
    TypingSessionsReport,
    MouseReport,
    ProgramActivityReport,
    DailyChromeSummaries,
    DailyProgramSummaries,
    TimelineRows,
} from "../interface/api.interface";
import {
    DayOfChromeUsage,
    WeeklyBreakdown,
    BreakdownByDay,
    WeeklyChromeUsage,
    WeeklyProgramUsage,
    WeeklyTimeline,
    PartiallyAggregatedWeeklyTimeline,
} from "../interface/weekly.interface";
import { formatDateForApi, getTimezone } from "../util/timeTools";
import { ensureSunday } from "../util/apiUtil";

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

const withErrorHandling = <T>(fn: () => Promise<AxiosResponse<T>>) => {
    return (): Promise<T> => {
        // console.log(
        // "Fetching:",
        // fn.toString().match(/api\.get\("([^"]+)"\)/)?.[1]
        // );
        return fn()
            .then((response) => {
                return response.data;
            })
            .catch((error) => {
                if (axios.isAxiosError(error)) {
                    console.error("Error:", error.response?.data);
                    throw new Error(`Failed to execute: ${error.message}`);
                }
                throw error;
            });
    };
};

const getKeyboardReport = withErrorHandling<TypingSessionsReport>(() =>
    api.get("/report/keyboard")
);

const getMouseReport = withErrorHandling<MouseReport>(() =>
    api.get("/report/mouse")
);

const getProgramReport = withErrorHandling<ProgramActivityReport>(() =>
    api.get("/report/program")
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

const withErrorHandlingAndArgument = <T, P extends any[]>(
    fn: (...args: P) => Promise<AxiosResponse<T>>
) => {
    return (...args: P): Promise<T> => {
        return fn(...args)
            .then((response) => {
                return response.data;
            })
            .catch((error) => {
                if (axios.isAxiosError(error)) {
                    console.error("Error:", error.response?.data);
                    throw new Error(`Failed to execute: ${error.message}`);
                }
                throw error;
            });
    };
};

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
    const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/breakdown/week/${formattedDate}`);
});

const getTimelineForPastWeek = withErrorHandlingAndArgument<
    WeeklyTimeline,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/timeline/week/${formattedDate}`);
});

const getChromeUsageForPastWeek = withErrorHandlingAndArgument<
    WeeklyChromeUsage,
    [Date]
>((date: Date) => {
    ensureSunday(date);
    const formattedDate = formatDateForApi(date);
    const timezone = getTimezone(date);
    // TODO: send timezone
    return api.get(`/dashboard/chrome/summaries/week/${formattedDate}`);
});

// Typescript wizardry
//
//
//

// Base interface for objects that have a date field that needs conversion
interface DateConvertible {
    date?: string | Date; // Optional because some types might use 'day' instead
    day?: string | Date; // Some of your interfaces use 'day' instead of 'date'
}

// Base interface for weekly data structures
interface WeeklyDataStructure<T extends DateConvertible> {
    days: T[];
}

// Generic conversion function that works with your existing types
const withDateConversion = <
    // DayType is the type of a single day's data (like DayOfChromeUsage or BreakdownByDay)
    // It must have either a 'date' or 'day' property
    DayType extends DateConvertible,
    // WeekType is the type of the whole week's data (like WeeklyChromeUsage or WeeklyBreakdown)
    // It must have a 'days' array containing DayType objects
    WeekType extends WeeklyDataStructure<DayType>,
    // FuncType is the type of function being wrapped (like getChromeUsageForPastWeek)
    // It must take a Date and return a Promise of WeekType
    FuncType extends (date: Date) => Promise<WeekType>
>(
    originalFunction: FuncType
) => {
    return async (date: Date): Promise<WeekType> => {
        const response = await originalFunction(date);

        const withConvertedDateObjs = response.days.map((day) => ({
            ...day,
            // Convert either 'date' or 'day' property to Date object
            ...(day.date !== undefined ? { date: new Date(day.date) } : {}),
            ...(day.day !== undefined ? { day: new Date(day.day) } : {}),
        }));

        return {
            ...response,
            days: withConvertedDateObjs,
        } as WeekType;
    };
};

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
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
    getTodaysTimelineData,
    getProgramSummaries,
    getChromeSummaries,
    getTimelineForPresentWeek,
    // getWeeklyClicking,
    // getWeeklyTyping,
    getPresentWeekProgramUsage,
    getPresentWeekChromeUsage,
    getTimelineForPastWeek,
    getEnhancedChromeUsageForPastWeek,
    getEnhancedWeeklyBreakdown,
};
