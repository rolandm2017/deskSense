import { Selection, ScaleTime } from "d3";
import { ScaleBand } from "d3";
import { AggregatedTimelineEntry } from "../interface/misc.interface";
import { TimelineEvent } from "../interface/weekly.interface";

import { getColorFromAppName } from "./coloringLines";

export function addEventLinesForPeripherals(
    yPosition: number,
    entry: AggregatedTimelineEntry,
    eventLines: Selection<SVGGElement, unknown, null, undefined>,
    x: ScaleTime<number, number, never>,
    y: ScaleBand<string>
) {
    // Convert the entry times to our reference date (Jan 1, 2024)
    const startTime = normalizeToReferenceDate(entry.start);
    const endTime = normalizeToReferenceDate(entry.end);

    const startX = x(startTime);
    const endX = x(endTime);

    // Add the line for the event
    eventLines
        .append("line")
        .attr("x1", startX)
        .attr("x2", endX)
        .attr("y1", yPosition)
        .attr("y2", yPosition)
        .attr("stroke", entry.group === "mouse" ? "steelblue" : "#e41a1c")
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 0.7);

    // Add small circles at start and end points
    eventLines
        .append("circle")
        .attr("cx", startX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", entry.group === "mouse" ? "steelblue" : "#e41a1c");

    eventLines
        .append("circle")
        .attr("cx", endX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", entry.group === "mouse" ? "steelblue" : "#e41a1c");
}

const programColors = [
    { colorName: "Soft Teal", hexCode: "#5ABFB9" },
    { colorName: "Muted Coral", hexCode: "#F2A88D" },
    { colorName: "Lavender", hexCode: "#AEA1EA" },
    { colorName: "Sage Green", hexCode: "#A0C1A0" },
];

export function addEventLinesForPrograms(
    yPosition: number,
    programName: string,
    entry: TimelineEvent,
    eventLines: Selection<SVGGElement, unknown, null, undefined>,
    x: ScaleTime<number, number, never>,
    y: ScaleBand<string>
) {
    // Convert the entry times to our reference date (Jan 1, 2024)
    const startTime = normalizeToReferenceDate(entry.startTime);
    const endTime = normalizeToReferenceDate(entry.endTime);

    const startX = x(startTime);
    const endX = x(endTime);

    const colorForApp = getColorFromAppName(programName);

    // Add the line for the event
    eventLines
        .append("line")
        .attr("x1", startX)
        .attr("x2", endX)
        .attr("y1", yPosition)
        .attr("y2", yPosition)
        .attr("stroke", colorForApp)
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 0.7);

    // Add small circles at start and end points
    eventLines
        .append("circle")
        .attr("cx", startX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", colorForApp);

    eventLines
        .append("circle")
        .attr("cx", endX)
        .attr("cy", yPosition)
        .attr("r", 2)
        .attr("fill", colorForApp);
}

// Helper function to normalize any date to our reference date (Jan 1, 2024)
function normalizeToReferenceDate(
    date: Date | string | { toString: () => string }
): Date {
    // Ensure we're working with a proper Date object
    const dateObj = date instanceof Date ? date : new Date(date.toString());

    // Create a new date on our reference day (Jan 1, 2024)
    return new Date(
        2024, // year
        0, // month (0 = January)
        1, // day
        dateObj.getHours(),
        dateObj.getMinutes(),
        dateObj.getSeconds(),
        dateObj.getMilliseconds()
    );
}

// Helper function to map Date to x position (-3 to 3)
function dateToX(date: Date | string | { toString: () => string }): number {
    // Ensure we're working with a proper Date object
    const dateObj = date instanceof Date ? date : new Date(date.toString());
    const midnight = new Date(dateObj);
    midnight.setHours(0, 0, 0, 0);
    const endOfDay = new Date(dateObj);
    endOfDay.setHours(23, 59, 59, 999);

    // Calculate position between -3 and 3 based on time of day
    // console.log(
    //     endOfDay,
    //     Object.prototype.toString.call(endOfDay) === "[object Date]",
    //     "46ru"
    // );

    const totalMs = endOfDay.getTime() - midnight.getTime();
    const currentMs = dateObj.getTime() - midnight.getTime();
    return -3 + (currentMs / totalMs) * 6;
}
