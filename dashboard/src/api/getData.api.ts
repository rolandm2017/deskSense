import axios, { AxiosError, AxiosResponse } from "axios";
import {
    TypingSessionsReport,
    MouseReport,
    ProgramActivityReport,
} from "../interface/api.interface";

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

const keyboardEventsRoute = baseRoute + "/keyboard";
const mouseEventsRoute = baseRoute + "/mouse";
const programsRoute = baseRoute + "/program";
const chromeRoute = baseRoute + "/chrome";

const withErrorHandling = <T>(fn: () => Promise<AxiosResponse<T>>) => {
    return (): Promise<T> => {
        console.log(
            "Fetching:",
            fn.toString().match(/api\.get\("([^"]+)"\)/)?.[1]
        );
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

export interface DailyProgramSummary {
    id: number;
    programName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface DailyProgramSummaries {
    columns: DailyProgramSummary[];
}

export interface DailyChromeSummary {
    id: number;
    domainName: string;
    hoursSpent: number;
    gatheringDate: Date;
}

export interface DailyChromeSummaries {
    columns: DailyChromeSummary[];
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

const getTimelineData = withErrorHandling<TimelineRows>(() =>
    api.get("/dashboard/timeline")
);

const getProgramSummaries = withErrorHandling<DailyProgramSummaries>(() =>
    api.get("/dashboard/program/summaries")
);

const getChromeSummaries = withErrorHandling<DailyChromeSummaries>(() =>
    api.get("/dashboard/chrome/summaries")
);

export {
    getKeyboardReport,
    getMouseReport,
    getProgramReport,
    getTimelineData,
    getProgramSummaries,
    getChromeSummaries,
};
