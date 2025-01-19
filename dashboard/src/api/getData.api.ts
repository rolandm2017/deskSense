import axios, { AxiosError, AxiosResponse } from "axios";
import {
    TypingSessionsReport,
    MouseReport,
    ProgramActivityReport,
} from "../interface/api.interface";

const baseRoute = import.meta.env.VITE_API_URL + "/api/report";

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

// const withErrorHandlingAsync = <T>(fn: () => Promise<AxiosResponse<T>>) => {
//     return async (): Promise<T> => {
//         try {
//             const response = await fn();
//             return response.data;
//         } catch (error) {
//             if (axios.isAxiosError(error)) {
//                 console.error("Error:", error.response?.data);
//                 throw new Error(`Failed to execute: ${error.message}`);
//             }
//             throw error;
//         }
//     };
// };

// const getKeyboardReportAsync = withErrorHandlingAsync<KeyboardReport>(
//     async () => api.get("/keyboard")
// );

// const getMouseReportAsync = withErrorHandlingAsync<MouseReport>(async () =>
//     api.get("/mouse")
// );

// const getProgramReportAsync = withErrorHandlingAsync<ProgramActivityReport>(
//     async () => api.get("/program")
// );

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
    api.get("/keyboard")
);

const getMouseReport = withErrorHandling<MouseReport>(() => api.get("/mouse"));

const getProgramReport = withErrorHandling<ProgramActivityReport>(() =>
    api.get("/program")
);

export { getKeyboardReport, getMouseReport, getProgramReport };
