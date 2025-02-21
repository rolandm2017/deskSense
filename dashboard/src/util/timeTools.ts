export function formatDateForApi(date: Date) {
    return date.toISOString().split("T")[0]; // formats to YYYY-MM-DD
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
