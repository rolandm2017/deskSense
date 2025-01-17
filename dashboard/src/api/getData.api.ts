import axios, { AxiosError, AxiosResponse } from "axios";

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

export interface KeyboardLog {
    keyboard_event_id: number;
    timestamp: string; // ISO 8601 datetime string
}

export interface KeyboardReport {
    count: number;
    keyboard_logs: KeyboardLog[];
}

export interface MouseLog {
    mouse_event_id: number;
    start_time: string; // ISO 8601 datetime string
    end_time: string; // ISO 8601 datetime string
}

export interface MouseReport {
    count: number;
    mouse_reports: MouseLog[];
}

export interface ProgramActivityLog {
    program_event_id: number;
    window: string;
    start_time: string; // ISO 8601 datetime string
    end_time: string; // ISO 8601 datetime string
    productive: boolean;
}

export interface ProgramActivityReport {
    count: number;
    program_reports: ProgramActivityLog[]; //
}

const withErrorHandlingAsync = <T>(fn: () => Promise<AxiosResponse<T>>) => {
    return async (): Promise<T> => {
        try {
            const response = await fn();
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                console.error("Error:", error.response?.data);
                throw new Error(`Failed to execute: ${error.message}`);
            }
            throw error;
        }
    };
};

const getKeyboardReportAsync = withErrorHandlingAsync<KeyboardReport>(
    async () => api.get("/keyboard")
);

const getMouseReportAsync = withErrorHandlingAsync<MouseReport>(async () =>
    api.get("/mouse")
);

const getProgramReportAsync = withErrorHandlingAsync<ProgramActivityReport>(
    async () => api.get("/program")
);

const withErrorHandling = <T>(fn: () => Promise<AxiosResponse<T>>) => {
    return (): Promise<T> => {
        console.log(
            "Fetching:",
            fn.toString().match(/api\.get\("([^"]+)"\)/)?.[1]
        );
        // console.log('Fetching:', fn.toString().match(/api\.get\("([^"]+)"\)/)?.[1]);
        return fn()
            .then((response) => {
                console.log(response.data, "100ru");
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

const getKeyboardReport = withErrorHandling<KeyboardReport>(() =>
    api.get("/keyboard")
);

const getMouseReport = withErrorHandling<MouseReport>(() => api.get("/mouse"));

const getProgramReport = withErrorHandling<ProgramActivityReport>(() =>
    api.get("/program")
);

// // GET request with error handling
// async function getKeyboardReport(): Promise<KeyboardReport> {
//     const response: AxiosResponse<KeyboardReport> = await api.get("/keyboard");
//     return response.data;
// }

// async function getMouseReport(): Promise<MouseReport> {
//     const response: AxiosResponse<MouseReport> = await api.get("/mouse");
//     return response.data;
// }

// async function getProgramReport(): Promise<ProgramActivityReport> {
//     const response: AxiosResponse<ProgramActivityReport> = await api.get("/program");
//     return response.data;
// }

export { getKeyboardReport, getMouseReport, getProgramReport };
