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
    WeeklyChromeUsage,
    WeeklyProgramUsage,
    WeeklyTimeline,
} from "../interface/weekly.interface";

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

const getTimelineData = withErrorHandling<TimelineRows>(() =>
    api.get("/dashboard/timeline")
);

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

const getWeeklyProgramUsage = withErrorHandling<WeeklyProgramUsage>(() =>
    api.get("/dashboard/program/summaries/week")
);

const getWeeklyChromeUsage = withErrorHandling<WeeklyChromeUsage>(() =>
    api.get("/dashboard/chrome/summaries/week")
);

const getTimelineWeekly = withErrorHandling<WeeklyTimeline>(() =>
    api.get("/dashboard/timeline/week")
);

export {
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
    getTimelineData,
    getProgramSummaries,
    getChromeSummaries,
    // getWeeklyClicking,
    // getWeeklyTyping,
    getWeeklyChromeUsage,
    getWeeklyProgramUsage,
    getTimelineWeekly,
};
