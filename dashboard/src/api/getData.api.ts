import axios, { AxiosError } from "axios";

import { withErrorHandling } from "./apiUtil";

import { DailyProgramSummaries } from "../interface/programs.interface";

import { DailyChromeSummaries } from "../interface/chrome.interface";

import { TimelineRows } from "../interface/peripherals.interface";

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

// Typescript wizardry
//
//
//

export {
    getChromeSummaries,
    // getWeeklyClicking,
    // getWeeklyTyping,
    getProgramSummaries,
    getTodaysTimelineData,
};
