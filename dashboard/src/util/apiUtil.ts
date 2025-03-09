/**
 * Checks if the provided date is a Sunday and throws an error if it's not.
 * @param date - The date to check. Accepts Date object, ISO string, or timestamp
 * @throws Error if the provided date is not a Sunday
 * @returns The original date if it is a Sunday
 */
export function ensureSunday(date: Date): Date {
    // Check if the date is valid
    if (isNaN(date.getTime())) {
        throw new Error("Invalid date provided");
    }

    // Check if the date is a Sunday (0 = Sunday in JavaScript Date)
    if (date.getDay() !== 0) {
        throw new Error(
            `The date ${date.toISOString().split("T")[0]} is not a Sunday`
        );
    }

    return date;
}
