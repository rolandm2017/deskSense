export function formatDateForApi(date: Date): string {
    // Use methods that respect local time rather than UTC time
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

export function getIanaTimezone() {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return timeZone;
}

export function getTimezone(date: Date) {
    const timeZoneAbbr = date
        .toLocaleTimeString("en-us", { timeZoneName: "short" })
        .split(" ")
        .pop();
    return timeZoneAbbr;
}

// export function formatDateForApi(date: Date) {
//     return date.toISOString().split("T")[0]; // formats to YYYY-MM-DD
// }

/**
 * Checks if the given date is in the current week or later
 * @param viewedWeek The date to check
 * @returns boolean - true if the date is in the present week or later, false otherwise
 */
export function dateIsThePresentWeekOrLater(viewedWeek: Date): boolean {
    // Get the current date
    const today = new Date();

    // Set both dates to the beginning of their respective weeks (Sunday)
    const todayDay = today.getDay(); // 0 for Sunday, 1 for Monday, etc.
    const startOfCurrentWeek = new Date(today);
    startOfCurrentWeek.setDate(today.getDate() - todayDay);
    startOfCurrentWeek.setHours(0, 0, 0, 0); // Set to midnight

    const viewedWeekDay = viewedWeek.getDay();
    const startOfViewedWeek = new Date(viewedWeek);
    startOfViewedWeek.setDate(viewedWeek.getDate() - viewedWeekDay);
    startOfViewedWeek.setHours(0, 0, 0, 0); // Set to midnight

    // Compare the start of the viewed week with the start of the current week
    return startOfViewedWeek >= startOfCurrentWeek;
}

export function getPreviousSunday() {
    let today = new Date();
    let daysSinceSunday = today.getDay(); // Sunday is 0
    let previousSunday = new Date(today);
    previousSunday.setDate(today.getDate() - daysSinceSunday);
    return previousSunday; // TODO: Test this function
}

export function getUpcomingSaturday() {
    let today = new Date();
    let daysUntilSaturday = 6 - today.getDay(); // Saturday is 6
    let nextSaturday = new Date(today);
    nextSaturday.setDate(today.getDate() + daysUntilSaturday);
    return nextSaturday;
}

export function convertStringToDate(someSundayAsString: string) {
    return new Date(someSundayAsString);
}

export function getSaturdayThatEndsTheWeek(someSundayAsString: string | Date) {
    const someSunday =
        typeof someSundayAsString === "string"
            ? new Date(someSundayAsString)
            : someSundayAsString;
    let saturdayDate = new Date(someSunday);
    saturdayDate.setDate(someSunday.getDate() + 6);
    return saturdayDate;
}

export function getSundayOfNextWeek(startingSunday: Date) {
    let sundayOfNextWeek = new Date(startingSunday);
    sundayOfNextWeek.setDate(startingSunday.getDate() + 7);
    return sundayOfNextWeek;
}

export const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
    });
};

export const formatDateMmDdYyyy = (date: Date) => {
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();

    return `${month}-${day}-${year}`;
};

export const parseDateMmDdYyyy = (dateString: string) => {
    // Split date and time
    const [datePart, timePart] = dateString.split(", ");

    // Split date components
    const [month, day, year] = datePart.split("-").map(Number);

    // Split time components
    const [hours, minutes, seconds] = timePart.split(":").map(Number);

    // Create new Date object (month is 0-based, so subtract 1)
    return new Date(year, month - 1, day, hours, minutes, seconds);
};
