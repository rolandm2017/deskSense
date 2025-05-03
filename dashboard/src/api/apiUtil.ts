import axios, { AxiosResponse } from "axios";

export const withErrorHandlingAndArgument = <T, P extends any[]>(
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

export const withErrorHandling = <T>(fn: () => Promise<AxiosResponse<T>>) => {
    return (): Promise<T> => {
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
export const withDateConversion = <
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
